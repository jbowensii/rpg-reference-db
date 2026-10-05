-- Game-related publications from an ISFDB MySQL backup (CC BY 4.0), one row per publication.
-- Run inside the temporary MariaDB that holds the dump:
--   mariadb -B isfdb < isfdb_export.sql > isfdb_game_pubs.tsv
-- "Game-related" = published by a game company, or containing a title in a game-world series.
SET SESSION group_concat_max_len = 4000;
SELECT p.pub_id, p.pub_title, p.pub_tag, p.pub_year, pb.publisher_name, p.pub_pages, p.pub_ptype, p.pub_ctype,
       p.pub_isbn, p.pub_catalog, p.pub_price, ps.pub_series_name,
       (SELECT GROUP_CONCAT(DISTINCT a.author_canonical ORDER BY a.author_canonical SEPARATOR '; ')
          FROM pub_authors pa JOIN authors a ON a.author_id = pa.author_id WHERE pa.pub_id = p.pub_id) AS authors,
       (SELECT GROUP_CONCAT(DISTINCT s.series_title SEPARATOR '; ')
          FROM pub_content pc JOIN titles t ON t.title_id = pc.title_id JOIN series s ON s.series_id = t.series_id
         WHERE pc.pub_id = p.pub_id) AS title_series
  FROM pubs p
  LEFT JOIN publishers pb ON pb.publisher_id = p.publisher_id
  LEFT JOIN pub_series ps ON ps.pub_series_id = p.pub_series_id
 WHERE pb.publisher_name REGEXP 'Black Library|BL Publishing|^TSR|Wizards of the Coast|FASA|Games Workshop|Chaosium|White Wolf|Steve Jackson Games|West End Games|Iron Crown|Palladium Books|Catalyst Game|Paizo|Game Designers|Mongoose Publishing|Fantasy Flight|Pelgrane|Flying Buffalo|Green Ronin|Privateer Press|Pinnacle Entertainment|Evil Hat|Arc Dream|Onyx Path|Cubicle 7|Modiphius|Free League|Kobold Press|Judges Guild|Mayfair Games|R\\. Talsorian|Hero Games|Eden Studios|Margaret Weis Productions|Decipher|Last Unicorn|Wizkids|Aconyte'
    OR ps.pub_series_name REGEXP 'Warhammer|Horus Heresy|Forgotten Realms|Dragonlance|Greyhawk|Ravenloft|Eberron|Dark Sun|Planescape|Spelljammer|Mystara|Dungeons|BattleTech|MechWarrior|Shadowrun|Earthdawn|Star Trek|Star Wars|Fighting Fantasy|Lone Wolf|Pathfinder|Iron Kingdoms|Magic: The Gathering|World of Darkness|Vampire|Werewolf|Deadlands|Traveller|Call of Cthulhu|Arkham Horror|Endless Quest|Gamma World|Paranoia|Exalted|Legend of the Five Rings|Mage: The'
    OR EXISTS (SELECT 1 FROM pub_content pc JOIN titles t ON t.title_id = pc.title_id JOIN series s ON s.series_id = t.series_id
                WHERE pc.pub_id = p.pub_id
                  AND s.series_title REGEXP 'Warhammer|Horus Heresy|Forgotten Realms|Dragonlance|Greyhawk|Ravenloft|Eberron|Dark Sun|Planescape|Spelljammer|Mystara|BattleTech|MechWarrior|Shadowrun|Earthdawn|Star Trek|Star Wars|Fighting Fantasy|Lone Wolf|Pathfinder|Iron Kingdoms|Magic: The Gathering|World of Darkness|Deadlands|Call of Cthulhu|Arkham Horror|Endless Quest|Gamma World|Exalted|Legend of the Five Rings|Gaunt''s Ghosts|Ciaphas Cain|Eisenhorn|Ravenor|Space Marine Battles|Drizzt|Elminster|Dragonlance Chronicles');
