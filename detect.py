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

def detect(source, trace=False, weights='model_weights/best.pt', img_size=512, conf_thres=0.4, iou_thres=0.45, agnostic_nms= False, save_txt= True, save_img=False, save_conf= True, detect_path='runs/detect', detect_sub_path='detect_res', is_augment=False, class_filter=None):
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
                for xmin, ymin, w, h, conf, cls in reversed(det):
                      cls= cls.item()
                      xmin, ymin, w, h= xmin.item(), ymin.item(), w.item(), h.item()
                      xmax, ymax= xmin+w, ymin+h

                      top_left, top_right, bottom_left, bottom_right= [[xmin, ymin], [xmax, ymin], [xmin, ymax], [xmax, ymax]]
                      conf= conf.item()

                      temp_dict= {
                          'class': int(cls),
                          'confidence': conf,
                          'bounding_box':{
                              'top_left': top_left,
                              'top_right': top_right,
                              'bottom_left': bottom_left,
                              'bottom_right': bottom_right,
                          }
                      }

                      json_object_detected.append(temp_dict)

                result['status']= json_status
                result['detection_count']= json_detection_count
                result['object_detected']= json_object_detected


    return json.dumps(result)