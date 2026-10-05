from refdb.rpgnet import parse_page

PAGE = """<html><head><title>Warhammer Fantasy Roleplay (1989 Games Workshop edition) - RPGnet RPG Game Index</title></head>
<body><div>Title</div><div>Warhammer Fantasy Roleplay</div><div>Author</div><div>Chris Pramas</div>
<div>Book Type</div><div>Core Rules</div><div>This Edition</div><div>Games Workshop</div><div>(1989)</div>
<div>Stock: 20</div><div>ISBN:&nbsp;1-869893-58-1</div><div>System</div><div>Warhammer Fantasy Roleplay</div>
<div>Notes on This Edition</div><div>366 pages. First edition soft cover.</div>
<table class='boxWide'><tr><td><div class='sitesubhead'>Game Editions</div></td></tr></table>
<table class='boxWide'><tr class='boxHeader'><td>#</td><td>Title</td><td>System</td><td>Publisher</td><td>Released</td><td>Stock</td><td>Status</td></tr>
<tr><td><a href="https://index.rpg.net/display-entry.phtml?mainid=76&editionid=12551">1</a></td>
<td><a href="x?editionid=12551">Warhammer Fantasy Roleplay HC</a></td><td>WFRP 1</td><td>Games Workshop </td><td>1986</td><td>20</td><td>Out of print</td></tr>
</table></body></html>"""


def test_edition_page() -> None:
    ed, table = parse_page(PAGE)
    assert (ed["title"], ed["author"], ed["publisher"], ed["year"]) == ("Warhammer Fantasy Roleplay", "Chris Pramas", "Games Workshop", "1989")
    assert (ed["code"], ed["isbn"], ed["pages"], ed["product_type"]) == ("20", "1-869893-58-1", "366", "Core Rules")
    (row,) = table
    assert (row["title"], row["publisher"], row["year"], row["code"]) == ("Warhammer Fantasy Roleplay HC", "Games Workshop", "1986", "20")
    assert row["fields"]["edition_id"] == "12551"
