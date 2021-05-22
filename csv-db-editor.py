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

    bookmarks = [re.search(r'(.*?)\[(.*?)\](.*)', row['Bookmark']) for row in db]

    palette = [
        ('context', 'white', 'default'),
        ('highlight', 'dark green', 'default')
    ]
    content = urwid.SimpleListWalker([
        urwid.Edit([
            ('context', '\n' + bookmark.group(1)),
            ('highlight', bookmark.group(2)),
            ('context', bookmark.group(3) + '\n'),
        ])
        for bookmark in bookmarks
    ])
    listbox = urwid.ListBox(content)

    def update_on_cr(key):
        if key == 'enter':
            focus_widget, position = listbox.get_focus()
            listbox.set_focus(position + 1)

    loop = urwid.MainLoop(listbox, palette, unhandled_input=update_on_cr)
    loop.run()
