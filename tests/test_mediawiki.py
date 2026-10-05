from refdb.mediawiki import parse_infobox


def test_infobox_fields_and_columns() -> None:
    text = """Intro text.
{{Book
| title = Vampire: The Masquerade Revised
| publication_# = WW2026
| reference_# = ISBN 1-56504-249-6
| pages = 304
| published = 1998
| author = [[Justin Achilli]], [[Andrew Bates]]
| publisher = [[White Wolf Publishing]]
| pdf = {{DTRPG|1234}}
| blank =
}}
More text with {{Book}} later."""
    rec = parse_infobox(text, "Book")
    assert rec["code"] == "WW2026"
    assert rec["isbn"] == "ISBN 1-56504-249-6"
    assert rec["author"] == "Justin Achilli, Andrew Bates"          # wiki links stripped
    assert rec["publisher"] == "White Wolf Publishing"
    assert rec["year"] == "1998" and rec["pages"] == "304"
    assert rec["fields"]["pdf"] == "1234"                            # {{DTRPG|1234}} -> its argument
    assert "blank" not in rec["fields"]


def test_value_templates_and_breaks() -> None:
    rec = parse_infobox("{{Novel |ISBN={{ISBN|0671034774}} |published={{srcdate|1999|July}} "
                        "|title=Technical Readout: 3025<br/>The Succession Wars}}", "Novel")
    assert rec["isbn"] == "0671034774" and rec["year"] == "1999 July"
    assert rec["title"] == "Technical Readout: 3025 The Succession Wars"


def test_template_name_normalised_and_missing() -> None:
    assert parse_infobox("{{InfoBoxProduct |productioncode=1600 |ISBN13=978-1-55560-300-8}}",
                         "InfoBoxProduct")["code"] == "1600"
    assert parse_infobox("{{Infobox_Product |year=1985}}", "Infobox Product")["year"] == "1985"
    assert parse_infobox("no box here", "Book") is None


def test_box_found_despite_broken_markup_elsewhere() -> None:
    # Forgotten Realms pages: broken markup later on the page hid the whole infobox from the parser.
    text = ("{{Book\n| code = 8548 (hardcover) <br /> 8548P (paperback)\n| author = [[Ed Greenwood]]\n}}\n"
            "Text {{yearlink|1994 and an unclosed template '' {{refs")
    rec = parse_infobox(text, "Book")
    assert rec["code"] == "8548 (hardcover) 8548P (paperback)" and rec["author"] == "Ed Greenwood"
    assert parse_infobox("{{Book/subsection | title = X}}", "Book") is None      # a different template


def test_unbalanced_italics_and_numbered_editions() -> None:
    text = ("{{Book\n| caption = Cover of ''Elminster'.'\n| code = 8548\n| publisher = [[TSR, Inc.]]\n"
            "| released1 = December 1994\n| pages1 = 320\n| isbn10-1 = 1-5607-6936-X\n"
            "| followed_by = Elminster in Myth Drannor''\n}}")
    rec = parse_infobox(text, "Book")
    assert rec["code"] == "8548" and rec["publisher"] == "TSR, Inc."
    assert rec["year"] == "December 1994" and rec["pages"] == "320" and rec["isbn"] == "1-5607-6936-X"
