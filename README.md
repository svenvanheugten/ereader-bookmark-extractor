ereader-bookmark-extractor
==========================
Run
---
Run for Kobo devices:

```bash
python3 ereader-bookmark-extractor.py /Volumes/KOBOeReader .
```

Build
-----
Build stand-alone app for Mac:

```bash
python3 setup.py py2app
```

Examples
--------
```bash
python3 ereader-bookmark-extractor.py /Volumes/KOBOeReader - --context sentence --output-format csv | python3 upsert-to-csv-db.py -
```