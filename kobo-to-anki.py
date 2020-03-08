import sqlite3
from zipfile import ZipFile


VOLUME = '/Volumes/KOBOeReader/'


if __name__ == '__main__':
    db = sqlite3.connect(VOLUME + '.kobo/KoboReader.sqlite')

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text FROM Bookmark''')

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue

        print(text)

        book_file, suffix = content_id.split('#', 1)
        _, xhtml_file = suffix.split(')', 1)

        if '#' in xhtml_file:
            xhtml_file = xhtml_file.split('#')[0]

        with ZipFile(VOLUME + book_file[20:]) as book_zip:
            with book_zip.open(xhtml_file) as book_chapter:
                chapter_text = book_chapter.read()

