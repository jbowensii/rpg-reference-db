"""Sources that offer their whole dataset as one file or one query API (no page crawling):
John H. Kim's RPG Encyclopedia (XML), ttrpgwiki (JSON), the Traveller Wiki (Cargo query API)."""
import datetime as dt
import html
import json
import re
import time
import xml.etree.ElementTree as ET

import httpx

from .mediawiki import UA
from .store import save, save_raw, save_source, save_system


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _get(url: str, **params) -> httpx.Response:
    for attempt in range(4):                # a busy or briefly unreachable server: wait and retry
        try:
            r = httpx.get(url, params=params or None, headers={"User-Agent": UA}, timeout=120,
                          follow_redirects=True)
            if r.status_code not in (429, 500, 502, 503, 504):
                r.raise_for_status()
                return r
        except httpx.TransportError:
            if attempt == 3:
                raise
        time.sleep(15 * (attempt + 1))
    r.raise_for_status()
    return r


def _text(el, tag: str) -> str | None:
    found = el.find(tag)
    return " ".join(found.text.split()) if found is not None and found.text else None


def collect_kim(db, source) -> int:
    """One systems row per <Edition> of each <Game> in fulllist.xml."""
    save_source(db, source)
    body = _get(source.api).text
    save_raw(db, source.id, "fulllist.xml", source.api, "", _now(), body)
    rows = 0
    # The file uses HTML entity names (&oslash; ...) that only its DTD defines; resolve them first.
    xml_safe = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)(\w+);",
                      lambda m: html.unescape(m.group(0)) if html.unescape(m.group(0)) != m.group(0) else m.group(0),
                      body)
    for game in ET.fromstring(xml_safe.encode("utf-8")).iter("Game"):
        gid = game.get("game_id")
        for n, ed in enumerate(game.findall("Edition"), 1):
            authors = [a.text.strip() for a in ed.findall("Author") if a.text]
            company = ed.find("Company")
            save_system(db, source.id, f"{gid}#{n}", f"{source.url}#{gid}", {
                "name": _text(game, "Title"), "edition": _text(ed, "EdName"),
                "publisher": " ".join(company.text.split()) if company is not None and company.text else None,
                "year": _text(ed, "Year"), "author": "; ".join(authors) or None,
                "fields": {"type": game.get("type"), "language": game.get("language"),
                           "pages": _text(ed, "Pages"), "company_id": company.get("company_id") if company is not None else None,
                           "description": _text(game, "Description")}})
            rows += 1
    db.commit()
    return rows


def collect_ttrpgwiki(db, source) -> int:
    save_source(db, source)
    body = _get(source.api).text
    save_raw(db, source.id, "systems.json", source.api, "", _now(), body)
    rows = 0
    for item in json.loads(body):
        key = f"{item.get('name')}|{item.get('edition') or ''}"
        save_system(db, source.id, key, source.url, {
            "name": item.get("name"), "edition": item.get("edition"), "publisher": item.get("publisher"),
            "year": str(item["year"]) if item.get("year") else None, "family": item.get("family"),
            "fields": item})
        rows += 1
    db.commit()
    return rows


def collect_traveller(db, source) -> int:
    """Every row of the wiki's Cargo table RPGBook, 500 per request, one request per second."""
    save_source(db, source)
    fields = "_pageName=page,name,author,publisher,year,edition,format,pages,isbn,language,image,canon,version"
    rows, offset, seen = 0, 0, {}
    while True:
        d = _get(source.api, action="cargoquery", tables="RPGBook", fields=fields, limit=500,
                 offset=offset, format="json").json()
        batch = [{k: html.unescape(v) if isinstance(v, str) else v for k, v in r["title"].items()}
                 for r in d.get("cargoquery", [])]
        for r in batch:
            page = r.get("page") or r.get("name")
            seen[page] = seen.get(page, 0) + 1          # several editions can share one page
            url = source.url + "wiki/" + page.replace(" ", "_")
            save(db, source.id, f"{page}|{seen[page]}", url, "", _now(), json.dumps(r, ensure_ascii=False), {
                "title": r.get("name") or page, "publisher": r.get("publisher"), "author": r.get("author"),
                "year": (r.get("year") or "")[:4] or None, "edition": r.get("edition"), "pages": r.get("pages"),
                "isbn": r.get("isbn"), "product_type": r.get("format"), "cover": r.get("image"), "fields": r})
            rows += 1
        db.commit()
        if len(batch) < 500:
            return rows
        offset += 500
        time.sleep(1)


WIKIDATA_QUERY = """
SELECT ?i ?iLabel (SAMPLE(?cL) AS ?type) (SAMPLE(?pubL) AS ?publisher) (MIN(?date) AS ?published)
       (GROUP_CONCAT(DISTINCT ?isbn; separator="; ") AS ?isbns)
       (GROUP_CONCAT(DISTINCT ?authL; separator="; ") AS ?authors)
       (SAMPLE(?serL) AS ?series) (SAMPLE(?grog) AS ?grog_id) (SAMPLE(?ol) AS ?openlibrary_id) (SAMPLE(?wp) AS ?enwiki)
WHERE {
  VALUES ?c { wd:Q71631512 wd:Q4686479 wd:Q1643932 }   # RPG supplement, adventure module, tabletop RPG
  ?i wdt:P31 ?c . ?c rdfs:label ?cL FILTER(lang(?cL) = "en")
  ?i rdfs:label ?iLabel FILTER(lang(?iLabel) = "en")
  OPTIONAL { ?i wdt:P123 ?pub . ?pub rdfs:label ?pubL FILTER(lang(?pubL) = "en") }
  OPTIONAL { ?i wdt:P577 ?date }
  OPTIONAL { { ?i wdt:P212 ?isbn } UNION { ?i wdt:P957 ?isbn } }
  OPTIONAL { ?i wdt:P50 ?auth . ?auth rdfs:label ?authL FILTER(lang(?authL) = "en") }
  OPTIONAL { ?i wdt:P179 ?ser . ?ser rdfs:label ?serL FILTER(lang(?serL) = "en") }
  OPTIONAL { ?i wdt:P14656 ?grog } OPTIONAL { ?i wdt:P648 ?ol }
  OPTIONAL { ?wp schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }
}
GROUP BY ?i ?iLabel
"""
# Deliberately not queried: P7226 (RPGGeek ID) - BGG/RPGGeek data stays out of this database.


def collect_wikidata(db, source) -> int:
    """All tabletop-RPG items (games, supplements, adventures) in one SPARQL query. CC0."""
    save_source(db, source)
    d = _get(source.api, query=WIKIDATA_QUERY, format="json").json()
    rows = 0
    for b in d["results"]["bindings"]:
        r = {k: v["value"] for k, v in b.items()}
        qid = r["i"].rsplit("/", 1)[-1]
        save(db, source.id, qid, r["i"], "", _now(), json.dumps(r, ensure_ascii=False), {
            "title": r.get("iLabel"), "publisher": r.get("publisher"), "author": r.get("authors") or None,
            "year": (r.get("published") or "")[:4] or None, "isbn": r.get("isbns") or None,
            "product_type": r.get("type"), "fields": r})
        rows += 1
    db.commit()
    return rows


def collect_isfdb(db, source) -> int:
    """Rows of isfdb_game_pubs.tsv, exported from the ISFDB MySQL backup with refdb/isfdb_export.sql
    (the dump needs a free ISFDB login, so it is downloaded by hand; see README). CC BY 4.0."""
    import csv
    import os
    from pathlib import Path
    save_source(db, source)
    path = Path(os.environ.get("REFDB_CRAWL_ROOT", "/scraper")) / "isfdb" / "isfdb_game_pubs.tsv"
    if not path.exists():
        print(f"isfdb: {path} not found - export it first (refdb/isfdb_export.sql); skipped")
        return 0
    csv.field_size_limit(10_000_000)
    rows = 0
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            r = {k: (None if v in ("NULL", "") else v.replace("\t", "\t").replace("\n", " ")) for k, v in r.items()}
            save(db, source.id, r["pub_id"], f"https://www.isfdb.org/cgi-bin/pl.cgi?{r['pub_tag'] or r['pub_id']}",
                 "", _now(), "", {
                     "title": r["pub_title"], "publisher": r["publisher_name"], "author": r["authors"],
                     "year": (r["pub_year"] or "")[:4] if (r["pub_year"] or "0000")[:4] != "0000" else None,
                     "isbn": r["pub_isbn"], "code": r["pub_catalog"], "pages": r["pub_pages"],
                     "product_type": r["pub_ctype"], "fields": r})
            rows += 1
    db.commit()
    return rows


GAME_PUBLISHERS = re.compile(
    r"Black Library|BL Publishing|\bTSR\b|Wizards of the Coast|\bFASA\b|Games Workshop|Chaosium|White Wolf|"
    r"Steve Jackson Games|West End Games|Iron Crown|Palladium Books|Catalyst Game|Paizo|Game Designers'? Workshop|"
    r"Mongoose Publishing|Fantasy Flight|Pelgrane|Flying Buffalo|Green Ronin|Privateer Press|Pinnacle Entertainment|"
    r"Evil Hat|Arc Dream|Onyx Path|Cubicle 7|Modiphius|Free League|Kobold Press|Judges Guild|Mayfair Games|"
    r"R\. ?Talsorian|Hero Games|Eden Studios|Margaret Weis Productions|Last Unicorn|Hogshead|Avalanche Press|"
    r"Atlas Games|Necromancer Games|Goodman Games|Troll Lord|Sword ?& ?Sorcery Studio|Guardians of Order|"
    r"Gold Rush Games|Grey Ghost|Columbia Games|Fantasy Games Unlimited|Task Force Games|Avalon Hill", re.I)
GAME_SUBJECTS = re.compile(r"role[- ]?playing game|fantasy games|games, fantasy|dungeons (and|&) dragons", re.I)


def collect_openlibrary(db, source) -> int:
    """Stream Open Library's editions dump (~9 GB gzip, CC0) and keep game-publisher / role-playing
    editions. Nothing is stored except the matching lines."""
    import gzip
    save_source(db, source)
    rows = seen = 0
    now = _now()
    with httpx.stream("GET", source.api, headers={"User-Agent": UA}, timeout=600, follow_redirects=True) as r:
        r.raise_for_status()
        raw = _StreamFile(r.iter_raw(1 << 20))
        with gzip.open(raw, "rt", encoding="utf-8", errors="replace") as lines:
            for line in lines:
                seen += 1
                if seen % 2_000_000 == 0:
                    db.commit()
                    print(f"openlibrary: {seen:,} editions read, {rows:,} kept")
                parts = line.split("\t", 4)
                if len(parts) < 5 or not (GAME_PUBLISHERS.search(parts[4]) or GAME_SUBJECTS.search(parts[4])):
                    continue
                e = json.loads(parts[4])
                pubs = "; ".join(e.get("publishers") or [])
                subjects = " ".join(e.get("subjects") or [])
                if not (GAME_PUBLISHERS.search(pubs) or GAME_SUBJECTS.search(subjects)):
                    continue                    # the match was elsewhere (e.g. a description)
                isbns = (e.get("isbn_13") or []) + (e.get("isbn_10") or [])
                title = e.get("title", "") + (f": {e['subtitle']}" if e.get("subtitle") else "")
                key = e.get("key", parts[1])
                save(db, source.id, key, "https://openlibrary.org" + key, str(e.get("revision", "")), now, "", {
                    "title": title, "publisher": pubs or None, "isbn": "; ".join(isbns) or None,
                    "year": (re.search(r"(1[89]|20)\d\d", e.get("publish_date") or "") or [None])[0],
                    "pages": str(e["number_of_pages"]) if e.get("number_of_pages") else None,
                    "product_type": e.get("physical_format"), "fields": e})
                rows += 1
    db.commit()
    return rows


class _StreamFile:
    """Minimal file object over an httpx byte iterator, so gzip can read the download as it arrives."""

    def __init__(self, chunks) -> None:
        self._chunks, self._buf = chunks, b""

    def read(self, n: int = -1) -> bytes:
        while n < 0 or len(self._buf) < n:
            try:
                self._buf += next(self._chunks)
            except StopIteration:
                break
        out, self._buf = (self._buf, b"") if n < 0 else (self._buf[:n], self._buf[n:])
        return out
