# RPG Reference DB

A free, downloadable reference database of tabletop role-playing game products: rulebooks,
supplements, adventures, magazines and game fiction. Each record holds the title, product or stock
code (e.g. `TSR 9039`, `FASA 7101`, `WW 2026`), ISBN, publisher, author, year, edition, pages and
type. **Every record names the source it came from, and that source's licence.**

It is assembled from public reference sources: wikis, open library data and fan indexes. It is
built to identify game books, for example in
[book_sorter](https://github.com/jbowensii/book_sorter), and to be useful to anyone cataloguing
RPG collections.

> Status: collector under construction. The first public release will be published under
> [Releases](../../releases) once the wiki sources are collected and checked.

## Sources and credits

| Source | What it gives | Licence | In the public release |
|---|---|---|---|
| [Sarna.net BattleTechWiki](https://www.sarna.net/wiki/) | FASA / FanPro / Catalyst BattleTech products: production codes, ISBNs, pages | GNU FDL 1.2 | yes |
| [White Wolf Wiki](https://whitewolf.fandom.com/) | White Wolf / Onyx Path books: WW numbers, ISBNs | CC BY-SA 3.0 | yes |
| [Forgotten Realms Wiki](https://forgottenrealms.fandom.com/) | TSR / WotC Forgotten Realms books: codes, ISBNs | CC BY-SA 3.0 | yes |
| [Wookieepedia](https://starwars.fandom.com/) | Star Wars reference and RPG books | CC BY-SA 3.0 | yes |
| [Memory Beta](https://memory-beta.fandom.com/) | Star Trek books, including FASA RPG stock numbers | CC BY-SA 3.0 | yes |

More sources are being added: Wikipedia product lists, Wikidata, ISFDB, Open Library, the
Traveller wiki, Kim's RPG Encyclopedia and more. The full plan, with each source's licence, is in
`SOURCES.md` (coming with the first release). Thank you to every editor of these wikis and indexes.

## What is deliberately NOT in the public release

- **Sources whose owner hasn't allowed republishing.** Some sites are used privately, only to
  help identify books, and never leave the collector's own database. That includes sites with no
  licence (until their owners agree) and sites whose terms forbid reproduction.
- **Anything from BoardGameGeek / RPGGeek**, or sites built on their data.
- **Descriptions, reviews and cover images** from sources that don't licence them. Releases carry
  facts (titles, codes, ISBNs, names, dates, page counts) plus links back to each source page.
- **Nothing about anyone's personal collection.** No file names, paths or checksums.

## Licence

- **Code** (`refdb/`, tests): MIT, see `LICENSE`.
- **Data**: each record keeps its source's licence. Share-alike sources (CC BY-SA, GFDL) keep
  their terms, so reuse their records under the same licence and credit the source as listed
  above. The release notes for each version state exactly which licences apply.

## Running the collector

```bash
pip install -r requirements.txt
python -m refdb collect sarna            # or: all
python -m refdb stats
```

It is deliberately slow and polite: one request per second, Wikimedia `maxlag` honoured, and a
User-Agent that points back to this repository. Raw source text is stored with every record, so
parsing can be improved without fetching again.
