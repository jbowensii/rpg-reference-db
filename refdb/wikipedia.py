"""Wikipedia product-list articles ("List of Dungeons & Dragons modules", "List of Shadowrun books",
...): every row of every wikitable becomes a record, columns mapped by their header text."""
import datetime as dt
import re

import mwparserfromhell

from .mediawiki import Wiki, _text
from .store import save, save_raw, save_source

API = "https://en.wikipedia.org/w/api.php"

PAGES = [
    "List of Dungeons & Dragons modules", "List of Dungeons & Dragons rulebooks",
    "List of Dungeons & Dragons adventures", "List of Dungeons & Dragons fiction",
    "List of Forgotten Realms modules and sourcebooks", "List of Forgotten Realms novels",
    "List of Dragonlance modules and sourcebooks", "List of Dragonlance novels",
    "List of Eberron modules and sourcebooks", "List of Dark Sun modules and sourcebooks",
    "List of Shadowrun books", "List of GURPS books", "List of Traveller books", "List of BattleTech novels",
    "List of Vampire: The Masquerade books", "List of Mage: The Ascension books",
    "List of Werewolf: The Apocalypse books", "List of Wraith: The Oblivion books",
    "List of Changeling: The Dreaming books", "List of Vampire: The Dark Ages books",
    "List of Exalted publications", "List of Cyberpunk 2020 books",
    "List of Fading Suns books", "List of RuneQuest supplements", "List of Marvel RPG supplements",
    "List of Star Wars Roleplaying Game books", "List of D6 System books",
    "List of Warhammer Fantasy Roleplay publications", "List of Warhammer 40,000 novels",
    "List of Warhammer Fantasy novels", "List of Pathfinder books", "List of Dungeon Crawl Classics modules",
    "List of Fighting Fantasy gamebooks", "List of Lone Wolf media", "List of Call of Cthulhu books",
]

# Header text (lower case, punctuation squeezed) -> our column. Order matters: first match wins.
HEADERS = [
    ("code", r"^(tsr ?#|tsr no|product (code|no|number|#)|sku|stock( no| number| #)?|item( code)?|cat(alog(ue)?)?( no| number| #)?|ww ?#|fasa ?#|product)$"),
    ("series_code", r"^(code|module code|series code)$"),
    ("title", r"^(title|name|module|book|adventure|novel|product name)( title)?$"),
    ("isbn", r"^isbn"),
    ("author", r"^(authors?|writers?|designers?|authors?\s*/\s*designers?)"),
    ("year", r"^(published|publication date|release date|released|date|year|first published|pub\.? date|original release)"),
    ("edition", r"^(edition|rules edition|rules|game edition|system)$"),
    ("publisher", r"^publisher"),
    ("pages", r"^(pages|page count|pp)$"),
    ("product_type", r"^(type|format)$"),
]


def _header_col(h: str) -> str | None:
    h = re.sub(r"[\s\[\]().]+", " ", h.lower()).strip()
    for col, rx in HEADERS:
        if re.search(rx, h):
            return col
    return None


def parse_tables(wikitext: str) -> list[dict]:
    """Rows of every wikitable, each as {column: value, fields: {header: value, section: heading}}."""
    code = mwparserfromhell.parse(wikitext)
    out, section = [], ""
    for node in code.nodes:
        if isinstance(node, mwparserfromhell.nodes.Heading):
            section = _text(node.title)
            continue
        if not (isinstance(node, mwparserfromhell.nodes.Tag) and str(node.tag).strip() == "table"):
            continue
        headers: list[str] = []
        caption, rows, loose = "", [], []
        for ch in node.contents.filter_tags(recursive=False):
            tag = str(ch.tag).strip()
            if tag in ("th", "td"):          # cells before the first |- form an implicit first row
                loose.append(ch)
            elif tag == "tr":
                rows.append(ch.contents.filter_tags(recursive=False, matches=lambda t: str(t.tag).strip() in ("th", "td")))
            elif tag == "caption":
                caption = _text(ch.contents)
        if loose:
            # A "|+ caption" line comes through as a leading td cell: split it off as the caption.
            first_th = next((i for i, c in enumerate(loose) if str(c.tag).strip() == "th"), None)
            if first_th:
                caption = caption or " ".join(_text(c.contents) for c in loose[:first_th]).lstrip("+ ").strip()
                loose = loose[first_th:]
            rows.insert(0, loose)
        for cells in rows:
            if cells and all(str(c.tag).strip() == "th" for c in cells):
                headers = [_text(c.contents) for c in cells]
                continue
            if not headers or len(cells) != len(headers):     # rowspans/colspans: skip, don't misalign
                continue
            rec: dict = {"fields": {"section": section, **({"caption": caption} if caption else {})}}
            for h, c in zip(headers, cells):
                value = _text(c.contents)
                if not value:
                    continue
                rec["fields"][h] = value
                col = _header_col(h)
                if col == "series_code":
                    rec["fields"]["series_code"] = value
                elif col and col not in rec:
                    rec[col] = value
            if "series_code" in rec["fields"] and "code" not in rec:
                rec["code"] = rec["fields"]["series_code"]       # only a module code: use it as the code
            if rec.get("title"):
                out.append(rec)
    return out


def collect(db, source) -> int:
    save_source(db, source)
    wiki = Wiki(API, interval=1.0)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rows = 0
    for i in range(0, len(PAGES), 50):
        for title, revid, text in wiki.contents(PAGES[i:i + 50]):
            url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
            save_raw(db, source.id, title, url, revid, now, text)
            for n, rec in enumerate(parse_tables(text), 1):
                save(db, source.id, f"{title}#{n}", url, revid, now, "", rec)
                rows += 1
    db.commit()
    return rows
