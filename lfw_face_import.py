import os
import random

import cv2
import numpy as np
import tensorflow as tf
from align import detect_face
from database_operation import save_ins_to_people, load_all_face_vector_from_people, load_name_by_job_id_from_people
import facenet
from PIL import Image
from tqdm import tqdm

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
    for image_path in tqdm(images_path, desc="计算人脸向量"):
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

def get_random_name():
    """
    从name.txt文件中随机读取一行作为姓名
    :return: 随机选择的姓名
    """
    try:
        with open('name.txt', 'r', encoding='utf-8') as f:
            names = f.readlines()
            # 去除每行的换行符
            names = [name.strip() for name in names if name.strip()]
            if names:
                return random.choice(names)
            else:
                return "未知"
    except Exception as e:
        print(f"读取name.txt文件出错: {e}")
        return "未知"

def delete_even_lines():
    """
    删除name.txt文件中的偶数行
    """
    try:
        # 读取文件内容
        with open('name.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 只保留奇数行（索引从0开始，所以是0,2,4...）
        odd_lines = [line for i, line in enumerate(lines) if i % 2 == 0]
        
        # 写回文件
        with open('name.txt', 'w', encoding='utf-8') as f:
            f.writelines(odd_lines)
            
        print(f"已删除偶数行，剩余{len(odd_lines)}行")
    except Exception as e:
        print(f"处理name.txt文件时出错: {e}")

if __name__ == '__main__':
    lfw_path = "lfw_funneled"
    folders = get_lfw_folders(lfw_path)
    images_path = []
    for item in folders:
        images_path.append(lfw_path + "/" + item + "/" + item + "_0001" + ".jpg")
    images_path = images_path[:1000]
    # images_path = images_path[1000:2000]
    vectors = calculate_vector(images_path)
    job_id = 202112136
    for i in tqdm(range(len(images_path)), desc="保存人员信息"):
        job_id += i * random.randint(2, 5)
        name = get_random_name()
        department_id = random.randint(1, 10)
        is_manager = 0
        face_vector = vectors[i]
        save_ins_to_people(job_id, name, department_id, face_vector, is_manager)

