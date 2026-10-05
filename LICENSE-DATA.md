# Data licence

The **code** in this repository (`refdb/`, `tests/`) is under the MIT License: see `LICENSE`.

The **data** (the released database and CSV files) is licensed under the
**Creative Commons Attribution-ShareAlike 4.0 International licence (CC BY-SA 4.0)**:
https://creativecommons.org/licenses/by-sa/4.0/

You may share and adapt it, for any purpose, as long as you:

1. **Give credit**: name this dataset ("RPG Reference DB, https://github.com/jbowensii/rpg-reference-db")
   and keep the source credits in `CREDITS.md` (every record also links to its source page).
2. **Share alike**: release your adapted data under CC BY-SA 4.0 (or a compatible licence).

## Why CC BY-SA and not MIT for the data

The data comes from sources with their own licences, and the release has to respect all of them:

| Source licence | Sources | How it fits |
|---|---|---|
| CC0 (public domain) | Wikidata, Open Library | No conditions; fits inside CC BY-SA |
| CC BY 4.0 | ISFDB | Needs credit; fits inside CC BY-SA |
| CC BY-SA 3.0 / 4.0 | Wikipedia, Fandom wikis (White Wolf, Forgotten Realms, Wookieepedia, Memory Beta) | Requires share-alike, so the combined data must be CC BY-SA |
| GNU FDL 1.2 | Sarna.net BattleTechWiki | See the exception below |

A permissive licence such as MIT or CC BY would drop the share-alike condition the wiki sources
require, so it would not be allowed.

## Exception: Sarna.net (GNU FDL 1.2)

Values taken from the Sarna.net BattleTechWiki remain under the **GNU Free Documentation License
1.2**: https://www.gnu.org/licenses/old-licenses/fdl-1.2.html. You can identify them through each
product's `sources` and `provenance` columns. Most of them are facts (product codes, ISBNs, page
counts, years), but the FDL terms apply when you reuse them.

## Facts and links

Records hold bibliographic facts (titles, codes, ISBNs, names, dates, page counts) and links back
to the source pages. No descriptions, reviews or images are copied from sources that don't licence
them, and sources whose owners haven't agreed to republication are left out of the release
entirely. They are listed in `CREDITS.md` with thanks.
