#!/usr/bin/env python

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from math import fabs
import os

from numpy import true_divide
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
sys.path.insert(0, './yolov5')

from yolov5.models.experimental import attempt_load
from yolov5.utils.downloads import attempt_download
from yolov5.utils.datasets import DirectDataset, LoadImages, LoadStreams
from yolov5.utils.general import check_img_size, non_max_suppression, scale_coords, check_imshow, xyxy2xywh
from yolov5.utils.torch_utils import select_device, time_sync
from yolov5.utils.plots import Annotator, colors
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort
import argparse
import os
import platform
import shutil
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np

class WinterSimObjectDetectionDeepSort():

    def Input(self, image):
        with torch.no_grad():
            return self.detect(self.args, image)

    def detect(self, opt, image):
        out, source, yolo_weights, deep_sort_weights, show_vid, save_vid, save_txt, imgsz, evaluate, half = \
            opt.output, opt.source, opt.yolo_weights, opt.deep_sort_weights, opt.show_vid, opt.save_vid, \
                opt.save_txt, opt.img_size, opt.evaluate, opt.half
        webcam = source == '0' or source.startswith(
            'rtsp') or source.startswith('http') or source.endswith('.txt')

        img = image
        if self.init_done == False:
            # initialize deepsort
            cfg = get_config()
            cfg.merge_from_file(opt.config_deepsort)
            attempt_download(deep_sort_weights, repo='mikel-brostrom/Yolov5_DeepSort_Pytorch')
            self.deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                                max_dist=cfg.DEEPSORT.MAX_DIST, min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                                max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                                max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                                use_cuda=True)

            # Initialize
            self.device = select_device(opt.device)
            self.half &= self.device.type != 'cpu'  # half precision only supported on CUDA

            # Load model
            print("using model: " + str(yolo_weights))
            self.model = attempt_load(yolo_weights, map_location=self.device)  # load FP32 model
            self.stride = int(self.model.stride.max())  # model stride
            imgsz = check_img_size(imgsz, s=self.stride)  # check img_size
            self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names  # get class names
            if self.half:
                self.model.half()  # to FP16
                print("using half precision.")
            #if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, imgsz, imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
            self.init_done = True
            
        dataset = DirectDataset(img0=img, img_size=imgsz, stride=self.stride)

        for frame_idx, (path, img, im0s, vid_cap) in enumerate(dataset):
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Inference
            pred = self.model(img, augment=opt.augment)[0] # this takes 200 ms

            # Apply NMS
            pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)

            # Process detections
            for i, det in enumerate(pred):  # detections per image
               
                im0 = im0s
                annotator = Annotator(np.ascontiguousarray(im0), line_width=2, pil=not ascii)

                if det is not None and len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(
                        img.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        #s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    xywhs = xyxy2xywh(det[:, 0:4])
                    confs = det[:, 4]
                    clss = det[:, 5]

                    # pass detections to deepsort
                    outputs = self.deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), im0)

                    # draw boxes for visualization
                    if len(outputs) > 0:
                        for j, (output, conf) in enumerate(zip(outputs, confs)): 
                            
                            bboxes = output[0:4]
                            id = output[4]
                            cls = output[5]

                            c = int(cls)  # integer class
                            #label = f'{id} {self.names[c]} {conf:.2f}'
                            label = f'{self.names[c]}'
                            annotator.box_label(bboxes, label, color=colors(c, True))

                else:
                    self.deepsort.increment_ages()

                return annotator.result()

    def __init__(self):
        super(WinterSimObjectDetectionDeepSort, self).__init__()

        parser = argparse.ArgumentParser()
        parser.add_argument('--yolo_weights', nargs='+', type=str, default='yolov5n.pt', help='model.pt path(s)')
        parser.add_argument('--deep_sort_weights', type=str, default='deep_sort_pytorch/deep_sort/deep/checkpoint/ckpt.t7', help='ckpt.t7 path')
        # file/folder, 0 for webcam
        parser.add_argument('--source', type=str, default=' ', help='source')
        parser.add_argument('--output', type=str, default='inference/output', help='output folder')  # output folder
        parser.add_argument('--img-size', type=int, default=320, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=0.4, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.5, help='IOU threshold for NMS')
        parser.add_argument('--fourcc', type=str, default='mp4v', help='output video codec (verify ffmpeg support)')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--show-vid', action='store_true', default=True, help='display tracking video results')
        parser.add_argument('--save-vid', action='store_true', help='save video tracking results')
        parser.add_argument('--save-txt', action='store_true', help='save MOT compliant results to *.txt')
        # class 0 is person, 1 is bycicle, 2 is car... 79 is oven
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 16 17')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', default=False, help='augmented inference')
        parser.add_argument('--evaluate', action='store_true', help='augmented inference')
        parser.add_argument("--config_deepsort", type=str, default="deep_sort_pytorch/configs/deep_sort.yaml")
        parser.add_argument("--half", action="store_true", default=True, help="use FP16 half-precision inference")
        args = parser.parse_args()
        args.img_size = check_img_size(args.img_size)

        self.args = args
        self.init_done = False
        self.device = None
        self.model = None
        self.dataset = None
        self.deepsort = None
        self.stride = None
        self.names = None
        self.half = False