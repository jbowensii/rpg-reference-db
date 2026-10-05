"""Every source we collect from, with the licence and credit line that travel with its records.

`publish` decides whether a source's records go into the public release. Private sources are
still collected (they help identify books) but never leave the collector's own database.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    licence: str
    credit: str
    publish: bool
    # MediaWiki sources: API endpoint + the infobox template every product page uses.
    api: str = ""
    template: str = ""


FANDOM = "CC BY-SA 3.0"

SOURCES = {s.id: s for s in [
    Source("sarna", "Sarna.net BattleTechWiki", "https://www.sarna.net/wiki/", "GNU FDL 1.2",
           "BattleTechWiki contributors, sarna.net", True,
           "https://www.sarna.net/wiki/api.php", "InfoBoxProduct"),
    Source("whitewolf", "White Wolf Wiki", "https://whitewolf.fandom.com/", FANDOM,
           "White Wolf Wiki contributors, whitewolf.fandom.com", True,
           "https://whitewolf.fandom.com/api.php", "Book"),
    Source("forgottenrealms", "Forgotten Realms Wiki", "https://forgottenrealms.fandom.com/", FANDOM,
           "Forgotten Realms Wiki contributors, forgottenrealms.fandom.com", True,
           "https://forgottenrealms.fandom.com/api.php", "Book"),
    Source("wookieepedia", "Wookieepedia", "https://starwars.fandom.com/", FANDOM,
           "Wookieepedia contributors, starwars.fandom.com", True,
           "https://starwars.fandom.com/api.php", "ReferenceBook"),
    Source("memorybeta", "Memory Beta", "https://memory-beta.fandom.com/", FANDOM,
           "Memory Beta contributors, memory-beta.fandom.com", True,
           "https://memory-beta.fandom.com/api.php", "Novel"),
]}
