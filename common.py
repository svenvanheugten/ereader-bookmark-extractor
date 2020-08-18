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
        self.__location = []
        self.__start_epubcti = start
        self.__end_epubcti = end
        self.__should_be = should_be
        self.__scanning = False
        self.__scanned_data = b''
        self.__start_pos = -1
        self.__end_pos = -1

    def handle_starttag(self, tag, attrs):
        if len(self.__location) > 0:
            self.__location[-1] += 1
        self.__location.append(0)

    def handle_endtag(self, tag):
        self.__location.pop()

    def handle_data(self, data):
        if len(self.__location) > 0:
            self.__location[-1] += 1
        anchor = '/1/' + '/'.join([str(x) for x in self.__location]) + ':'
        if self.__start_epubcti.startswith(anchor):
            self.__scanning = True
            self.__start_pos = int(self.__start_epubcti[len(anchor):])
        if self.__scanning:
            self.__scanned_data += data.encode('utf-8')
        if self.__end_epubcti.startswith(anchor):
            self.__scanning = False
            self.__end_pos += int(self.__end_epubcti[len(anchor):])
            fragment = self.__scanned_data[self.__start_pos:self.__end_pos].decode('utf-8')
            assert re.sub(r'\s+', '', fragment) == re.sub(r'\s+', '', self.__should_be)
            self.__write_to.write('<p>')
            self.__write_to.write(self.__scanned_data[:self.__start_pos].decode('utf-8'))
            self.__write_to.write('<strong><font color="green">')
            self.__write_to.write(fragment)
            self.__write_to.write('</font></strong>')
            self.__write_to.write(self.__scanned_data[self.__end_pos:].decode('utf-8'))
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
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text
                      FROM Bookmark
                      ORDER BY DateModified DESC''')

    books_to_bookmarks = {}

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('/mnt/onboard/'):
            continue
        content_id_parts = content_id.split('#', 1)
        book = content_id_parts[0][len('/mnt/onboard/'):]
        books_to_bookmarks.setdefault(book, []).append((start_container_path, end_container_path, text))

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

                for (start_container_path, end_container_path, text) in bookmarks:
                    try:
                        if text is None:
                            continue

                        chapter_file, start_container_path_point = start_container_path.split('!!', 1)
                        _, end_container_path_point = end_container_path.split('!!', 1)

                        with book_zip.open(chapter_file) as book_chapter:
                            parser = MyHTMLParser(output, start_container_path_point[6:-1],
                                                  end_container_path_point[6:-1], text)
                            parser.feed(book_chapter.read().decode('utf-8'))
                    except:  # noqa: E722
                        logging.exception('Unable to parse {}'.format((path, start_container_path,
                                                                       end_container_path, text)))

    print('Done.')
