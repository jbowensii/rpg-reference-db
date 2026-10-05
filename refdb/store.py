"""SQLite store: one portable file anyone can open. Raw source text is kept next to the parsed
record so a better parser can re-read everything without fetching again."""
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, name TEXT, url TEXT, licence TEXT, credit TEXT, publish INTEGER);
CREATE TABLE IF NOT EXISTS raw (
  source TEXT, key TEXT, url TEXT, revision TEXT, fetched_at TEXT, body TEXT,
  PRIMARY KEY (source, key));
CREATE TABLE IF NOT EXISTS records (
  source TEXT, key TEXT, url TEXT,
  title TEXT, code TEXT, isbn TEXT, publisher TEXT, author TEXT, year TEXT,
  edition TEXT, pages TEXT, product_type TEXT, cover TEXT,
  fields TEXT,                         -- every infobox field, JSON, as the source wrote it
  PRIMARY KEY (source, key));
CREATE TABLE IF NOT EXISTS systems (     -- game systems / game lines (not individual books)
  source TEXT, key TEXT, url TEXT,
  name TEXT, edition TEXT, publisher TEXT, year TEXT, author TEXT, family TEXT,
  fields TEXT,
  PRIMARY KEY (source, key));
CREATE INDEX IF NOT EXISTS records_isbn ON records(isbn);
CREATE INDEX IF NOT EXISTS records_code ON records(code);
"""

COLUMNS = ("title", "code", "isbn", "publisher", "author", "year", "edition", "pages", "product_type", "cover")


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def save_source(db: sqlite3.Connection, s) -> None:
    db.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?)",
               (s.id, s.name, s.url, s.licence, s.credit, int(s.publish)))


def save_system(db: sqlite3.Connection, source: str, key: str, url: str, row: dict) -> None:
    db.execute("INSERT OR REPLACE INTO systems VALUES (?,?,?,?,?,?,?,?,?,?)",
               (source, key, url, row.get("name"), row.get("edition"), row.get("publisher"), row.get("year"),
                row.get("author"), row.get("family"), json.dumps(row.get("fields") or {}, ensure_ascii=False)))


def save_raw(db: sqlite3.Connection, source: str, key: str, url: str, revision: str, fetched_at: str,
             body: str) -> None:
    db.execute("INSERT OR REPLACE INTO raw VALUES (?,?,?,?,?,?)", (source, key, url, revision, fetched_at, body))


def save(db: sqlite3.Connection, source: str, key: str, url: str, revision: str, fetched_at: str,
         body: str, record: dict) -> None:
    save_raw(db, source, key, url, revision, fetched_at, body)
    db.execute(f"INSERT OR REPLACE INTO records (source, key, url, {', '.join(COLUMNS)}, fields) "
               f"VALUES (?,?,?,{','.join('?' * len(COLUMNS))},?)",
               (source, key, url, *(record.get(c) for c in COLUMNS),
                json.dumps(record.get("fields") or {}, ensure_ascii=False)))


def write_status(source: str, **info) -> None:
    """data/<source>.status.json: progress of long jobs, readable over the network share."""
    import datetime as dt
    p = Path("data") / f"{source}.status.json"
    p.parent.mkdir(exist_ok=True)
    info["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    p.write_text(json.dumps(info), encoding="utf-8")
