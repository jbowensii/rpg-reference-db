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
