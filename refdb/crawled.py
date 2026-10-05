"""Parsers for pages crawled by scraper-stack (one markdown file per page under <job>/pages/).

The crawl root is /scraper inside the collector container (Tower05: /mnt/user/scraper); set
REFDB_CRAWL_ROOT to read it from elsewhere (e.g. //tower05/scraper on Windows)."""
import datetime as dt
import os
import re
from pathlib import Path

from .store import save, save_source

CRAWL_ROOT = Path(os.environ.get("REFDB_CRAWL_ROOT", "/scraper"))


def _unescape(s: str) -> str:
    """Markdown escapes back to plain text: 'Dungeons \\& Dragons \\(A1\\)' -> 'Dungeons & Dragons (A1)'."""
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!&|<>~])", r"\1", s).strip()


def _front_matter(md: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", md, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"')
    return out


# ---------------------------------------------------------------------------- Wayne's Books
_W_TITLE = re.compile(r"\*\*([^*\[\]]{3,140}?)\*\*")
# "1980 ... David Cook ... 24 pages ... TSR 9039 ... ISBN 0935696253" (parts vary; the line ends at a link)
_W_DATA = re.compile(r"(?<![\d.])((?:1[89]|20)\d\d\b[^\[\n]{0,300}?\.\.\.[^\[\n]{3,400})")
_NAV = re.compile(r"return to|browse my|items currently|check wayne|series$|^modules|^hardbacks|^accessories", re.I)


def parse_waynes(md: str) -> list[dict]:
    """One record per product data line, paired with the nearest bold title before it."""
    page_title = _front_matter(md).get("title", "").replace(" - Wayne's Books RPG Reference", "")
    events = [(m.start(), "title", _unescape(m.group(1))) for m in _W_TITLE.finditer(md)]
    events += [(m.start(), "data", _unescape(m.group(1))) for m in _W_DATA.finditer(md)]
    out, title = [], None
    for _, kind, text in sorted(events):
        if kind == "title":
            # bold cover blurbs ("The fate of the galaxy depends upon you ...") are not titles
            if not _NAV.search(text) and not re.search(r"(\.\.\.|…|[!?])\s*$", text):
                title = text
            continue
        if not title:
            continue
        rec = {"title": title, "fields": {"data_line": text, "page": page_title}}
        m = re.search(r"\(([^()]{1,20})\)\s*$", title)          # "Slave Pits of the Undercity (A1)"
        if m:
            rec["fields"]["series_code"] = m.group(1)
        authors = []
        for part in (p.strip(" .,;") for p in text.split("...")):
            if not part:
                continue
            if re.fullmatch(r"(?:1[89]|20)\d\d(?:\s*[-/,&]\s*(?:1[89]|20)?\d\d)*", part) and "year" not in rec:
                rec["year"] = part[:4]
            elif re.fullmatch(r"\d+\s*pages?(?:\s*\+.*)?", part, re.I):
                rec["pages"] = re.match(r"\d+", part).group(0)
            elif re.match(r"ISBN", part, re.I):
                rec["isbn"] = re.sub(r"^ISBN[:\s]*", "", part, flags=re.I)
            elif re.search(r"\d", part) and re.fullmatch(r"[A-Za-z&]{2,12}[\s#-]*[\w#./-]*\d[\w./-]*", part):
                rec["code"] = part                               # "TSR 9039", "GDW #?", "FASA 7101"
            else:
                authors.append(part)
        if authors:
            rec["author"] = "; ".join(authors)
        out.append(rec)
        title = None                                            # one data line per title
    return out


PARSERS = {"waynes": parse_waynes}


def collect(db, source) -> int:
    """Parse every crawled page of a scraper-stack job into records."""
    save_source(db, source)
    pages = sorted((CRAWL_ROOT / source.api / "pages").glob("*.md"))
    parse = PARSERS[source.template]
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rows = 0
    for p in pages:
        md = p.read_text(encoding="utf-8", errors="replace")
        url = _front_matter(md).get("source_url", "")
        for n, rec in enumerate(parse(md), 1):
            save(db, source.id, f"{p.stem}#{n}", url, "", now, rec["fields"].get("data_line", ""), rec)
            rows += 1
    db.commit()
    return rows
