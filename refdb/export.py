"""Build the public release from a merged database: only publish=True sources ever leave.

Writes into <out>/:
  rpg-reference-db-<date>.sqlite  products, product_records (with source page links), sources
  rpg-reference-db-<date>.csv     products, one row each
  CREDITS.md                      every source in the release, its licence and credit line"""
import csv
import datetime as dt
import sqlite3
from pathlib import Path

from .sources import SOURCES

PRODUCT_COLS = ("id", "title", "publisher", "author", "year", "code", "isbn13", "edition", "pages",
                "product_type", "isbns", "codes", "sources", "provenance")


def export(db: sqlite3.Connection, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    public = {k: s for k, s in SOURCES.items() if s.publish}
    target = out / f"rpg-reference-db-{stamp}.sqlite"
    target.unlink(missing_ok=True)
    rel = sqlite3.connect(target)
    rel.executescript(f"""
      CREATE TABLE products ({', '.join(c + (' INTEGER PRIMARY KEY' if c == 'id' else ' TEXT') for c in PRODUCT_COLS)});
      CREATE TABLE product_records (product_id INTEGER, source TEXT, key TEXT, url TEXT);
      CREATE TABLE sources (id TEXT PRIMARY KEY, name TEXT, url TEXT, licence TEXT, credit TEXT,
                            owner TEXT, contact TEXT);
      CREATE TABLE systems (source TEXT, key TEXT, url TEXT, name TEXT, edition TEXT, publisher TEXT,
                            year TEXT, author TEXT, family TEXT);
    """)
    systems = db.execute(f"SELECT source, key, url, name, edition, publisher, year, author, family FROM systems "
                         f"WHERE source IN ({','.join('?' * len(public))})", list(public)).fetchall()
    rel.executemany("INSERT INTO systems VALUES (?,?,?,?,?,?,?,?,?)", systems)
    products = db.execute(f"SELECT {', '.join(PRODUCT_COLS)} FROM public_products").fetchall()
    links = db.execute("SELECT product_id, source, key, url FROM public_product_records").fetchall()
    assert all(src in public for _, src, _, _ in links), "a private source reached the release"
    rel.executemany(f"INSERT INTO products VALUES ({','.join('?' * len(PRODUCT_COLS))})", products)
    rel.executemany("INSERT INTO product_records VALUES (?,?,?,?)", links)
    rel.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?)",
                    [(s.id, s.name, s.url, s.licence, s.credit, s.owner, s.contact) for s in public.values()])
    rel.commit()
    rel.close()

    with (out / f"rpg-reference-db-{stamp}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PRODUCT_COLS)
        w.writerows(products)

    used = sorted({src for _, src, _, _ in links} | {s[0] for s in systems})
    (out / "CREDITS.md").write_text(credits_md(stamp, len(products), used), encoding="utf-8")
    root = Path(__file__).resolve().parent.parent
    for name in ("LICENSE", "LICENSE-DATA.md", "DISCLAIMER.md"):   # licences + disclaimer travel with every release
        if (root / name).exists():
            (out / name).write_text((root / name).read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _contact(c: str) -> str:
    return f"[{c}](mailto:{c})" if "@" in c and not c.startswith("http") else (f"<{c}>" if c else "")


def credits_md(stamp: str, n_products: int, used: list[str]) -> str:
    """Thanks to every source: those in this release, and those used privately for matching."""
    lines = ["# Credits and thanks", "",
             f"Release {stamp}: {n_products:,} products from {len(used)} sources. Thank you to everyone",
             "who built and maintains these sources. Every record links back to its source page",
             "(`product_records.url`). Data licence: CC BY-SA 4.0 (see LICENSE-DATA.md).", "",
             "References only: no works are included in whole or in part, and all product and company names",
             "are trademarks of their respective owners (see DISCLAIMER.md).", "",
             "## Sources in this release", "",
             "| Source | Made by | Contact | Licence |", "|---|---|---|---|"]
    for sid in used:
        s = SOURCES[sid]
        lines.append(f"| [{s.name}]({s.url}) | {s.owner or s.credit} | {_contact(s.contact)} | {s.licence} |")
    private = [s for s in SOURCES.values() if not s.publish]
    if private:
        lines += ["", "## Also with thanks", "",
                  "These sources helped identify books privately. None of their data is in this release",
                  "(their owners have not agreed to republication, or their terms don't allow it).", "",
                  "| Source | Made by | Contact |", "|---|---|---|"]
        lines += [f"| [{s.name}]({s.url}) | {s.owner or s.credit} | {_contact(s.contact)} |" for s in private]
    return "\n".join(lines) + "\n"
