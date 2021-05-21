#!/usr/bin/env python3

import re
import csv
import os.path
import genanki


DB_LOCATION = os.path.expanduser('~/flashcard-db.csv')


if __name__ == '__main__':
    deck = genanki.Deck(2059400110, 'Default')

    with open(DB_LOCATION, 'r') as db_file:
        reader = csv.DictReader(db_file)
        db = list(reader)

    for row in db:
        bookmark = re.search(r'(.*?)\[(.*?)\](.*)', row['Bookmark'])
        deck.add_note(genanki.Note(
            guid=row['ID'],
            model=genanki.CLOZE_MODEL,
            fields=['{}{{{{c1::{}::{}}}}}{}'.format(
                bookmark.group(1),
                bookmark.group(2),
                row['Translation'],
                bookmark.group(3)
            )]
        ))

    genanki.Package(deck).write_to_file('output.apkg')
