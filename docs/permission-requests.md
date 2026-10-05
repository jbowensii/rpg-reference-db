# Permission requests (drafts for John to send)

Each site below is used privately for matching today. These drafts ask to include its **facts only**
(title, product/stock code, ISBN, publisher, author, year, page count) in the free public dataset,
always credited and linked. Never descriptions, reviews or images. Edit freely before sending.

| Site | Contact | Status |
|---|---|---|
| Wayne's Books RPG Reference | waynesbooks.com contact page | not sent |
| John H. Kim's RPG Encyclopedia | email on darkshire.net (his policy: credit, link, and tell him) | not sent |
| The TSR Archive | black_dougal@yahoo.com | not sent |
| Traveller Wiki | wiki.travellerrpg.com admins | not sent |
| TTRPG Wiki | thettrpgwiki@gmail.com | not sent |
| The Acaeum (optional) | acaeum.com | not sent |
| Steve Jackson Games (optional) | sjgames.com contact | not sent |
| Lexicanum (optional) | lexicanum.com admins | not sent |

---

## General template

**Subject:** May I include your product facts in a free RPG reference dataset?

Hi <name>,

I'm building a free, open reference database of tabletop RPG products: title, product/stock code,
ISBN, publisher, author, year and page count. Anyone cataloguing a game collection can download it.
It lives at https://github.com/jbowensii/rpg-reference-db, and every record credits and links the
site it came from.

<Site> is one of the best sources for <what they cover>, and I'd like to include those **facts**
from your pages, credited to you with a link back to each page. I would not copy your
descriptions, reviews or images. I collected the pages once, slowly, for my own cataloguing.

Would that be OK with you? If you'd rather I didn't publish anything from your site, I'll keep it
out of the public dataset completely. That's no problem, and thank you for the years of work
behind <Site>.

Best regards,
John Bowens

---

## Per-site notes

- **Wayne's Books** (<what they cover> = "out-of-print RPGs from TSR, GDW, FASA, ICE, West End and
  more, with stock numbers and ISBNs"). It's a store's reference site; mention the links back would
  bring readers to his pages.
- **John H. Kim's RPG Encyclopedia.** His site policy already allows reuse with credit, a link and
  a notice, so this is the **notice**: "I'm using fulllist.xml (game, edition, author, year,
  company) in ... with credit to J. Hanju Kim and a link to the encyclopedia." Once sent, set
  `kim` to `publish=True` in `refdb/sources.py`.
- **The TSR Archive** (<what they cover> = "every TSR product line with item codes, formats and
  years").
- **Traveller Wiki** (<what they cover> = "Traveller products from every publisher"). Ask whether
  the RPGBook Cargo data can be republished with attribution.
- **TTRPG Wiki** (<what they cover> = "current game systems with editions, publishers and years").
  The data is a single JSON file; ask about a licence for it.
