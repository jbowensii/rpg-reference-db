"""Collector for wikis whose product pages carry an infobox (Sarna, White Wolf, Forgotten Realms,
Wookieepedia, Memory Beta, ...). Uses the public MediaWiki API: list every page that embeds the
infobox template, fetch their wikitext 50 at a time, keep every infobox field.

Polite by construction: one request per `interval` seconds, `maxlag` honoured, a User-Agent that
says who we are."""
import datetime as dt
import re
import time
from typing import Iterator
from urllib.parse import quote

import httpx
import mwparserfromhell

UA = "rpg-reference-db/0.1 (+https://github.com/jbowensii/rpg-reference-db)"

# Infobox parameter names (normalised: lower case, spaces/underscores/hyphens removed) -> our column.
SYNONYMS = {
    "code": ["productioncode", "code", "publication#", "number", "sku", "stocknumber", "stock",
             "productcode", "itemcode"],
    "isbn": ["isbn", "isbn13", "isbn10", "reference#"],
    "publisher": ["publisher", "publishers"],
    "author": ["author", "authors", "primarywriting", "writer", "writers", "designer", "designers"],
    "year": ["year", "released", "published", "releasedate", "publicationdate", "date"],
    "edition": ["edition", "gameedition", "rules"],
    "pages": ["pages"],
    "product_type": ["type", "booktype"],
    "cover": ["image", "cover"],
    "title": ["title", "name"],
}


def _norm(name: str) -> str:
    return re.sub(r"[\s_\-]", "", name.strip().lower())


def _text(value) -> str:
    """Plain text of a wikitext value: links -> their text, small templates -> their positional
    arguments ({{ISBN|0671034774}} -> 0671034774, {{srcdate|1999|July}} -> 1999 July), <br> -> space."""
    v = mwparserfromhell.parse(str(value))
    for t in v.filter_templates(recursive=False):
        v.replace(t, " ".join(str(a.value).strip() for a in t.params if not a.showkey))
    s = re.sub(r"<br\s*/?>", " ", str(v), flags=re.I)
    return re.sub(r"\s+", " ", mwparserfromhell.parse(s).strip_code()).strip()


def _template_block(wikitext: str, template: str) -> str | None:
    """The text of the first {{template ...}}, found by counting braces."""
    name = r"[\s_]*".join(re.escape(w) for w in re.split(r"[\s_]+", template.strip()))
    m = re.search(r"\{\{\s*" + name + r"\s*(?=[|}\n])", wikitext, re.I)
    if not m:
        return None
    depth, i = 0, m.start()
    while i < len(wikitext) - 1:
        pair = wikitext[i:i + 2]
        if pair == "{{":
            depth += 1
            i += 2
        elif pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[m.start():i]
        else:
            i += 1
    return None


def parse_infobox(wikitext: str, template: str) -> dict | None:
    """Every field of the first `{{template ...}}` on the page, markup stripped, plus our columns."""
    want = _norm(template)
    block = _template_block(wikitext, template)       # parse only the box: broken markup elsewhere
    # Bold/italic quote marks carry no data, and an unbalanced pair swallows the next fields.
    code = mwparserfromhell.parse(re.sub(r"'{2,}", "", block or wikitext))
    box = next((t for t in code.filter_templates(recursive=False) if _norm(str(t.name)) == want), None)
    if box is None:
        return None
    fields = {}
    for p in box.params:
        value = _text(p.value)
        if value:
            fields[str(p.name).strip()] = value
    rec: dict = {"fields": fields}
    by_norm = {_norm(k): v for k, v in fields.items()}
    for col, names in SYNONYMS.items():
        for n in names:
            for key in (n, n + "1"):        # per-edition fields: released1, pages1, isbn10-1 ...
                if by_norm.get(key):
                    rec[col] = by_norm[key]
                    break
            if col in rec:
                break
    return rec


class Wiki:
    def __init__(self, api: str, interval: float = 1.0) -> None:
        self.api = api
        self.interval = interval
        self._next = 0.0
        self.http = httpx.Client(headers={"User-Agent": UA}, timeout=60)

    def get(self, **params) -> dict:
        params = {"format": "json", "formatversion": "2", "maxlag": "5", **params}
        for attempt in range(6):
            wait = self._next - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._next = time.monotonic() + self.interval
            r = self.http.get(self.api, params=params)
            if r.status_code == 200:
                data = r.json()
                if data.get("error", {}).get("code") == "maxlag":     # server busy: back off
                    time.sleep(5 * (attempt + 1))
                    continue
                return data
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
        raise RuntimeError(f"{self.api}: gave up after retries")

    def pages_using(self, template: str) -> Iterator[str]:
        cont: dict = {}
        while True:
            d = self.get(action="query", list="embeddedin", eititle=f"Template:{template}",
                         einamespace="0", eilimit="500", **cont)
            for p in d["query"]["embeddedin"]:
                yield p["title"]
            if "continue" not in d:
                return
            cont = {"eicontinue": d["continue"]["eicontinue"], "continue": d["continue"]["continue"]}

    def contents(self, titles: list[str]) -> Iterator[tuple[str, str, str]]:
        """(title, revision id, wikitext), 50 titles per request."""
        for i in range(0, len(titles), 50):
            d = self.get(action="query", prop="revisions", rvprop="ids|content", rvslots="main",
                         titles="|".join(titles[i:i + 50]))
            for p in d["query"]["pages"]:
                revs = p.get("revisions") or []
                if revs:
                    yield p["title"], str(revs[0]["revid"]), revs[0]["slots"]["main"]["content"]


def page_url(base: str, title: str) -> str:
    return base.rstrip("/") + "/wiki/" + quote(title.replace(" ", "_")) if "fandom.com" in base \
        else base + quote(title.replace(" ", "_"))


def collect(db, source, limit: int = 0, interval: float = 1.0) -> tuple[int, int]:
    """Fetch and store every product page of a MediaWiki source. Returns (pages, records)."""
    from .store import save, save_raw, save_source
    save_source(db, source)
    wiki = Wiki(source.api, interval)
    titles = list(wiki.pages_using(source.template))
    if limit:
        titles = titles[:limit]
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    pages = records = 0
    for title, revid, text in wiki.contents(titles):
        pages += 1
        rec = parse_infobox(text, source.template)
        url = page_url(source.url, title)
        if rec is None:                     # keep the page anyway: a better parser can read it later
            save_raw(db, source.id, title, url, revid, now, text)
            continue
        rec.setdefault("title", title)
        save(db, source.id, title, url, revid, now, text, rec)
        records += 1
        if records % 200 == 0:
            db.commit()
    db.commit()
    return pages, records
