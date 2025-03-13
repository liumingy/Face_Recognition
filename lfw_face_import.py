from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import random
import copy
import cv2
import numpy as np
import tensorflow as tf

from database_operation import save_ins_to_people, load_all_face_vector_from_people, load_name_by_job_id_from_people
import facenet
import align.detect_face
from PIL import Image

def get_lfw_folders(directory):
    """
    获取指定目录下的所有文件夹名称
    :param directory: lfw_funneled 目录路径
    :return: 文件夹名称列表
    """
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

def calculate_vector(images_path):
    image_size = 160
    margin = 44
    gpu_memory_fraction = 1.0
    model_path = r"D:\PythonWorkspace\Facial_Recognition\models\20180402-114759.pb"
    # mtcnn相关参数
    minsize = 30  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    # 创建mtcnn网络
    with tf.Graph().as_default():
        gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=gpu_memory_fraction)
        sess = tf.compat.v1.Session(
            config=tf.compat.v1.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)

    # Run forward pass to calculate embeddings
    with tf.Graph().as_default():
        with tf.compat.v1.Session() as sess:
            # Load the model
            facenet.load_model(model_path)
            # Get input and output tensors
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            tmp_images_path=copy.copy(images_path)
            img_list = []
            i = 0
            for image in tmp_images_path:
                i += 1
                if i % 100 == 0:
                    print(i)
                img = cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB)
                img_size = np.asarray(img.shape)[0:2]
                bounding_boxes, _ = align.detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
                if len(bounding_boxes) < 1:
                    images_path.remove(image)
                    print("can't detect face")
                    continue
                det = np.squeeze(bounding_boxes[0, 0:4])
                bb = np.zeros(4, dtype=np.int32)
                bb[0] = np.maximum(det[0] - margin / 2, 0)
                bb[1] = np.maximum(det[1] - margin / 2, 0)
                bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
                bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
                cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
                aligned = np.array(Image.fromarray(cropped).resize((image_size, image_size)))
                prewhitened = facenet.prewhiten(aligned)
                img_list.append(prewhitened)
            images = np.stack(img_list)
            feed_dict = {images_placeholder: images, phase_train_placeholder: False}
            emb = sess.run(embeddings, feed_dict=feed_dict)  # 计算向量
            return emb

def extract_between_slashes(s):
    parts = s.split("/")
    return parts[1] if len(parts) > 2 else None  # 确保至少有两个斜杠

if __name__ == '__main__':
    # 示例用法
    lfw_path = "lfw_funneled"
    folders = get_lfw_folders(lfw_path)
    images_path = []
    for item in folders:
        images_path.append(lfw_path + "/" + item + "/" + item + "_0001" + ".jpg")
    # images_path = images_path[:1000] # 202112136 - 202113135 准确率1.0
    images_path = images_path[1000:2000] # 202113136 - 202114135 准确率1.0
    # images_path = images_path[2000:3000] # 202114136 - 202115135
    # images_path = images_path[3000:4000]  # 202115136 - 202116134
    # images_path = images_path[4000:5000] # 202116135 - 202117134
    # images_path = images_path[5000:5749] # 202117135 - 202117883
    vectors = calculate_vector(images_path)
    count = 0
    for i in range(len(images_path)):
        # job_id = 202117135 + i
        # name = extract_between_slashes(images_path[i])
        # department_id = random.randint(1, 8)
        # is_manager = 0
        # face_vector = vectors[i]
        # save_ins_to_people(job_id, name, department_id, face_vector, is_manager)
        image_path = images_path[i]
        vector = vectors[i]
        data_vectors = load_all_face_vector_from_people()
        result = []
        for v in data_vectors:
            dist = [v[0], np.sqrt(np.sum(np.square(np.subtract(v[1], vector))))]
            result.append(dist)
        min_value_row = min(enumerate(result), key=lambda x: x[1][1])  # 第二列索引是1
        print(min_value_row)
        if min_value_row[1][1] <= 0.8:
            info = load_name_by_job_id_from_people(min_value_row[1][0])
            if info == extract_between_slashes(image_path):
                count += 1
        else:
            continue
    print(count / len(images_path))

