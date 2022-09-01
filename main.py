from string import ascii_lowercase
from random import choice, randint, random
from datetime import date
import cv2
import numpy as np

import os
import shutil

from io import BytesIO
from PIL import Image
import base64

from detect import *

model_weights_dir= 'model_weights/best.pt'
temp_save_dir= 'temp_save_dir'

if not os.path.isdir(temp_save_dir):
    os.mkdir(temp_save_dir)

save_image_format= 'jpg'

def generate_random_image_dir(base_dir='temp_save_dir', save_image_format= 'jpg'):
    unique_image_name = f"{''.join([choice(ascii_lowercase) for _ in range(randint(2, 10))])}_{date.today()}.{save_image_format}"

    return os.path.join(base_dir, unique_image_name)

def load_image_and_detect(base64_image):
    read_base64= base64_image.encode()
    read_base64= base64.decodebytes(read_base64)

    img= Image.open(BytesIO(read_base64))
    img= np.array(img)

    unique_image_dir= generate_random_image_dir(temp_save_dir, save_image_format)

    while os.path.isfile(unique_image_dir):
        unique_image_dir= generate_random_image_dir(temp_save_dir, save_image_format)
        
    cv2.imwrite(unique_image_dir,img)

    return_json= detect(unique_image_dir)

    try:
        os.remove(unique_image_dir)
    except:
        pass

    return return_json