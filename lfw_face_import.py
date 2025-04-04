import os
import random

import cv2
import numpy as np
import tensorflow as tf
from align import detect_face
from database_operation import save_ins_to_people, load_all_face_vector_from_people, load_name_by_job_id_from_people
import facenet
from PIL import Image

def get_lfw_folders(directory):
    """
    获取指定目录下的所有文件夹名称
    :param directory: lfw_funneled 目录路径
    :return: 文件夹名称列表
    """
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

def calculate_vector(images_path):
    # mtcnn相关参数
    minsize = 40
    threshold = [0.6, 0.7, 0.7]  # pnet、rnet、onet三个网络输出人脸的阈值，大于阈值则保留，小于阈值则丢弃
    factor = 0.709  # scale factor
    margin = 44
    image_size = 160
    # 创建mtcnn网络
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')
    # Load the model
    model = facenet.Facenet()
    result = []
    for image_path in images_path:
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        img_size = np.asarray(image.shape)[0:2]
        bounding_box, _ = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
        if len(bounding_box) < 1:
            continue
        det = np.squeeze(bounding_box[0, 0:4])
        bb = np.zeros(4, dtype=np.int32)
        bb[0] = np.maximum(det[0] - margin / 2, 0)
        bb[1] = np.maximum(det[1] - margin / 2, 0)
        bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
        bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
        cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
        aligned = cv2.resize(cropped, (image_size, image_size))
        emb = np.array(model.detect_image(Image.fromarray(aligned)), dtype=np.float32)  # 计算向量
        result.append(emb[0])
    return result

def extract_between_slashes(s):
    parts = s.split("/")
    return parts[1] if len(parts) > 2 else None  # 确保至少有两个斜杠

if __name__ == '__main__':
    # 示例用法
    lfw_path = "lfw"
    folders = get_lfw_folders(lfw_path)
    images_path = []
    for item in folders:
        images_path.append(lfw_path + "/" + item + "/" + item + "_0001" + ".jpg")
    # images_path = images_path[:1000] # 202112136 - 202113135
    images_path = images_path[1000:2000] # 202113136 - 202114135
    # images_path = images_path[2000:3000] # 202114136 - 202115135
    vectors = calculate_vector(images_path)
    for i in range(len(images_path)):
        job_id = 202113136 + i
        name = extract_between_slashes(images_path[i])
        department_id = random.randint(1, 8)
        is_manager = 0
        face_vector = vectors[i]
        save_ins_to_people(job_id, name, department_id, face_vector, is_manager)
        print(name)

