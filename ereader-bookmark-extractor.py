import sqlite3
from zipfile import ZipFile, is_zipfile
from html.parser import HTMLParser
from more_itertools import pairwise
from itertools import chain
import spacy.lang.en
import argparse
import re
import os


nlp = spacy.lang.en.English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))


class MyHTMLParser(HTMLParser):
    def __init__(self, context, write_to, start, end, should_be):
        super().__init__()
        self.__context = context
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
            self.write()
        else:
            self.__end_pos = len(self.__scanned_data)

    def write(self):
        paragraph = self.get_paragraph()
        (h_start, h_end) = self.get_highlight_interval()
        (c_start, c_end) = self.get_context_interval()
        assert re.sub(r'\s+', '', paragraph[h_start:h_end]) == re.sub(r'\s+', '', self.__should_be)
        self.__write_to.write('<p>')
        self.__write_to.write(paragraph[c_start:h_start])
        self.__write_to.write('<strong><font color="green">')
        self.__write_to.write(paragraph[h_start:h_end])
        self.__write_to.write('</font></strong>')
        self.__write_to.write(paragraph[h_end:c_end])
        self.__write_to.write('</p><hr/>')

    def get_paragraph(self):
        return self.__scanned_data.decode('utf-8')

    def get_highlight_interval(self):
        start = len(self.__scanned_data[:self.__start_pos].decode('utf-8'))
        end = len(self.__scanned_data[:self.__end_pos].decode('utf-8'))
        return (start, end)

    def get_context_interval(self):
        paragraph = self.get_paragraph()
        if self.__context == 'sentence':
            highlight_interval = self.get_highlight_interval()
            sentences = list(nlp(paragraph).sents)
            sentence_indexes = chain(map(lambda sentence: sentence[0].idx, sentences), [len(paragraph)])
            sentence_intervals = pairwise(sentence_indexes)
            surrounding_sentence_intervals = list(filter(
                lambda i: highlight_interval[0] >= i[0] and highlight_interval[0] < i[1],
                sentence_intervals
            ))
            return (surrounding_sentence_intervals[0][0], surrounding_sentence_intervals[-1][1])
        elif self.__context == 'paragraph':
            return (0, len(paragraph))


def is_epub(path):
    if not is_zipfile(path):
        return False
    with ZipFile(path) as zipfile:
        with zipfile.open('mimetype') as f:
            return f.read() == b'application/epub+zip'


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('volume')
    argparser.add_argument('destination')
    argparser.add_argument('--context', choices=['sentence', 'paragraph'], required=True)

    args = argparser.parse_args()

    db = sqlite3.connect(os.path.join(args.volume, '.kobo/KoboReader.sqlite'))

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text
                      FROM Bookmark
                      ORDER BY DateModified DESC''')

    books_to_bookmarks = {}

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue
        content_id_parts = content_id.split('#', 1)
        book = content_id_parts[0][len('file:///mnt/onboard/'):]
        books_to_bookmarks.setdefault(book, []).append((start_container_path, end_container_path, text))

    for book, bookmarks in books_to_bookmarks.items():
        path = os.path.join(args.volume, book)
        if not is_epub(path):
            print('Skipping {} because it is not an epub'.format(book))
            continue
        with ZipFile(path) as book_zip:
            print('Processing {}...'.format(book))
            output_path = os.path.join(args.destination, os.path.splitext(os.path.basename(book))[0] + '.html')
            with open(output_path, 'w') as output:
                output.write('<meta charset="UTF-8"><style>body { font-family: sans-serif; }</style>')

                for (start_container_path, end_container_path, text) in bookmarks:
                    if text is None:
                        continue

                    chapter_file, start_container_path_point = start_container_path.split('#', 1)
                    _, end_container_path_point = end_container_path.split('#', 1)

                    with book_zip.open(chapter_file) as book_chapter:
                        parser = MyHTMLParser(args.context, output, start_container_path_point[6:-1],
                                              end_container_path_point[6:-1], text)
                        parser.feed(book_chapter.read().decode('utf-8'))
