"""python -m refdb collect <source|all> [--limit N] [--db data/refdb.sqlite]
   python -m refdb import <other.sqlite>   (copy a long job's own database into the main one)
   python -m refdb stats [--db ...]"""
import argparse

from . import crawled, downloads, mediawiki, rpgnet, wikipedia
from .sources import SOURCES
from .store import connect


def main() -> None:
    ap = argparse.ArgumentParser(prog="refdb")
    ap.add_argument("command", choices=["collect", "stats", "merge", "export", "import"])
    ap.add_argument("source", nargs="?", default="all")
    ap.add_argument("--limit", type=int, default=0, help="only the first N pages (testing)")
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between requests")
    ap.add_argument("--db", default="data/refdb.sqlite")
    a = ap.parse_args()
    db = connect(a.db)
    if a.command == "merge":
        from .merge import merge
        print(f"products (all sources): {merge(db):,}")
        print(f"products (public release): {merge(db, public=True):,}")
        return
    if a.command == "import":                  # long jobs keep their own file: copy it in
        db.execute("ATTACH DATABASE ? AS other", (a.source,))
        for table in ("sources", "raw", "records", "systems"):
            if db.execute("SELECT 1 FROM other.sqlite_master WHERE name = ?", (table,)).fetchone():
                n = db.execute(f"INSERT OR REPLACE INTO {table} SELECT * FROM other.{table}").rowcount
                print(f"{table}: {n:,} rows")
        db.commit()
        db.execute("DETACH DATABASE other")
        return
    if a.command == "export":
        from pathlib import Path
        from .export import export
        print(f"release written: {export(db, Path(a.source if a.source != 'all' else 'release'))}")
        return
    if a.command == "stats":
        for row in db.execute("SELECT source, count(*), count(code), count(isbn), count(year) "
                              "FROM records GROUP BY source ORDER BY source"):
            print("%-16s records %6d  code %6d  isbn %6d  year %6d" % row)
        for row in db.execute("SELECT source, count(*) FROM systems GROUP BY source ORDER BY source"):
            print("%-16s systems %6d" % row)
        return
    long_jobs = ("rpgnet", "openlibrary")          # hours long: run them on their own
    ids = [k for k, s in SOURCES.items() if s.kind not in long_jobs] if a.source == "all" else [a.source]
    for sid in ids:
        s = SOURCES[sid]
        if s.kind == "mediawiki":
            pages, records = mediawiki.collect(db, s, a.limit, a.interval)
            print(f"{sid}: {pages} pages, {records} records")
        elif s.kind == "rpgnet":
            print(f"{sid}: {rpgnet.collect(db, s, a.limit)} records")
        elif s.kind == "wikipedia":
            print(f"{sid}: {wikipedia.collect(db, s)} rows")
        elif s.kind == "crawl":
            print(f"{sid}: {crawled.collect(db, s)} records")
        else:
            print(f"{sid}: {getattr(downloads, 'collect_' + s.kind)(db, s)} rows")


if __name__ == "__main__":
    main()
