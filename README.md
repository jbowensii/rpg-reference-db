# RPG Reference DB

A free, downloadable reference database of tabletop role-playing game products: rulebooks,
supplements, adventures, magazines and game fiction. Each record holds the title, product or stock
code (e.g. `TSR 9039`, `FASA 7101`, `WW 2026`), ISBN, publisher, author, year, edition, pages and
type. **Every record names the source it came from, and that source's licence.**

It is assembled from public reference sources: wikis, open library data and fan indexes. It is
built to identify game books, for example in
[book_sorter](https://github.com/jbowensii/book_sorter), and to be useful to anyone cataloguing
RPG collections.

> Status: collecting. About 24,000 product records from the open sources so far; the first public
> release will be published under [Releases](../../releases) once the remaining sources are in and
> the records are merged and checked.

## Sources and credits

Thank you to every editor of these wikis, databases and indexes. Every record names its source.

| Source | What it gives | Licence | Public release |
|---|---|---|---|
| [Wikipedia](https://en.wikipedia.org/) RPG product lists | D&D, Shadowrun, Pathfinder, World of Darkness, BattleTech, Fighting Fantasy and more: codes, ISBNs, authors, years | CC BY-SA 4.0 | yes |
| [Sarna.net BattleTechWiki](https://www.sarna.net/wiki/) | FASA / FanPro / Catalyst BattleTech: production codes, ISBNs, pages | GNU FDL 1.2 | yes |
| [White Wolf Wiki](https://whitewolf.fandom.com/) | White Wolf / Onyx Path: WW numbers, ISBNs | CC BY-SA 3.0 | yes |
| [Forgotten Realms Wiki](https://forgottenrealms.fandom.com/) | TSR / WotC Forgotten Realms: codes, ISBNs | CC BY-SA 3.0 | yes |
| [Wookieepedia](https://starwars.fandom.com/) | Star Wars reference and RPG books | CC BY-SA 3.0 | yes |
| [Memory Beta](https://memory-beta.fandom.com/) | Star Trek books incl. FASA RPG stock numbers | CC BY-SA 3.0 | yes |
| [Wikidata](https://www.wikidata.org/) | ~3.7k games, supplements, adventures; cross-links between catalogues | CC0 | yes |
| [ISFDB](https://www.isfdb.org/) | Game-world fiction (Black Library, TSR/WotC, BattleTech, Star Wars, Star Trek...) | CC BY 4.0 | yes |
| [Open Library](https://openlibrary.org/) | Editions from game publishers: ISBNs, dates, pages | CC0 | yes |
| [John H. Kim's RPG Encyclopedia](https://www.darkshire.net/jhkim/rpg/encyclopedia/) | ~2,000 game-system editions | reuse with credit, link and notice | after notice |
| [Traveller Wiki](https://wiki.travellerrpg.com/) | 1,334 Traveller products, all publishers | no open licence | asking |
| [TTRPG Wiki](https://ttrpgwiki.com/) | ~300 current game systems | none stated | asking |
| [The TSR Archive](http://www.tsrarchive.com/) | TSR item codes, formats, years | none stated | asking |
| [Wayne's Books RPG Reference](http://www.waynesbooks.com/) | Print-era products: stock codes, ISBNs, pages | copyright | asking |
| RPGnet Gaming Index (via the Internet Archive) | Editions, stock numbers, ISBNs | (c) Dyvers Hands | no (private) |
| Le GRoG | French and English editions, ISBNs, pages | EU database right | no (private) |

"Asking" means the owner is being asked for permission; until then those records are used
privately for matching and are not in the release.

## What is deliberately NOT in the public release

- **Sources whose owner hasn't allowed republishing.** Some sites are used privately, only to
  help identify books, and never leave the collector's own database. That includes sites with no
  licence (until their owners agree) and sites whose terms forbid reproduction.
- **Anything from BoardGameGeek / RPGGeek**, or sites built on their data.
- **Descriptions, reviews and cover images** from sources that don't licence them. Releases carry
  facts (titles, codes, ISBNs, names, dates, page counts) plus links back to each source page.
- **Nothing about anyone's personal collection.** No file names, paths or checksums.

## Licence

- **Code** (`refdb/`, `tests/`): **MIT**, see `LICENSE`.
- **Data** (the released database and CSV): **CC BY-SA 4.0**, see `LICENSE-DATA.md`. The wiki
  sources are share-alike, so the combined data must be too; the CC0 and CC BY sources fit inside
  it. Values from Sarna.net stay under the GNU FDL 1.2 (marked per product).
- **Credits**: every release ships `CREDITS.md`, listing each source, who makes it, how to contact
  them and its licence, and thanking the sources used privately. Contacts are only the ones the
  owners publish themselves.

## Running the collector

```bash
pip install -r requirements.txt
python -m refdb collect sarna            # or: all
python -m refdb stats
```

It is deliberately slow and polite: one request per second, Wikimedia `maxlag` honoured, and a
User-Agent that points back to this repository. Raw source text is stored with every record, so
parsing can be improved without fetching again.
