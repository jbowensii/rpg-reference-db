"""RPGnet Gaming Index (index.rpg.net), recovered from the Wayback Machine. The live site went
offline in 2026; archive.org kept its pages. PRIVATE: (c) Dyvers Hands, used for matching only.

1. List every capture of display-entry.phtml from the Wayback CDX index (22 pages).
2. Normalise to one URL per product (mainid) and per edition (editionid), newest capture wins.
3. Fetch each capture raw (id_), slowly; already-fetched pages are skipped, so runs resume.
4. Parse: an edition page gives publisher (year), Stock, ISBN, system, notes (pages); every page
   also has the game's editions table (title, system, publisher, released, stock)."""
import datetime as dt
import html
import re
import time
from urllib.parse import parse_qs, urlsplit

import httpx

from .mediawiki import UA
from .store import save, save_raw, save_source, write_status

CDX = "http://web.archive.org/cdx/search/cdx"
WAYBACK = "http://web.archive.org/web/{ts}id_/{url}"


def _client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": UA}, timeout=120, follow_redirects=True)


def _get(http: httpx.Client, endpoint: str, **params) -> httpx.Response | None:
    # (`endpoint`, not `url`: the CDX API itself takes a parameter called url)
    for attempt in range(6):                     # archive.org is often busy: back off and retry
        try:
            r = http.get(endpoint, params=params or None)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except httpx.TransportError:
            pass
        time.sleep(20 * (attempt + 1))
    return None


def capture_list(http: httpx.Client) -> dict[str, tuple[str, str]]:
    """{'main:76' | 'edition:158': (timestamp, clean url)}, newest capture per key."""
    base = {"url": "index.rpg.net/display-entry.phtml*", "filter": "statuscode:200", "collapse": "urlkey"}
    pages = int(_get(http, CDX, showNumPages="true", **base).text.strip())
    out: dict[str, tuple[str, str]] = {}
    for page in range(pages):
        r = _get(http, CDX, fl="timestamp,original", page=str(page), **base)
        for line in (r.text.splitlines() if r else []):
            ts, _, orig = line.partition(" ")
            q = parse_qs(urlsplit(html.unescape(orig)).query)
            main, ed = (q.get("mainid") or [""])[0], (q.get("editionid") or [""])[0]
            if ed.isdigit():
                key, clean = f"edition:{ed}", f"https://index.rpg.net/display-entry.phtml?editionid={ed}"
            elif main.isdigit():
                key, clean = f"main:{main}", f"https://index.rpg.net/display-entry.phtml?mainid={main}"
            else:
                continue
            if key not in out or ts > out[key][0]:
                out[key] = (ts, orig)          # fetch the exact archived URL; keep the clean one as key
        time.sleep(2)
    return out


_LABELS = ("Title", "Author", "Book Type", "Genre", "Setting", "System")


def _lines(page: str) -> list[str]:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    return [re.sub(r"\s+", " ", l).strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", t)).splitlines()
            if l.strip()]


def parse_page(page: str) -> tuple[dict | None, list[dict]]:
    """(this edition's record or None, rows of the game's editions table)."""
    lines = _lines(page)
    head = re.search(r"<title>\s*(.*?)\s*-\s*RPGnet", page, re.S | re.I)
    rec: dict = {"fields": {"page_title": html.unescape(head.group(1)) if head else None}}
    for i, line in enumerate(lines[:-1]):
        if line in _LABELS and line.lower() not in rec["fields"]:
            rec["fields"][line.lower()] = lines[i + 1]
        elif line.startswith("Stock:"):
            rec["code"] = line.split(":", 1)[1].strip() or None
        elif line.startswith("ISBN:"):
            rec["isbn"] = line.split(":", 1)[1].strip() or None
        elif line == "This Edition":
            rec["publisher"] = lines[i + 1]
            m = re.match(r"\((\d{4})", lines[i + 2]) if i + 2 < len(lines) else None
            rec["year"] = m.group(1) if m else None
        elif line == "Notes on This Edition":
            note = lines[i + 1]
            rec["fields"]["edition_notes"] = note
            m = re.search(r"(\d+)\s*pages?", note, re.I)
            if m:
                rec["pages"] = m.group(1)
    f = rec["fields"]
    rec.update(title=f.get("title"), author=f.get("author"), product_type=f.get("book type"))
    edition = rec if (rec.get("publisher") or rec.get("isbn") or rec.get("code")) and rec.get("title") else None

    table = []
    m = re.search(r"Game Editions.*?boxHeader(.*?)</table>", page, re.S | re.I)   # the heading is its own table
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1) if m else "", re.S | re.I):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        eid = re.search(r"editionid=(\d+)", tr)
        if len(cells) >= 6 and eid and cells[1]:
            table.append({"title": cells[1], "publisher": cells[3] or None,
                          "year": (re.search(r"\d{4}", cells[4]) or [None])[0], "code": cells[5] or None,
                          "fields": {"edition_id": eid.group(1), "system": cells[2], "released": cells[4],
                                     "status": cells[6] if len(cells) > 6 else None}})
    return edition, table


def collect(db, source, limit: int = 0, interval: float = 1.5) -> int:
    save_source(db, source)
    http = _client()
    caps = capture_list(http)
    done = {r[0] for r in db.execute("SELECT key FROM raw WHERE source = ?", (source.id,))}
    todo = [(k, v) for k, v in sorted(caps.items()) if k not in done]
    print(f"rpgnet: {len(caps)} pages captured, {len(done)} already fetched, {len(todo)} to fetch")
    write_status("rpgnet", done=False, fetched=0, to_fetch=len(todo), captured=len(caps), records=0)
    if limit:
        todo = todo[:limit]
    rows = 0
    for n, (key, (ts, orig)) in enumerate(todo, 1):
        r = _get(http, WAYBACK.format(ts=ts, url=orig))
        time.sleep(interval)
        if r is None:
            continue
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        page = r.text
        save_raw(db, source.id, key, orig, ts, now, page)
        edition, table = parse_page(page)
        if edition and key.startswith("edition:"):
            save(db, source.id, key, orig, ts, now, "", edition)
            rows += 1
        for row in table:
            save(db, source.id, f"row:{row['fields']['edition_id']}", orig, ts, now, "", row)
            rows += 1
        if n % 100 == 0:
            db.commit()
            print(f"rpgnet: {n}/{len(todo)} fetched, {rows} records")
            write_status("rpgnet", done=False, fetched=n, to_fetch=len(todo), captured=len(caps), records=rows)
    db.commit()
    write_status("rpgnet", done=True, fetched=len(todo), to_fetch=len(todo), captured=len(caps), records=rows)
    return rows
