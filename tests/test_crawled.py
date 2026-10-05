from refdb.crawled import parse_tsrarchive, parse_waynes

PAGE = r"""---
title: "Advanced Dungeons & Dragons (AD&D) Modules A-G - Wayne's Books RPG Reference"
source_url: "http://www.waynesbooks.com/ModulesAG.html"
---
[**Return to AD\&D Central**](add.html) **Slave Pits of the Undercity (A1\)** At my blog
1980 ... David Cook ... 24 pages ... TSR 9039 ... ISBN 0935696253[Check Wayne's Books Inventory](x)
**Grimsyn Sector** **The fate of the galaxy depends upon you ...** blurb
1993 ... 96 pages ... WEG 21007 ... ISBN 0874312345[Amazon](y)
"""


def test_waynes_products() -> None:
    a, b = parse_waynes(PAGE)
    assert a["title"] == "Slave Pits of the Undercity (A1)" and a["fields"]["series_code"] == "A1"
    assert (a["year"], a["author"], a["pages"], a["code"], a["isbn"]) == ("1980", "David Cook", "24", "TSR 9039", "0935696253")
    assert a["fields"]["page"] == "Advanced Dungeons & Dragons (AD&D) Modules A-G"
    assert b["title"] == "Grimsyn Sector" and b["code"] == "WEG 21007" and "author" not in b


TSR = r"""---
title: "One-on-One Adventure Gamebooks Archive"
---
|  |  | **Castle Arcania**  |  |  | | --- | --- | | **Item Code:** | 8461 | | **Type:** | Game book | | **Author:** | James M. Ward | | **Published:** | 1985 | | **Format:** | [Slipcase](1on1-arc.jpg) | |
| **Fear \& FuryAhmut's Legion** | | **Item Code:** | 88570 | | **Published:** | 2002 |
| **Dungeonland (EX1\)** | | **Item Code:** | 9065 | | **Published:** | June 1983 | | **Notes:** | First print |
"""


def test_tsrarchive_products() -> None:
    a, f, b = parse_tsrarchive(TSR)
    assert f["title"] == "Fear & Fury Ahmut's Legion"
    assert (a["title"], a["code"], a["product_type"], a["author"], a["year"]) == ("Castle Arcania", "8461", "Game book", "James M. Ward", "1985")
    assert a["fields"]["format"] == "Slipcase" and "publisher" not in a
    assert (b["title"], b["code"], b["year"], b["fields"]["notes"]) == ("Dungeonland (EX1)", "9065", "1983", "First print")
