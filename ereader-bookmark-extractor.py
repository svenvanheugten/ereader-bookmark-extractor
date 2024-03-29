#!/usr/bin/env python3

import sqlite3
from zipfile import ZipFile, is_zipfile
from html.parser import HTMLParser
from more_itertools import pairwise
from itertools import chain
import spacy.lang.en
import argparse
import sys
import csv
import re
import os


nlp = spacy.lang.en.English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))


class MyHTMLParser(HTMLParser):
    def __init__(self, context, start, end, should_be):
        super().__init__()
        self.__context = context
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
            self.finalize()
        else:
            self.__end_pos = len(self.__scanned_data)

    def finalize(self):
        paragraph = self.__get_paragraph()
        (h_start, h_end) = self.__get_highlight_interval()
        (c_start, c_end) = self.__get_context_interval()
        self.lhs = paragraph[c_start:h_start].lstrip()
        self.highlight = paragraph[h_start:h_end].replace('\n', ' ')
        self.rhs = paragraph[h_end:c_end].rstrip()

    def __get_paragraph(self):
        return self.__scanned_data.decode('utf-8')

    def __get_highlight_interval(self):
        paragraph = self.__get_paragraph()
        start = len(self.__scanned_data[:self.__start_pos].decode('utf-8'))
        end = len(self.__scanned_data[:self.__end_pos].decode('utf-8'))
        highlight = paragraph[start:end]
        assert re.sub(r'\s+', '', highlight) == re.sub(r'\s+', '', self.__should_be)
        start += len(highlight) - len(str.lstrip(highlight))
        end += len(highlight) - len(str.rstrip(highlight))
        if highlight.strip()[-1] in {'.', ',', '?', '!'}:
            end -= 1
        return (start, end)

    def __get_context_interval(self):
        paragraph = self.__get_paragraph()
        if self.__context == 'sentence':
            highlight_interval = self.__get_highlight_interval()
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


class TextOutputWriter:
    def __init__(self, destination):
        self.__destination = destination
        self.__outputs = {}

    def write(self, bookmark_id, book_name, lhs, highlight, rhs):
        output = self.__outputs.get(book_name, None)
        if output is None:
            output = self.__outputs[book_name] = open(os.path.join(self.__destination, book_name + '.txt'), 'w')
        output.write('{}[{}]{}\n\n'.format(lhs, highlight, rhs))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for output in self.__outputs.values():
            output.close()


class HTMLOutputWriter:
    def __init__(self, destination):
        self.__destination = destination
        self.__outputs = {}

    def write(self, bookmark_id, book_name, lhs, highlight, rhs):
        output = self.__outputs.get(book_name, None)
        if output is None:
            output = self.__outputs[book_name] = open(os.path.join(self.__destination, book_name + '.html'), 'w')
            output.write('<meta charset="UTF-8"><style>body { font-family: sans-serif; }</style>')
        output.write('<p>')
        output.write(parser.lhs)
        output.write('<strong><font color="green">')
        output.write(parser.highlight)
        output.write('</font></strong>')
        output.write(parser.rhs)
        output.write('</p><hr/>')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for output in self.__outputs.values():
            output.close()


class CsvOutputWriter:
    def __init__(self, destination):
        self.__output = open(destination, 'w') if destination != '-' else sys.stdout
        self.__csv_writer = csv.DictWriter(self.__output, fieldnames=['ID', 'Book', 'Bookmark'])
        self.__csv_writer.writeheader()

    def write(self, bookmark_id, book_name, lhs, highlight, rhs):
        self.__csv_writer.writerow({
            'ID': bookmark_id,
            'Book': book_name,
            'Bookmark': '{}[{}]{}'.format(lhs, highlight, rhs)
        })

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__output.close()


def get_output_writer(output_format, destination):
    if output_format == 'txt':
        return TextOutputWriter(destination)
    elif output_format == 'html':
        return HTMLOutputWriter(destination)
    elif output_format == 'csv':
        return CsvOutputWriter(destination)


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
    argparser.add_argument('--context', choices=['sentence', 'paragraph'], default='paragraph')
    argparser.add_argument('--output-format', choices=['txt', 'html', 'csv'], default='html')

    args = argparser.parse_args()

    db = sqlite3.connect(os.path.join(args.volume, '.kobo/KoboReader.sqlite'))

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, BookmarkID, StartContainerPath, EndContainerPath, Text
                      FROM Bookmark
                      ORDER BY DateModified DESC''')

    books_to_bookmarks = {}

    for content_id, bookmark_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue
        content_id_parts = content_id.split('#', 1)
        book = content_id_parts[0][len('file:///mnt/onboard/'):]
        books_to_bookmarks.setdefault(book, []).append((bookmark_id, start_container_path, end_container_path, text))

    with get_output_writer(args.output_format, args.destination) as output_writer:
        for book, bookmarks in books_to_bookmarks.items():
            path = os.path.join(args.volume, book)
            if not is_epub(path):
                print('Skipping {} because it is not an epub'.format(book), file=sys.stderr)
                continue
            with ZipFile(path) as book_zip:
                print('Processing {}...'.format(book), file=sys.stderr)
                book_name = os.path.splitext(os.path.basename(book))[0]
                for (bookmark_id, start_container_path, end_container_path, text) in bookmarks:
                    if text is None:
                        continue

                    chapter_file, start_container_path_point = start_container_path.split('#', 1)
                    _, end_container_path_point = end_container_path.split('#', 1)

                    with book_zip.open(chapter_file) as book_chapter:
                        parser = MyHTMLParser(args.context, start_container_path_point[6:-1],
                                              end_container_path_point[6:-1], text)
                        parser.feed(book_chapter.read().decode('utf-8'))
                        output_writer.write(bookmark_id, book_name, parser.lhs, parser.highlight, parser.rhs)
