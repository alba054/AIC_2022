import time
from pathlib import Path

from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import check_img_size, non_max_suppression, \
    scale_coords, set_logging
from utils.torch_utils import select_device, time_synchronized, TracedModel

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
import json

def detect(source, trace=False, weights='model_weights/best.pt', img_size=512, conf_thres=0.4, iou_thres=0.5, agnostic_nms= False, is_augment=False, class_filter=None):
    # Initialize
    set_logging()
    device = select_device('')
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(img_size, s=stride)  # check img_size

    if trace:
        model = TracedModel(model, device, img_size)

    if half:
        model.half()  # to FP16
        
    dataset = LoadImages(source, img_size=imgsz, stride=stride)
        
    old_img_w = old_img_h = imgsz
    old_img_b = 1

    # t0 = time.time()
    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Warmup
        if device.type != 'cpu' and (old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
            old_img_b = img.shape[0]
            old_img_h = img.shape[2]
            old_img_w = img.shape[3]
            for i in range(3):
                model(img, augment=is_augment)[0]

        # Inference
        # t1 = time_synchronized()
        pred = model(img, augment=is_augment)[0]
        # t2 = time_synchronized()

        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=class_filter, agnostic=agnostic_nms)
        # t3 = time_synchronized()


        result= {
                'status':'failed',
                'detection_count': 0,
                'object_detected': []
        }
        abs_height, abs_width=  im0s.shape[0:2]
        # Process detections
        for i, det in enumerate(pred):  # detections per image
            im0= im0s
            
            if len(det):
                json_status= 'success'
                json_detection_count= len(det)
                json_object_detected= []

                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Write results
                temp_dict= {}
                for xmin, ymin, xmax, ymax, conf, cls in reversed(det):
                      cls= cls.item()
                      xmin, ymin, xmax, ymax= xmin.item(), ymin.item(), xmax.item(), ymax.item()

                      xmin, xmax= xmin/abs_width, xmax/abs_width
                      ymin, ymax= ymin/abs_height, ymax/abs_height
                      
                    #   top_left, top_right, bottom_left, bottom_right= [[xmin, ymin], [xmax, ymin], [xmin, ymax], [xmax, ymax]]
                      conf= conf.item()

                      temp_dict= {
                          'class': int(cls),
                          'confidence': conf,
                          'bounding_box':{
                              'xmin': xmin,
                              'xmax': xmax,
                              'ymin': ymin,
                              'ymax': ymax,
                          }
                      }

                      json_object_detected.append(temp_dict)

                result['status']= json_status
                result['detection_count']= json_detection_count
                result['object_detected']= json_object_detected


    return json.dumps(result)


from string import ascii_lowercase
from random import choice, randint, random
from datetime import date
import numpy as np

import os
import shutil

from io import BytesIO
from PIL import Image
import base64


model_weights_dir= 'model_weights/best.pt'
temp_save_dir= 'temp_save_dir'

if not os.path.isdir(temp_save_dir):
    os.mkdir(temp_save_dir)

save_image_format= 'jpg'

def generate_random_image_dir(base_dir='temp_save_dir', save_image_format= 'jpg'):
    unique_image_name = f"{''.join([choice(ascii_lowercase) for _ in range(randint(2, 10))])}_{date.today()}.{save_image_format}"

    return os.path.join(base_dir, unique_image_name)

def load_image_and_detect(base64_image, class_filter=None):
    read_base64= base64_image.encode()
    read_base64= base64.decodebytes(read_base64)

    img= Image.open(BytesIO(read_base64))
    img= np.array(img)

    unique_image_dir= generate_random_image_dir(temp_save_dir, save_image_format)

    while os.path.isfile(unique_image_dir):
        unique_image_dir= generate_random_image_dir(temp_save_dir, save_image_format)
        
    cv2.imwrite(unique_image_dir,img)

    return_json= detect(unique_image_dir, class_filter= class_filter)

    try:
        os.remove(unique_image_dir)
    except:
        pass

    return return_json

def hello_name(name):
    print("hello " + name)
