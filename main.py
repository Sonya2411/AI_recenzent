from clip import *
import sqlite3
import base64
from PIL import Image
import io
import torch

con = sqlite3.connect('images_AI.db')
cursor = con.cursor()
cursor.execute("SELECT image_ID FROM images")
images = cursor.fetchall()
c = 1
for i in images:
    cursor.execute("SELECT image FROM images WHERE image_ID = ?", [i[0]])
    data = cursor.fetchall()
    image_data = data[0][0]
    image = Image.open(io.BytesIO(image_data))
    rec = []
    rec = blip_model(image)
    probs = clip_model(image, rec)
    probs = probs.tolist()
    max_value = max(probs)
    max_index = probs.index(max_value)
    description = rec[max_index]
    cursor.execute("UPDATE meta SET description = ? WHERE image_id = ?", [description, i[0]])
    con.commit()
    print(c)
    c = c+1
    #print(probs)

con.close()