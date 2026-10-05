from refdb.crawled import parse_waynes

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
