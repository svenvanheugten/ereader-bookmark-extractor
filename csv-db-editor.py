#!/usr/bin/env python3

import re
import csv
import os.path
import urwid


DB_LOCATION = os.path.expanduser('~/flashcard-db.csv')


if __name__ == '__main__':
    with open(DB_LOCATION, 'r') as db_file:
        reader = csv.DictReader(db_file)
        db = list(reader)

    bookmarks = [
        {**row, 'Bookmark': re.search(r'(.*?)\[(.*?)\](.*)', row['Bookmark'])}
        for row in db
    ]

    palette = [
        ('context', 'white', 'default'),
        ('highlight', 'dark green', 'default')
    ]
    content = urwid.SimpleListWalker([
        urwid.Edit(
            [
                ('context', ('\n' if index != 0 else '') + row['Bookmark'].group(1)),
                ('highlight', row['Bookmark'].group(2)),
                ('context', row['Bookmark'].group(3) + '\n')
            ],
            multiline=True,
            edit_text=row['Translation']
        )
        for index, row in enumerate(bookmarks)
    ])
    listbox = urwid.ListBox(content)

    loop = urwid.MainLoop(listbox, palette)
    loop.run()
