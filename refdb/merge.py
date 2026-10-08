"""Merge per-source records into one product table.

Records are linked into one product when they share a valid ISBN, or share a product code and
have close titles, or have the same normalised title and year with no conflicting publisher.
Each product field takes the first value found in source-priority order, and remembers which
source and record it came from (provenance), so nothing is ever silently overwritten.

`public=True` merges only sources whose `publish` flag is set: that is the release."""
import json
import re
import sqlite3
from difflib import SequenceMatcher

from .names import split_companies, write_tables
from .sources import SOURCES

# Most specific / most carefully edited first.
PRIORITY = ["sarna", "whitewolf", "forgottenrealms", "wookieepedia", "memorybeta", "traveller", "wikipedia",
            "waynesbooks", "tsrarchive", "isfdb", "legrog", "openlibrary", "rpgnet", "wikidata"]
# Open Library often records the US distributor of early TSR books ("Distributed by Random House").
NOT_PUBLISHER = re.compile(r"\s*(distributed\b|distrib\.|\[?s\.\s?n\.\]?$)", re.I)
FIELDS = ("title", "publisher", "author", "year", "code", "isbn", "edition", "pages", "product_type")

SCHEMA = """
DROP TABLE IF EXISTS {p}products; DROP TABLE IF EXISTS {p}product_records;
CREATE TABLE {p}products (id INTEGER PRIMARY KEY, title TEXT, publisher TEXT, author TEXT, year TEXT,
  code TEXT, isbn13 TEXT, edition TEXT, pages TEXT, product_type TEXT,
  isbns TEXT, codes TEXT, sources TEXT, provenance TEXT, publisher_variants TEXT, work_id INTEGER);
CREATE TABLE {p}product_records (product_id INTEGER, source TEXT, key TEXT, url TEXT);
"""


# ---------------------------------------------------------------- normalisation
def isbn13s(text: str | None) -> list[str]:
    """Every checksum-valid ISBN in a free-text field, as ISBN-13."""
    out = []
    text = re.sub(r"(?<=\d)-(?=[\dXx])", "", text or "")     # '9-781560-765899' -> '9781560765899'
    for raw in re.findall(r"(?:97[89][\s-]?)?(?:\d[\s-]?){9}[\dXx]", text):
        d = re.sub(r"[^0-9Xx]", "", raw).upper()
        if len(d) == 10 and re.fullmatch(r"\d{9}[\dX]", d):
            if sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(d)) % 11 == 0:
                core = "978" + d[:9]
                d = core + str((10 - sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(core)) % 10) % 10)
            else:
                continue
        if len(d) == 13 and d.isdigit() and d[:3] in ("978", "979"):
            if (10 - sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(d[:12])) % 10) % 10 == int(d[12]):
                out.append(d)
    return list(dict.fromkeys(out))


def norm_title(t: str | None) -> str:
    t = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", (t or "").lower())
    t = re.sub(r"^(the|a|an)\s+", "", re.sub(r"[^a-z0-9]+", " ", t).strip())
    return t


def norm_code(c: str | None) -> list[str]:
    """'TSR 9039' -> ['9039','TSR9039']; '8415 (original) 967100000 (reissue)' -> both numbers."""
    out = []
    for part in re.split(r"[;,/]|\s{2,}|\(.*?\)", c or ""):
        p = re.sub(r"[^A-Z0-9]", "", part.upper())
        if len(p) >= 3 and re.search(r"\d", p):
            out += [p, re.sub(r"^[A-Z]+", "", p)]
    return [x for x in dict.fromkeys(out) if len(x) >= 3]


def _close(a: str, b: str) -> bool:
    return bool(a and b) and (a == b or SequenceMatcher(None, a, b).ratio() >= 0.9)


def _pub_ok(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return True
    na, nb = norm_title(a).split(), norm_title(b).split()
    if set(na[:2]) & set(nb[:2]):               # 'TSR, Inc.' ~ 'TSR'; 'Wizards of the Coast' ~ 'Wizards'
        return True
    sa, sb = "".join(na), "".join(nb)            # 'T.S.R.' ~ 'TSR, Inc.' ('tsr' vs 'tsrinc')
    return len(min(sa, sb, key=len)) >= 3 and (sa.startswith(sb) or sb.startswith(sa))


# ---------------------------------------------------------------- clustering
class _UF:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        self.p[self.find(a)] = self.find(b)


def merge(db: sqlite3.Connection, public: bool = False) -> int:
    sources = [s for s in PRIORITY if s in SOURCES and (SOURCES[s].publish or not public)]
    rank = {s: i for i, s in enumerate(sources)}
    rows = db.execute(f"SELECT source, key, url, {', '.join(FIELDS)} FROM records WHERE source IN "
                      f"({','.join('?' * len(sources))})", sources).fetchall()
    recs = [dict(zip(("source", "key", "url") + FIELDS, r)) for r in rows]
    write_tables(db, [k for k, s in SOURCES.items() if s.publish or not public])   # standard names
    std = dict(db.execute("SELECT variant, name FROM company_names"))

    def standard(field: str | None) -> str | None:
        return "; ".join(dict.fromkeys(std.get(c, c) for c in split_companies(field))) or None

    for r in recs:
        r["_pub"] = standard(r["publisher"])
        r["_isbns"] = isbn13s(r["isbn"])
        r["_title"] = norm_title(r["title"])
        r["_codes"] = norm_code(r["code"])
        r["_year"] = (re.search(r"(1[89]|20)\d\d", r["year"] or "") or [None])[0]
    from collections import Counter
    code_use = Counter(c for r in recs for c in r["_codes"])
    for r in recs:     # a code shared by dozens of records ('100', '1') identifies nothing, and comparing
        r["_codes"] = [c for c in r["_codes"] if code_use[c] <= 50]     # all their titles is quadratic
    uf = _UF(len(recs))
    by_isbn: dict[str, int] = {}
    by_code: dict[str, list[int]] = {}
    by_title_year: dict[tuple, list[int]] = {}
    for i, r in enumerate(recs):
        for isbn in r["_isbns"]:                                    # 1. same ISBN
            if isbn in by_isbn:
                uf.union(i, by_isbn[isbn])
            else:
                by_isbn[isbn] = i
        for c in r["_codes"]:                                       # 2. same code + close title
            for j in by_code.get(c, []):
                if _close(r["_title"], recs[j]["_title"]):
                    uf.union(i, j)
            by_code.setdefault(c, []).append(i)
        if r["_title"] and r["_year"]:                              # 3. same title + year, publisher ok
            k = (r["_title"], r["_year"])
            for j in by_title_year.get(k, []):
                if _pub_ok(r["_pub"], recs[j]["_pub"]):
                    uf.union(i, j)
            by_title_year.setdefault(k, []).append(i)

    clusters: dict[int, list[dict]] = {}
    for i, r in enumerate(recs):
        clusters.setdefault(uf.find(i), []).append(r)

    p = "public_" if public else ""
    db.executescript(SCHEMA.format(p=p))
    pid = 0
    works = _UF(len(clusters) + 1)
    by_work: dict[tuple, list[int]] = {}
    for members in clusters.values():
        members.sort(key=lambda r: rank[r["source"]])
        pid += 1
        chosen, prov = {}, {}
        for f in FIELDS:
            for r in members:
                if r[f] and not (f == "publisher" and NOT_PUBLISHER.match(r[f])):
                    chosen[f], prov[f] = (r["_pub"] if f == "publisher" else r[f]), f"{r['source']}:{r['key']}"
                    break
        variants = list(dict.fromkeys(c for r in members for c in split_companies(r["publisher"])
                                      if not NOT_PUBLISHER.match(c)))
        title = norm_title(chosen.get("title"))
        year = (re.search(r"(1[89]|20)\d\d", chosen.get("year") or "") or [None])[0]
        surnames = {w for r in members for w in re.findall(r"[a-z]{4,}", (r["author"] or "").lower())}
        if title:                                   # editions of one work: same title + an author in
            for w in surnames:                      # common, or same publisher and year
                for q in by_work.setdefault((title, "a", w), []):
                    works.union(pid, q)
                by_work[(title, "a", w)].append(pid)
            if chosen.get("publisher") and year:
                k = (title, "p", chosen["publisher"].lower(), year)
                for q in by_work.setdefault(k, []):
                    works.union(pid, q)
                by_work[k].append(pid)
        isbns = list(dict.fromkeys(x for r in members for x in r["_isbns"]))
        codes = list(dict.fromkeys(r["code"] for r in members if r["code"]))
        db.execute(f"INSERT INTO {p}products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            pid, chosen.get("title"), chosen.get("publisher"), chosen.get("author"),
            (re.search(r"(1[89]|20)\d\d", chosen.get("year") or "") or [chosen.get("year")])[0],
            chosen.get("code"), isbns[0] if isbns else None, chosen.get("edition"), chosen.get("pages"),
            chosen.get("product_type"), "; ".join(isbns) or None, "; ".join(codes) or None,
            "; ".join(dict.fromkeys(r["source"] for r in members)), json.dumps(prov),
            "; ".join(variants) or None, None))
        db.executemany(f"INSERT INTO {p}product_records VALUES (?,?,?,?)",
                       [(pid, r["source"], r["key"], r["url"]) for r in members])
    db.executemany(f"UPDATE {p}products SET work_id = ? WHERE id = ?",
                   [(works.find(i), i) for i in range(1, pid + 1)])
    db.commit()
    return pid
