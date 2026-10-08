import sqlite3

from refdb.export import export
from refdb.merge import merge
from refdb.store import SCHEMA, save_system


def test_release_has_public_systems_only(tmp_path, monkeypatch) -> None:
    import dataclasses
    from refdb.sources import SOURCES
    monkeypatch.setitem(SOURCES, "legrog", dataclasses.replace(SOURCES["legrog"], publish=False))
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.execute("INSERT INTO records (source, key, url, title, isbn, year) VALUES "
               "('wikipedia', 'w1', 'u', 'Slave Pits of the Undercity', '0935696253', '1980')")
    save_system(db, "kim", "k1", "u", {"name": "Star Wars", "publisher": "West End Games", "year": "1987"})
    save_system(db, "legrog", "g1", "u", {"name": "EABA"})          # made private above: must not leave
    merge(db, public=True)
    rel = sqlite3.connect(export(db, tmp_path))
    assert rel.execute("SELECT name, publisher FROM systems").fetchall() == [("Star Wars", "West End Games")]
    assert "John H. Kim" in (tmp_path / "CREDITS.md").read_text(encoding="utf-8")
