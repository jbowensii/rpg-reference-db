"""Name variants: one standard name per company and per game system, every spelling kept.

'TSR', 'TSR, Inc.', 'T.S.R.' and 'TSR Inc' all reduce to the key 'tsr'. The standard name of a group
is its most common spelling (ties: the shortest); `OVERRIDES` pins a different one where needed.
All-capital abbreviations in brackets ('West End Games (WEG)') become variants of the same company.
Several publishers in one field ('TSR; Wizards of the Coast') are split into separate companies.
For game systems brackets carry meaning ('Star Wars (D6 System)' is not 'Star Wars (Genesys)'), so
only a bracketed article is ignored there."""
import re
import sqlite3
from collections import Counter, defaultdict

_LEGAL = re.compile(r"\b(inc|incorporated|ltd|limited|llc|l\s?l\s?c|corp|corporation|co|company|gmbh|plc|"
                    r"s\s?a\s?r\s?l|s\s?l|s\s?a|s\s?r\s?l|pty|bv|ab|kg)\b")
_ACRONYM = re.compile(r"\(([A-Z][A-Z0-9&.]{1,9})\)")
_ARTICLE = re.compile(r"\((the|a|an|le|la|les|l'|der|die|das|el|il)\)", re.I)

# Known renames / brand names that belong to one company: key -> key of the company it belongs to.
ALIASES: dict[str, str] = {
    "tsrhobbies": "tsr",          # TSR Hobbies, Inc. became TSR, Inc. in 1983
}
# Standard names chosen by hand where the most common spelling is not the right one: key -> name.
OVERRIDES: dict[str, str] = {}


def key(name: str | None, keep_brackets: bool = False) -> str:
    """Matching key: lower case, '&' -> 'and', no punctuation, no legal endings, no leading article."""
    n = _ARTICLE.sub(" ", name or "").lower().replace("&", " and ")
    if not keep_brackets:                                     # 'Black Library / BL Publishing (UK)':
        n = n.split(" / ")[0]                                 # the imprint after ' / ' is not the name
        n = re.sub(r"\(([^)]*)\)", " ", n)
    n = re.sub(r"\b([a-z])\.(?=[a-z]\.)", r"\1", n)           # 't.s.r.' -> 'tsr.'
    n = re.sub(r"[^a-z0-9]+", " ", n)
    if not keep_brackets:
        n = _LEGAL.sub(" ", n)
    n = re.sub(r"^\s*(the|les|le|la)\s+", "", n)
    return re.sub(r"\s+", "", n)


def split_companies(field: str | None) -> list[str]:
    return [p.strip(" :,") for p in (field or "").split(";") if p.strip(" :,")]


def build(names: Counter, systems: bool = False) -> dict[str, tuple[str, int]]:
    """{written form: (standard name, group id)} for every written form in `names` (form -> count)."""
    parent: dict[str, str] = {}

    def find(k: str) -> str:
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def kf(form: str) -> str:
        k = key(form, keep_brackets=systems)
        return k if systems else ALIASES.get(k, k)

    for form in names:
        k = kf(form)
        if not k:
            continue
        find(k)
        if not systems:
            for a in _ACRONYM.findall(form):                   # 'West End Games (WEG)' joins 'WEG'
                ak = key(a)
                if len(ak) >= 3 and ak != k:
                    parent[find(ak)] = find(k)
    if not systems:                  # 'White Wolf Publishing' joins 'White Wolf' when both are used
        for k in list(parent):
            m = re.fullmatch(r"(.{5,}?)(publishing|publications|games|press|books)", k)
            if m and m.group(1) in parent:
                parent[find(k)] = find(m.group(1))
    groups: dict[str, Counter] = defaultdict(Counter)
    for form, n in names.items():
        if kf(form):
            groups[find(kf(form))][form.strip()] += n
    out = {}
    for gid, (root, forms) in enumerate(sorted(groups.items()), 1):
        clean = [f for f in forms if not re.search(r" / |[()\[\];]", f)] or list(forms)
        best = OVERRIDES.get(root) or min(clean, key=lambda f: (-forms[f], len(f), f))
        for form in forms:
            out[form] = (best, gid)
    return out


def write_tables(db: sqlite3.Connection, sources: list[str]) -> tuple[int, int]:
    """(Re)build `company_names` and `system_names` from the records and systems of `sources`."""
    marks = ",".join("?" * len(sources))
    pubs = Counter()
    for table in ("records", "systems"):
        for field, n in db.execute(f"SELECT publisher, count(*) FROM {table} WHERE source IN ({marks}) "
                                   f"AND publisher IS NOT NULL AND publisher != '' GROUP BY 1", sources):
            for part in split_companies(field):
                pubs[part] += n
    systems = Counter()
    for name, n in db.execute(f"SELECT name, count(*) FROM systems WHERE source IN ({marks}) "
                              f"AND name IS NOT NULL AND name != '' GROUP BY 1", sources):
        for part in name.split(" / "):                         # Le GRoG: 'Français / English'
            systems[part.strip()] += n
    db.executescript("""
      DROP TABLE IF EXISTS company_names; DROP TABLE IF EXISTS system_names;
      CREATE TABLE company_names (variant TEXT PRIMARY KEY, name TEXT, group_id INTEGER, uses INTEGER);
      CREATE TABLE system_names (variant TEXT PRIMARY KEY, name TEXT, group_id INTEGER, uses INTEGER);
    """)
    comp = build(pubs)
    db.executemany("INSERT OR REPLACE INTO company_names VALUES (?,?,?,?)",
                   [(f, c, g, pubs[f]) for f, (c, g) in comp.items()])
    syst = build(systems, systems=True)
    db.executemany("INSERT OR REPLACE INTO system_names VALUES (?,?,?,?)",
                   [(f, c, g, systems[f]) for f, (c, g) in syst.items()])
    db.commit()
    return len({g for _, g in comp.values()}), len({g for _, g in syst.values()})


def standard_publisher(db: sqlite3.Connection, field: str | None) -> str | None:
    """'TSR, Inc.; Wizards of the Coast LLC' -> 'TSR; Wizards of the Coast' (standard names, in order)."""
    out = []
    for part in split_companies(field):
        row = db.execute("SELECT name FROM company_names WHERE variant = ?", (part,)).fetchone()
        out.append(row[0] if row else part)
    return "; ".join(dict.fromkeys(out)) or None
