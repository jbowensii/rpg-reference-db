import sqlite3

from refdb.merge import isbn13s, merge, norm_code, norm_title
from refdb.store import SCHEMA


def test_normalisers() -> None:
    assert isbn13s("ISBN 0-935696-25-3 / 978-1-55560-310-6; bad 1234567890") == ["9780935696257", "9781555603106"]
    assert norm_title("The Slave Pits of the Undercity (A1)") == "slave pits of the undercity"
    assert "9039" in norm_code("TSR 9039") and "TSR9039" in norm_code("TSR 9039")
    assert set(norm_code("8415 (original) 967100000 (reissue)")) >= {"8415", "967100000"}


def test_merge_links_by_isbn_code_and_title() -> None:
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    rows = [
        # same ISBN, different sources -> one product; the wiki outranks Wayne's for the title
        ("waynesbooks", "w1", "Slave Pits of the Undercity (A1)", "TSR 9039", "0935696253", None, "1980"),
        ("wikipedia", "p1", "Slave Pits of the Undercity", "9039", None, "TSR", "1980"),
        ("rpgnet", "r1", "Slave Pits of the Undercity", None, "0-935696-25-3", "TSR, Inc.", "1980"),
        # same code but a different book -> stays separate
        ("tsrarchive", "t1", "Dragonlance Adventures", "9039", None, None, "1987"),
    ]
    for s, k, title, code, isbn, pub, year in rows:
        db.execute("INSERT INTO records (source, key, url, title, code, isbn, publisher, year) VALUES (?,?,?,?,?,?,?,?)",
                   (s, k, "", title, code, isbn, pub, year))
    assert merge(db) == 2
    (p,) = db.execute("SELECT title, publisher, isbn13, sources FROM products WHERE sources LIKE '%wayne%'").fetchall()
    assert p[0] == "Slave Pits of the Undercity" and p[1] == "TSR" and p[2] == "9780935696257"
    assert set(p[3].split("; ")) == {"wikipedia", "waynesbooks", "rpgnet"}
    # public merge leaves private sources (rpgnet, tsrarchive) out entirely; Wayne's is public (permission 2026-10-08)
    assert merge(db, public=True) == 1
    assert db.execute("SELECT sources FROM public_products").fetchone()[0] == "wikipedia; waynesbooks"


def test_credits_name_every_source() -> None:
    from refdb.export import credits_md
    from refdb.sources import SOURCES
    md = credits_md("2026-10-05", 10, ["wikipedia", "isfdb"])
    assert "Wikipedia contributors (Wikimedia Foundation)" in md and "ISFDB editors" in md
    assert "CC BY-SA 4.0" in md
    for s in SOURCES.values():
        if not s.publish:
            assert s.name in md                     # thanked even though their data is not released


def test_distributor_is_not_publisher() -> None:
    from refdb.merge import NOT_PUBLISHER
    assert NOT_PUBLISHER.match("Distributed by Random House")
    assert NOT_PUBLISHER.match("[s.n.]")
    assert not NOT_PUBLISHER.match("TSR")
    assert not NOT_PUBLISHER.match("Distant Horizons Press")
