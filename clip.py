from transformers import CLIPModel, CLIPProcessor, BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

def clip_model(image, text):
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    with torch.no_grad():
        inputs = processor(text = text, images = image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)
    return probs[0]
    
def blip_model(image):
    text = []
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    # Перенос модели на cuda ядра, если это возможно
    print(torch.cuda.is_available())
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    temperature = [0.2, 1.0, 1.5]
    for i in temperature:
        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_length=50, temperature=i, do_sample=True, top_k=50, top_p=0.9)
        description = processor.decode(out[0], skip_special_tokens=True)
        text.append(description)
    #print(text)
    return text