import os
import csv
import sys
import argparse
import os.path
import tempfile


DB_LOCATION = os.path.expanduser('~/flashcard-db.csv')


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('source')

    args = argparser.parse_args()

    if os.path.isfile(DB_LOCATION):
        with open(DB_LOCATION, 'r') as db_file:
            reader = csv.DictReader(db_file)
            db = list(reader)
    else:
        db = []

    with open(args.source, 'r') if args.source != '-' else sys.stdin as source:
        reader = csv.DictReader(source)
        for row in reader:
            if not any(r['ID'] == row['ID'] for r in db):
                db.append(row)

    temp_fd, temp_filename = tempfile.mkstemp()

    try:
        with os.fdopen(temp_fd, 'w') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['ID', 'Book', 'Bookmark', 'Translation'])
            writer.writeheader()
            for row in db:
                writer.writerow(row)
        os.replace(temp_filename, DB_LOCATION)
    except:  # noqa: E722
        os.remove(temp_filename)
