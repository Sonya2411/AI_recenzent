from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import base64
#from clip import *
from module import *
from openai_ import *
from PIL import Image
import io
from transformers import DetrImageProcessor, DetrForObjectDetection

app = Flask(__name__)
uploaded_files = {}
CORS(app)  # Разрешение CORS для всех запросов

def init_db():
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
        image_ID VARCHAR PRIMARY KEY,
        image_URL VARCHAR,
        name TEXT,
        description TEXT,
        image BLOB NOT NULL,
        detected_objects TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meta (
        description TEXT,
        tags VARCHAR,
        img_quality INTEGER,
        image_ID VARCHAR,
        FOREIGN KEY (image_ID) REFERENCES images (image_ID))
    ''')
    conn.commit()
    conn.close()

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    feedback_score = data.get('feedback')
    suggestion = data.get('suggestion')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                        id INTEGER PRINARY KEY,
                        score INTEGER,
                        suggestion TEXT)''')
    cursor.execute("INSERT INTO feedback (score, suggestion) VALUES (?, ?)", (feedback_score, suggestion,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Feedback received"}), 200

@app.route('/upload', methods=['POST'])
def upload_image():
    # Проверка, что файл был передан в запросе
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    image_file = request.files['file']
    name = os.path.splitext(image_file.filename)[0] # берем только название файла без расширения
    print(name)
    file_name = name
    file_data = image_file.filename
    uploaded_files[file_name] = file_data
    # Проверка, что файл выбран
    if image_file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    # Дополнительная диагностика
    print(f"Received file: {image_file.filename}")
    # Чтение файла в бинарном формате
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM images WHERE name = ?', (name,))
    result = cursor.fetchall()
    # Сохранение изображения в базе данных
    if(result):
        return jsonify({"message": "Файл уже существует"})
    else:
        try:
            image_data = image_file.read()
            conn = sqlite3.connect('images.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO images (name, image) VALUES (?, ?)', (name, image_data))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            return jsonify({"message": f"Database error: {e}"}), 500

    return jsonify({"message": "Image uploaded successfully"}), 200

@app.route('/images', methods=['GET'])
def get_images():
    try:
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        latest_file_name = list(uploaded_files.keys())[-1]
        print(latest_file_name)
        cursor.execute("SELECT image FROM images WHERE name = ?", (latest_file_name,))
        data = cursor.fetchall()
        image_data = data[0][0]
        image = Image.open(io.BytesIO(image_data))
        detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
        detected_objects = detect_objects(image, detr_processor, detr_model)
        print(detected_objects)
        #cursor.execute("UPDATE images SET detected_objects = ? WHERE name = ?", (detect, latest_file_name,))
        cursor.execute("SELECT image_ID FROM images WHERE name = ?", (latest_file_name,))
        data = cursor.fetchall()
        image_id = data[0][0]
        #update_meta_tags(conn, image_id, detected_objects)
        blip_caption = blip_model(image)
        vit_caption = vit_model(image)
        reviews = [blip_caption, vit_caption]
        probs = clip_model(image, reviews)
        max_prob, best_review_idx = probs.max(dim=0)
        best_review = reviews[best_review_idx.item()]
        cursor.execute("UPDATE images SET description = ? WHERE name = ?", (best_review, latest_file_name,))
        conn.commit()
        conn.close()
        conn = sqlite3.connect('images.db')
        cursor = conn.cursor()
        cursor.execute("SELECT image, name, description, detected_objects FROM images WHERE name = ?", (latest_file_name,))
        images = cursor.fetchall()
        #Форматируем данные в список словарей
        image_list = [
           {
            "image": base64.b64encode(row[0]).decode('utf-8'),
            "name": row[1], 
            "description": row[2],
            "detected_objects": row[3]
            }
            for row in images
        ]
        print("xui")
        cursor.execute("SELECT image, description, detected_objects FROM images WHERE name = ?", (latest_file_name,))
        data = cursor.fetchall()
        image1 = "https://live.staticflickr.com/65535/50738772673_7466e1d716_m.jpg"
        description1 = "a cat sitting on the grass"
        for image, description, detection_objects in data:
            review = generate_review(image1, description1, detection_objects, 0)
        add_list = [
            {
                "rezenz": review
            }
        ]
        for i, image2 in enumerate(image_list):
            image2.update(add_list[i])
        print(image_list)
        return jsonify(image_list), 200
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"message": "Error fetching data"}), 500
    except Exception as e:
        print(f"Unecpected error: {e}")
        return jsonify({"message": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    init_db()  # Создание таблицы перед запуском сервера
    app.run(port=5000)
