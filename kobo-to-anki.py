import sqlite3
from zipfile import ZipFile
from bs4 import BeautifulSoup


VOLUME = './KOBOeReader/'


if __name__ == '__main__':
    db = sqlite3.connect(VOLUME + '.kobo/KoboReader.sqlite')

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text FROM Bookmark''')

    for content_id, start_container_path, end_container_path, text in cursor:
        if not content_id.startswith('file:///mnt/onboard/'):
            continue

        book_file, _ = content_id.split('#', 1)
        chapter_file, start_container_path_point = start_container_path.split('#', 1)

        with ZipFile(VOLUME + book_file[20:]) as book_zip:
            with book_zip.open(chapter_file) as book_chapter:
                chapter_text = book_chapter.read()
                soup = BeautifulSoup(chapter_text, 'html.parser')
                start_container_path_point_split = start_container_path_point.split('/')
                paragraphs = [p.contents for p in soup.find_all('p')]
                paragraph_index = int(start_container_path_point_split[4]) // 2 + 1
                print('{} in {}'.format(text, paragraphs[paragraph_index]))
