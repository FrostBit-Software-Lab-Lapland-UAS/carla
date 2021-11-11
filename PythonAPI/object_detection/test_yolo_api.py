import numpy as np
import cv2
import time

from yolov5_api import WinterSimObjectDetectionDeepSort

image = cv2.imread('C:/Users/anarkila/Desktop/yolov5/yolov5_deepsort/Yolov5_DeepSort_Pytorch/test.jpg')
image2 = cv2.imread('C:/Users/anarkila/Desktop/yolov5/yolov5_deepsort/Yolov5_DeepSort_Pytorch/test_image.jpg')

# cv2.imshow("OpenCV Image Reading", image)
# cv2.waitKey(0)

x = WinterSimObjectDetectionDeepSort()


# start = time.perf_counter()
# detect = x.Input(image)
# end = time.perf_counter()
# mm = (end - start) * 1000
# print(f"done {mm:0.4f} milliseconds")

# cv2.imshow("Detected", image)
# cv2.waitKey(0)
# time.sleep(5)


for i in range(10):
    if i % 2 == 0:
        im = image
    else:
        im = image2

    detect = x.Input(im)

    cv2.imshow("Detected", image)
    cv2.waitKey(0)
    time.sleep(1)