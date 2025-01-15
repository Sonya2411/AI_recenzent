import sqlite3
import openai
import time

openai.api_key = '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'  # Замените на ваш API ключ
# Функция для подключения к базе данных SQLite
def connect_to_db(db_name='images_AI.db'):
    return sqlite3.connect(db_name)


# Функция для получения фотографий и их метаданных
def fetch_images_and_meta(connection):
    cursor = connection.cursor()
    cursor.execute('''SELECT i.image_id, i.image_URL, m.description, m.tags, m.img_quality 
                      FROM images i 
                      JOIN meta m ON i.image_id = m.image_id''')

    return cursor.fetchall()


# Функция для генерации рецензии на фотографию
def generate_review(image_url, description, tags, img_quality):
    prompt = (f"Напиши рецензию на фотографию по следующему описанию:\n"
              f"URL фотографии: {image_url}\n"
              f"Описание: {description}\n"
              f"Теги: {tags}\n"
              f"Качество изображения: {img_quality}/10\n\n"
              f"Рецензия:")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response['choices'][0]['message']['content']


# Главная функция
def main():
    # Подключаемся к базе данных
    connection = connect_to_db()

    # Получаем фотографии и их метаданные
    images_meta = fetch_images_and_meta(connection)

    reviews = []

    for image_id, image_url, description, tags, img_quality in images_meta:
        review = generate_review(image_url, description, tags, img_quality)
        print(f"Рецензия на фото:\n{review}")
        reviews.append((image_id, review))
        time.sleep(20)

    # Закрываем соединение с БД
    connection.close()

    # Выводим сгенерированные рецензии
    # Генерация рецензии
    # Вывод рецензии
    print(f"Рецензия на фото:\n{review}")


if __name__ == '__main__':
    main()