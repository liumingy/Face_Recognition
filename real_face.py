# -*- coding: utf-8 -*-
# @Time : 20-6-9 下午3:06
# @Author : zhuying
# @Company : Minivision
# @File : test.py
# @Software : PyCharm

import os
import cv2
import numpy as np
import argparse
import warnings
import time

from anti.anti_spoof_predict import AntiSpoofPredict
from anti.generate_patches import CropImage
from anti.utility import parse_model_name
warnings.filterwarnings('ignore')


SAMPLE_IMAGE_PATH = "./"


# 因为安卓端APK获取的视频流宽高比为3:4,为了与之一致，所以将宽高比限制为3:4
def check_image(image):
    height, width, channel = image.shape
    if width/height != 3/4:
        print("Image is not appropriate!!!\nHeight/Width should be 4/3.")
        return False
    else:
        return True


def is_real_face(image, model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    result = check_image(image)
    if result is False:
        return
    image_bbox = model_test.get_bbox(image)
    prediction = np.zeros((1, 3))
    test_speed = 0
    # sum the prediction from single model's result
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        start = time.time()
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))
        test_speed += time.time()-start

    # draw result of prediction
    label = np.argmax(prediction)
    value = prediction[0][label]/2
    if label == 1:
        # print("Image is Real Face. Score: {:.2f}.".format(value))
        # result_text = "RealFace Score: {:.2f}".format(value)
        # color = (255, 0, 0)
        return True, value
    else:
        # print("Image is Fake Face. Score: {:.2f}.".format(value))
        # result_text = "FakeFace Score: {:.2f}".format(value)
        # color = (0, 0, 255)
        return False, value
    # print("Prediction cost {:.2f} s".format(test_speed))
    #
    # cv2.imwrite("test.jpg", image)
    # cv2.rectangle(
    #     image,
    #     (image_bbox[0], image_bbox[1]),
    #     (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
    #     color, 2)
    # cv2.imwrite("test_result.jpg", image)


if __name__ == "__main__":
    image = cv2.imread("test.jpg")
    model_dir = "./model/anti_spoof_models"
    is_real_face(image, model_dir, 0)
