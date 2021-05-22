ereader-bookmark-extractor
==========================
Run
---
Run for Kobo devices:

```bash
./ereader-bookmark-extractor.py /Volumes/KOBOeReader .
```

Build
-----
Build stand-alone app for Mac:

```bash
python3 setup.py py2app
```

Examples
--------
Upsert all bookmarks to the DB:

```bash
./ereader-bookmark-extractor.py /Volumes/KOBOeReader - --context sentence --output-format csv | ./upsert-to-csv-db.py -
```

Edit the DB:

```bash
./csv-deb-editor.py
```

Convert to flashcards:

```bash
./csv-db-to-anki-deck.py
```