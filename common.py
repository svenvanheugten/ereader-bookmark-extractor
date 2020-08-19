import sqlite3
from zipfile import ZipFile, is_zipfile
from html.parser import HTMLParser
import re
import os
import logging


class MyHTMLParser(HTMLParser):
    def __init__(self, write_to, start, end, should_be):
        super().__init__()
        self.__write_to = write_to
        self.__location = None
        self.__start = start
        self.__end = end
        self.__should_be = should_be
        self.__scanning = False
        self.__scanned_data = b''
        self.__start_pos = -1
        self.__end_pos = -1

    def handle_starttag(self, tag, attrs):
        if tag == 'span' and ('class', 'koboSpan') in attrs:
            id_attr = [a[1] for a in attrs if a[0] == 'id'][0]
            self.__location = '{}#{}'.format(tag, id_attr)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.__location = None

    def handle_data(self, data):
        if self.__location == self.__start[0]:
            self.__scanning = True
            self.__start_pos = self.__start[1]
        if self.__scanning:
            self.__scanned_data += data.encode('utf-8')
        if self.__location == self.__end[0]:
            self.__scanning = False
            self.__end_pos += self.__end[1]
            fragment = self.__scanned_data.decode('utf-8')[self.__start_pos:self.__end_pos]
            assert re.sub(r'\s+', '', fragment) == re.sub(r'\s+', '', self.__should_be), \
                '"{}"[{}:{}] != {}'.format(self.__scanned_data.decode('utf-8'), self.__start_pos, self.__end_pos, self.__should_be)
            self.__write_to.write('<p>')
            self.__write_to.write(self.__scanned_data.decode('utf-8')[:self.__start_pos])
            self.__write_to.write('<strong><font color="green">')
            self.__write_to.write(fragment)
            self.__write_to.write('</font></strong>')
            self.__write_to.write(self.__scanned_data.decode('utf-8')[self.__end_pos:])
            self.__write_to.write('</p><hr/>')
        else:
            self.__end_pos = len(self.__scanned_data)


def is_epub(path):
    if not is_zipfile(path):
        return False
    with ZipFile(path) as zipfile:
        with zipfile.open('mimetype') as f:
            return f.read() == b'application/epub+zip'


def extract(volume, destination):
    db = sqlite3.connect(os.path.join(volume, '.kobo/KoboReader.sqlite'))

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, StartOffset, EndContainerPath, EndOffset, Text
                      FROM Bookmark
                      ORDER BY DateModified DESC''')

    books_to_bookmarks = {}

    for content_id, start_container_path, start_offset, end_container_path, end_offset, text in cursor:
        if not content_id.startswith('/mnt/onboard/'):
            continue
        content_id_parts = content_id.split('!!', 1)
        book = content_id_parts[0][len('/mnt/onboard/'):]
        chapter_file_parts = content_id_parts[1].split('#', 1)
        chapter_file = chapter_file_parts[0]
        books_to_bookmarks.setdefault(book, []).append((chapter_file, start_container_path, start_offset, end_container_path, end_offset, text))

    for book, bookmarks in books_to_bookmarks.items():
        path = os.path.join(volume, book)
        if not is_epub(path):
            print('Skipping {} because it is not an epub'.format(book))
            continue
        with ZipFile(path) as book_zip:
            print('Processing {}...'.format(book))
            output_path = os.path.join(destination, os.path.splitext(os.path.basename(book))[0] + '.html')
            with open(output_path, 'w') as output:
                output.write('<meta charset="UTF-8"><style>body { font-family: sans-serif; }</style>')

                for (chapter_file, start_container_path, start_offset, end_container_path, end_offset, text) in bookmarks:
                    try:
                        if text is None:
                            continue

                        with book_zip.open(chapter_file) as book_chapter:
                            parser = MyHTMLParser(output, (start_container_path.replace('\\', ''), int(start_offset)), (end_container_path.replace('\\', ''), int(end_offset)), text)
                            parser.feed(book_chapter.read().decode('utf-8'))
                    except:  # noqa: E722
                        logging.exception('Unable to parse {}'.format((path, start_container_path, start_offset,
                                                                       end_container_path, end_offset, text)))

    print('Done.')
