from refdb.wikipedia import parse_tables

TEXT = """== Greyhawk ==
{| class="wikitable"
|+ style="text-align: left;" | Aerie of the Slave Lords - 1st Ed. AD&D
! scope="col" | Code
!TSR#
! Title !! Author(s) !! Published
|-
|A1
|9039||''[[Scourge of the Slave Lords|Slave Pits of the Undercity]]'' || [[David Cook (game designer)|David Cook]] || 1980
|-
| colspan="5" | a note row that must be skipped, not misaligned
|}
"""


def test_wikitable_rows() -> None:
    (r,) = parse_tables(TEXT)
    assert (r["title"], r["code"], r["author"], r["year"]) == ("Slave Pits of the Undercity", "9039", "David Cook", "1980")
    assert r["fields"]["series_code"] == "A1" and r["fields"]["section"] == "Greyhawk"
    assert r["fields"]["caption"] == "Aerie of the Slave Lords - 1st Ed. AD&D"
