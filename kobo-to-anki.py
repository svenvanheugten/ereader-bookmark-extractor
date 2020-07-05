import sqlite3
from zipfile import ZipFile
from html.parser import HTMLParser
from termcolor import colored


VOLUME = '/Volumes/KOBOeReader/'


class MyHTMLParser(HTMLParser):
    def __init__(self, look_for, end, should_be):
        super().__init__()
        self.__location = []
        self.__look_for = look_for
        self.__end = end
        self.__should_be = should_be

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
        if self.__look_for.startswith(anchor):
            if not self.__end.startswith(anchor):
                print(':(')
                return
            begin = int(self.__look_for[len(anchor):])
            end = int(self.__end[len(anchor):])
            word = data.encode('utf-8')[begin:end].decode('utf-8')
            assert word == self.__should_be
            print(data.encode('utf-8')[:begin].decode('utf-8'), end='')
            print(colored(word, 'green'), end='')
            print(data.encode('utf-8')[end:].decode('utf-8'))
            print()


if __name__ == '__main__':
    db = sqlite3.connect(VOLUME + '.kobo/KoboReader.sqlite')

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text FROM Bookmark''')

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
        except:
            pass
