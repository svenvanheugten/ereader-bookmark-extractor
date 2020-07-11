import sqlite3
from zipfile import ZipFile
from html.parser import HTMLParser
import argparse
import re
import os


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


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('volume')
    argparser.add_argument('destination')

    args = argparser.parse_args()

    db = sqlite3.connect(os.path.join(args.volume, '.kobo/KoboReader.sqlite'))

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text
                      FROM Bookmark
                      ORDER BY ContentId, DateModified DESC''')

    books_to_bookmarks = {}

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue
        content_id_parts = content_id.split('#', 1)
        book = content_id_parts[0][20:]
        books_to_bookmarks.setdefault(book, []).append((start_container_path, end_container_path, text))

    for book, bookmarks in books_to_bookmarks.items():
        print('Processing {}...'.format(book))
        with \
            ZipFile(os.path.join(args.volume, book)) as book_zip, \
                open(os.path.join(args.destination, os.path.basename(book))[:-5] + '.html', 'w') as output:
            output.write('<meta charset="UTF-8"><style>body { font-family: sans-serif; }</style>')

            for (start_container_path, end_container_path, text) in bookmarks:
                if text is None:
                    continue

                chapter_file, start_container_path_point = start_container_path.split('#', 1)
                _, end_container_path_point = end_container_path.split('#', 1)

                with book_zip.open(chapter_file) as book_chapter:
                    parser = MyHTMLParser(output, start_container_path_point[6:-1],
                                          end_container_path_point[6:-1], text)
                    parser.feed(book_chapter.read().decode('utf-8'))
