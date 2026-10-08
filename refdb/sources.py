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
    # Download sources: `api` is the file / query endpoint and `kind` names the collector.
    api: str = ""
    template: str = ""
    kind: str = "mediawiki"
    # Credits: who made the data and how to reach them. Only contacts the owners publish themselves;
    # personal email addresses are never added without the owner's OK.
    owner: str = ""
    contact: str = ""


FANDOM = "CC BY-SA 3.0"

SOURCES = {s.id: s for s in [
    Source("sarna", "Sarna.net BattleTechWiki", "https://www.sarna.net/wiki/", "GNU FDL 1.2",
           "BattleTechWiki contributors, sarna.net", True,
           "https://www.sarna.net/wiki/api.php", "InfoBoxProduct",
           owner="BattleTechWiki contributors (sarna.net)", contact="https://www.sarna.net/wiki/Main_Page"),
    Source("whitewolf", "White Wolf Wiki", "https://whitewolf.fandom.com/", FANDOM,
           "White Wolf Wiki contributors, whitewolf.fandom.com", True,
           "https://whitewolf.fandom.com/api.php", "Book",
           owner="White Wolf Wiki contributors (hosted by Fandom)", contact="https://community.fandom.com/wiki/Special:Contact"),
    Source("forgottenrealms", "Forgotten Realms Wiki", "https://forgottenrealms.fandom.com/", FANDOM,
           "Forgotten Realms Wiki contributors, forgottenrealms.fandom.com", True,
           "https://forgottenrealms.fandom.com/api.php", "Book",
           owner="Forgotten Realms Wiki contributors (hosted by Fandom)", contact="https://community.fandom.com/wiki/Special:Contact"),
    Source("wookieepedia", "Wookieepedia", "https://starwars.fandom.com/", FANDOM,
           "Wookieepedia contributors, starwars.fandom.com", True,
           "https://starwars.fandom.com/api.php", "ReferenceBook",
           owner="Wookieepedia contributors (hosted by Fandom)", contact="https://community.fandom.com/wiki/Special:Contact"),
    Source("memorybeta", "Memory Beta", "https://memory-beta.fandom.com/", FANDOM,
           "Memory Beta contributors, memory-beta.fandom.com", True,
           "https://memory-beta.fandom.com/api.php", "Novel",
           owner="Memory Beta contributors (hosted by Fandom)", contact="https://community.fandom.com/wiki/Special:Contact"),
    Source("wikipedia", "Wikipedia RPG product lists", "https://en.wikipedia.org/", "CC BY-SA 4.0",
           "Wikipedia contributors, en.wikipedia.org", True, "https://en.wikipedia.org/w/api.php", kind="wikipedia",
           owner="Wikipedia contributors (Wikimedia Foundation)", contact="https://en.wikipedia.org/wiki/Wikipedia:Contact_us"),
    Source("wikidata", "Wikidata", "https://www.wikidata.org/", "CC0 1.0", "Wikidata contributors, wikidata.org",
           True, "https://query.wikidata.org/sparql", kind="wikidata",
           owner="Wikidata contributors (Wikimedia Foundation)", contact="https://www.wikidata.org/wiki/Wikidata:Contact_the_development_team"),
    Source("isfdb", "ISFDB - Internet Speculative Fiction Database", "https://www.isfdb.org/", "CC BY 4.0",
           "ISFDB, isfdb.org", True, "", kind="isfdb",
           owner="ISFDB editors", contact="https://www.isfdb.org/wiki/index.php/ISFDB:Contact"),
    Source("openlibrary", "Open Library", "https://openlibrary.org/", "CC0 1.0", "Open Library, openlibrary.org",
           True, "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz", kind="openlibrary",
           owner="Open Library (Internet Archive)", contact="https://openlibrary.org/contact"),
    # Kim, ttrpgwiki, Traveller Wiki and the TSR Archive agreed 2026-10-08 (facts only).
    Source("kim", "John H. Kim's RPG Encyclopedia", "https://www.darkshire.net/jhkim/rpg/encyclopedia/",
           "Used with permission (facts only), granted 2026-10-08", "John H. Kim (J. Hanju Kim), darkshire.net",
           True, "https://www.darkshire.net/jhkim/rpg/encyclopedia/fulllist.xml", kind="kim",
           owner="John H. Kim (J. Hanju Kim)", contact="jhkim@darkshire.net"),
    Source("ttrpgwiki", "TTRPG Wiki", "https://ttrpgwiki.com/", "Used with permission (facts only), granted 2026-10-08", "ttrpgwiki.com",
           True, "https://ttrpgwiki.com/data/systems.json", kind="ttrpgwiki",
           owner="TTRPG Wiki", contact="thettrpgwiki@gmail.com"),
    Source("traveller", "Traveller Wiki", "https://wiki.travellerrpg.com/", "Used with permission (facts only), granted 2026-10-08",
           "Traveller Wiki contributors, wiki.travellerrpg.com", True,
           "https://wiki.travellerrpg.com/api.php", kind="traveller",
           owner="Traveller Wiki contributors", contact="https://wiki.travellerrpg.com/"),
    Source("rpgnet", "RPGnet Gaming Index (via the Wayback Machine)", "https://index.rpg.net/",
           "(c) Dyvers Hands, all rights reserved", "RPGnet Gaming Index, index.rpg.net; Internet Archive",
           False, "", kind="rpgnet",
           owner="RPGnet / Dyvers Hands", contact="https://www.rpg.net/"),
    # Crawled with scraper-stack: `api` = the job folder, `template` = the page parser.
    # Wayne granted permission 2026-10-08: facts only (title, year, author, pages, codes, ISBN), no blurbs.
    Source("waynesbooks", "Wayne's Books RPG Reference", "http://www.waynesbooks.com/",
           "Used with permission of Waynes World of Books (facts only)", "Wayne's Books RPG Reference, waynesbooks.com", True,
           "waynesbooks", "waynes", kind="crawl",
           owner="Wayne's Books", contact="http://www.waynesbooks.com/ContactWaynesBookscom.html"),
    Source("tsrarchive", "The TSR Archive", "http://www.tsrarchive.com/", "Used with permission (facts only), granted 2026-10-08",
           "The TSR Archive, tsrarchive.com", True, "tsrarchive", "tsrarchive", kind="crawl",
           owner="The TSR Archive", contact="http://www.tsrarchive.com/"),
    # Private only: Le GRoG's legal page invokes EU database rights and forbids public reproduction.
    Source("legrog", "Le GRoG - Guide du Rôliste Galactique", "https://www.legrog.org/",
           "(c) Le GRoG; EU database right, no public reproduction", "Le Guide du Rôliste Galactique, legrog.org",
           False, "legrog", "grog", kind="crawl",
           owner="Le GRoG association and contributors", contact="https://www.legrog.org/"),
]}
