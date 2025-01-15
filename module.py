TF_ENABLE_ONEDNN_OPTS=0
import io
import sqlite3
import cv2
import numpy as np
from transformers import (DetrImageProcessor, DetrForObjectDetection, 
                          ViTImageProcessor, ViTForImageClassification, 
                          VisionEncoderDecoderModel, AutoTokenizer, 
                          CLIPModel, CLIPProcessor, BlipProcessor, BlipForConditionalGeneration)
import torch
from PIL import Image
from io import BytesIO

def connect_to_db(db_name):
    return sqlite3.connect(db_name)

def blob_to_image(blob_data):
    image_array = np.frombuffer(blob_data, dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

def detect_objects(image, processor, model):
    image_pil = image
    inputs = processor(images=image_pil, return_tensors="pt")
    outputs = model(**inputs)
    results = processor.post_process_object_detection(outputs, target_sizes=[image_pil.size], threshold=0.75)[0]
    detected_objects = [model.config.id2label[label.item()] for label in results["labels"]]
    return detected_objects

def update_meta_tags(conn, image_id, detected_objects):
    meta_tags = ", ".join(detected_objects)
    cursor = conn.cursor()
    cursor.execute("UPDATE meta SET meta_tags = ? WHERE image_ID = ?", (meta_tags, image_id))
    conn.commit()

def clip_model(image, text):
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    inputs = processor(text=text, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)
    return probs[0]

def vit_model(image):
    model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
    processor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
    tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(inputs.pixel_values)
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return text

def blip_model(image):
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    text = processor.decode(out[0], skip_special_tokens=True)
    return text

def get_image(conn, image_id):
    cursor = conn.cursor()
    cursor.execute("SELECT image FROM images WHERE image_ID = ?", (image_id,))
    result = cursor.fetchone()
    if result:
        image_blob = result[0]
        return blob_to_image(image_blob)  # Преобразование сразу в OpenCV формат
    else:
        raise ValueError(f"Изображение с image_ID={image_id} не найдено в базе данных.")

def classify_image(image):
    feature_extractor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
    model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
    inputs = feature_extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    labels = model.config.id2label
    return labels[predicted_class_idx]

def main():
    conn = connect_to_db("images_AI.db")
    # Ввод ID изображения
    image_id = input("Введите ID изображения: ").strip()
    
    # Получение изображения
    image = get_image(conn, image_id)

    # DETR model for object detection
    detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
    detected_objects = detect_objects(image, detr_processor, detr_model)
    print(f"Обнаруженные объекты: {detected_objects}")

    # Обновление метатегов
    update_meta_tags(conn, image_id, detected_objects)
    print(f"Метатеги обновлены для изображения {image_id}.")

    # Генерация описаний
    blip_caption = blip_model(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
    vit_caption = vit_model(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
    reviews = [blip_caption, vit_caption]
    print(f"Составленные описания: {reviews}")

    # Модель CLIP для выбора лучшего описания
    probs = clip_model(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), reviews)
    max_prob, best_review_idx = probs.max(dim=0)
    best_review = reviews[best_review_idx.item()]
    print(f"Лучшее описание: {best_review} с вероятностью {max_prob.item()}.")

    # Сохранение лучшего описания
    cursor = conn.cursor()
    cursor.execute("UPDATE meta SET description = ? WHERE image_ID = ?", (best_review, image_id))
    conn.commit()

    # Классификация изображения
    predicted_class = classify_image(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
    print(f"Предсказанный класс: {predicted_class}")

    # Обновление класса изображения
    cursor.execute("UPDATE meta SET tags = ? WHERE image_ID = ?", (predicted_class, image_id))
    conn.commit()
    print(f"Класс изображения {image_id} обновлен.")

    conn.close()

if __name__ == "__main__":
    main()
