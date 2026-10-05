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
      CREATE TABLE sources (id TEXT PRIMARY KEY, name TEXT, url TEXT, licence TEXT, credit TEXT);
    """)
    products = db.execute(f"SELECT {', '.join(PRODUCT_COLS)} FROM public_products").fetchall()
    links = db.execute("SELECT product_id, source, key, url FROM public_product_records").fetchall()
    assert all(src in public for _, src, _, _ in links), "a private source reached the release"
    rel.executemany(f"INSERT INTO products VALUES ({','.join('?' * len(PRODUCT_COLS))})", products)
    rel.executemany("INSERT INTO product_records VALUES (?,?,?,?)", links)
    rel.executemany("INSERT INTO sources VALUES (?,?,?,?,?)",
                    [(s.id, s.name, s.url, s.licence, s.credit) for s in public.values()])
    rel.commit()
    rel.close()

    with (out / f"rpg-reference-db-{stamp}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PRODUCT_COLS)
        w.writerows(products)

    used = sorted({src for _, src, _, _ in links})
    lines = ["# Credits", "", f"Release {stamp}: {len(products):,} products from {len(used)} sources.", "",
             "| Source | Licence | Credit |", "|---|---|---|"]
    lines += [f"| [{public[s].name}]({public[s].url}) | {public[s].licence} | {public[s].credit} |" for s in used]
    lines += ["", "Records from share-alike sources (CC BY-SA, GFDL) keep those terms: reuse them under the same",
              "licence and credit the source. Each record links back to its source page (product_records.url)."]
    (out / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
