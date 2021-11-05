#!/usr/bin/env python

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


import torch

class WinterSimObjectDetection():

    def Detect(self, image):

        # Inference
        result = self.model(image, size=640)

        result.display(render=True)

        return result.imgs[0]

    def __init__(self):
        super(WinterSimObjectDetection, self).__init__()

        # load model
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # or yolov5m, yolov5l, yolov5x, custom

       