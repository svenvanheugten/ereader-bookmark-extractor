import sqlite3
from zipfile import ZipFile
from html.parser import HTMLParser
from termcolor import colored
import re


VOLUME = '/Volumes/KOBOeReader/'


class MyHTMLParser(HTMLParser):
    def __init__(self, start, end, should_be):
        super().__init__()
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
        else:
            self.__end_pos = len(self.__scanned_data)


if __name__ == '__main__':
    db = sqlite3.connect(VOLUME + '.kobo/KoboReader.sqlite')

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text FROM Bookmark ORDER BY DateModified DESC''')

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue

        book_file, _ = content_id.split('#', 1)
        chapter_file, start_container_path_point = start_container_path.split('#', 1)
        _, end_container_path_point = end_container_path.split('#', 1)

        try:
            with ZipFile(VOLUME + book_file[20:]) as book_zip:
                with book_zip.open(chapter_file) as book_chapter:
                    parser = MyHTMLParser(start_container_path_point[6:-1], end_container_path_point[6:-1], text)
                    parser.feed(book_chapter.read().decode('utf-8'))
        except KeyError:
            pass