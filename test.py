import requests
from PIL import Image
from io import BytesIO
from transformers import BlipProcessor, BlipForConditionalGeneration

# Загрузить изображение по URL
def download_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Проверка на успешный ответ
        image = Image.open(BytesIO(response.content))
        return image
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке изображения: {e}")
        return None
    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")
        return None

# Генерация рецензии на изображение
def generate_review(image_url):
    # Инициализация модели и процессора
    processor = BlipProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")
    
    # Загрузить изображение
    image = download_image(image_url)
    if image is None:
        return "Не удалось загрузить изображение."
    
    # Преобразование изображения для модели
    inputs = processor(images=image, return_tensors="pt")
    
    # Генерация текста (рецензии)
    try:
        out = model.generate(**inputs, max_length=200)
        review = processor.decode(out[0], skip_special_tokens=True)
        return review
    except Exception as e:
        return f"Ошибка при генерации рецензии: {e}"

# Пример использования
image_url = "https://live.staticflickr.com/65535/50738772673_7466e1d716_m.jpg"  # замените на ваш URL изображения
review = generate_review(image_url)
print("Рецензия на изображение:")
print(review)