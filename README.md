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
```bash
./ereader-bookmark-extractor.py /Volumes/KOBOeReader - --context sentence --output-format csv | ./upsert-to-csv-db.py -
```
