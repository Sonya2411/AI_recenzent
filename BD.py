import sqlite3
import requests

con = sqlite3.connect('images_AI.db')
cursor = con.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    image_ID VARCHAR PRIMARY KEY,
    image_URL VARCHAR,
    image BLOB NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS meta (
    description TEXT,
    tags VARCHAR,
    img_quality INTEGER,
    image_ID VARCHAR,
    FOREIGN KEY (image_ID) REFERENCES images (image_ID)
)
''')

def download_images_and_save(api_url, api_key, search_term, db_cursor, db_connection):
    params = {
        'method': 'flickr.photos.search',
        'api_key': api_key,
        'text': search_term,
        'format': 'json',
        'privacy_filter': 1,
        'content_types': 0,
        'nojsoncallback': 1,
        'extras': 'url_s, tags',
        'per_page': 100,
        'sort': 'relevance'
    }

    response = requests.get(api_url, params=params)
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        for photo in data['photos']['photo']:
            image_id = photo['id']
            image_url = photo.get('url_s')
            image_tags = photo.get('tags', '')
            tags_list = image_tags.split()
            tags_string = ', '.join(tags_list)
            if image_url:
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    image_blob = image_response.content
                    db_cursor.execute("INSERT INTO images (image_ID, image_URL, image) VALUES (?, ?, ?)",
                                      (image_id, image_url, image_blob))
                    db_connection.commit()
                    db_cursor.execute("INSERT INTO meta (tags, image_ID) VALUES (?, ?)",
                                      (tags_string, image_id))
                    db_connection.commit()
                else:
                    print("Ошибка при загрузке изображения:", image_response.status_code)
            else:
                print("URL изображения отсутствует для ID:", image_id)
    else:
        print("Ошибка при получении метаданных:", response.status_code)

api_key = "7cd65095e88a635e40f3a0c11fd99743"
api_url = "https://api.flickr.com/services/rest/"
search_terms = ["Кошки животные", "Собаки играют", "Мотоциклы", "Архитектура", "Чудеса света"]
for term in search_terms:
    download_images_and_save(api_url, api_key, term, cursor, con)

con.commit()
con.close()
