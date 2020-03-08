import sqlite3

if __name__ == '__main__':
    db = sqlite3.connect('/Volumes/KOBOeReader/.kobo/KoboReader.sqlite')

    cursor = db.cursor()
    cursor.execute('''SELECT ContentID, StartContainerPath, EndContainerPath, Text FROM Bookmark''')

    for content_id, start_container_path, end_container_path, text in cursor:
        print(text)
