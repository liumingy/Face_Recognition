from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import threading
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from database_operation import save_ins_to_people
from queue import Queue
import tensorflow as tf
from database_operation import load_all_face_vector_from_people, load_all_manager_face_vector_from_people
import facenet
import align.detect_face
from PIL import Image


capture = cv2.VideoCapture(0)
model_path = r"D:\PythonWorkspace\Facial_Recognition\models\20180402-114759.pb"
queue_recognition_image = Queue()
queue_recognition_result = Queue()
queue_register_image = Queue()
queue_register_result = Queue()
queue_manager_image = Queue()
queue_manager_result =Queue()

def grab_frame(capture):
    ret, frame = capture.read()
    frame = np.fliplr(frame) # 水平镜像
    return cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)


class Recognition(QObject, threading.Thread):

    result_updated = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.result = []
        # 用于暂停线程的标识
        self.flag = threading.Event()
        self.flag.set()  # 设置为True
        # 用于停止线程的标识
        self.running = threading.Event()
        self.running.set()  # 将running设置为True

    def run(self):
        while self.running.is_set():
            self.flag.wait()
            if queue_recognition_image.empty():
                queue_recognition_image.put(grab_frame(capture))
                # queue_recognition_image.put(cv2.cvtColor(cv2.imread("D:\PythonWorkspace\Facial_Recognition\lfw_funneled\Aaron_Tippin\Aaron_Tippin_0001.jpg"),
                #                                          cv2.COLOR_BGR2RGB))
            if not queue_recognition_result.empty():
                try:
                    vector = queue_recognition_result.get(timeout=5)
                except Exception:
                    continue
                self.result = []
                vectors = load_all_face_vector_from_people()
                for v in vectors:
                    dist = [v[0], np.sqrt(np.sum(np.square(np.subtract(v[1], vector))))]
                    self.result.append(dist)
                if self.result:
                    self.result_updated.emit(self.result)
            time.sleep(1)

    def pause(self):
        self.flag.clear()

    def resume(self):
        self.flag.set()

    def stop(self):
        self.flag.set()  # 将线程从暂停状态恢复, 如果已经暂停的话
        self.running.clear()

class Camera:
    def __init__(self):
        # 创建matplotlib的Figure和Axes
        self.fig, self.ax = plt.subplots()
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)  # 填充整个fig
        self.ax.set_position([0, 0, 1, 1])  # 设置ax的位置为整个fig
        self.canvas = FigureCanvas(self.fig)

    def update_image(self):
        # 获取当前摄像头的图像
        frame = grab_frame(capture)
        if frame is None:
            print('获取帧失败')
            return
        # 清空原有图像并更新
        self.ax.clear()
        self.ax.imshow(frame)
        self.ax.axis('off')  # 关闭坐标轴
        self.canvas.draw()

class Compare(threading.Thread):
    def __init__(self):
        super().__init__()
        # 用于暂停线程的标识
        self.flag = threading.Event()
        self.flag.set()  # 设置为True
        # 用于停止线程的标识
        self.running = threading.Event()
        self.running.set()  # 将running设置为True
        self.image_size = 160
        self.margin = 44
        self.gpu_memory_fraction = 1.0

    def run(self):
        # mtcnn相关参数
        minsize = 30  # minimum size of face
        threshold = [0.6, 0.7, 0.7]  # three steps's threshold
        factor = 0.709  # scale factor
        # 创建mtcnn网络
        with tf.Graph().as_default():
            gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=self.gpu_memory_fraction)
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

                while self.running.is_set():
                    self.flag.wait()
                    if not queue_recognition_image.empty() and queue_recognition_result.empty():
                        try:
                            image = queue_recognition_image.get(timeout=5)
                        except Exception:
                            continue
                        img_size = np.asarray(image.shape)[0:2]
                        bounding_boxes, _ = align.detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                        if len(bounding_boxes) < 1:
                            print("can't detect face")
                            continue
                        det = np.squeeze(bounding_boxes[0, 0:4])
                        bb = np.zeros(4, dtype=np.int32)
                        bb[0] = np.maximum(det[0] - self.margin / 2, 0)
                        bb[1] = np.maximum(det[1] - self.margin / 2, 0)
                        bb[2] = np.minimum(det[2] + self.margin / 2, img_size[1])
                        bb[3] = np.minimum(det[3] + self.margin / 2, img_size[0])
                        cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
                        aligned = np.array(Image.fromarray(cropped).resize((self.image_size, self.image_size)))
                        prewhitened = facenet.prewhiten(aligned)
                        images = np.stack([prewhitened])
                        feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                        emb = sess.run(embeddings, feed_dict=feed_dict)  # 计算向量
                        queue_recognition_result.put(emb[0])
                    if not queue_register_image.empty() and queue_register_result.empty():
                        try:
                            image = queue_register_image.get(timeout=5)
                        except Exception:
                            continue
                        img_size = np.asarray(image.shape)[0:2]
                        bounding_boxes, _ = align.detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                        if len(bounding_boxes) < 1:
                            print("can't detect face")
                            continue
                        det = np.squeeze(bounding_boxes[0, 0:4])
                        bb = np.zeros(4, dtype=np.int32)
                        bb[0] = np.maximum(det[0] - self.margin / 2, 0)
                        bb[1] = np.maximum(det[1] - self.margin / 2, 0)
                        bb[2] = np.minimum(det[2] + self.margin / 2, img_size[1])
                        bb[3] = np.minimum(det[3] + self.margin / 2, img_size[0])
                        cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
                        aligned = np.array(Image.fromarray(cropped).resize((self.image_size, self.image_size)))
                        prewhitened = facenet.prewhiten(aligned)
                        images = np.stack([prewhitened])
                        feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                        emb = sess.run(embeddings, feed_dict=feed_dict)  # 计算向量
                        queue_register_result.put(emb[0])
                    if not queue_manager_image.empty() and queue_manager_result.empty():
                        try:
                            image = queue_manager_image.get(timeout=5)
                        except Exception:
                            continue
                        img_size = np.asarray(image.shape)[0:2]
                        bounding_boxes, _ = align.detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                        if len(bounding_boxes) < 1:
                            print("can't detect face")
                            continue
                        det = np.squeeze(bounding_boxes[0, 0:4])
                        bb = np.zeros(4, dtype=np.int32)
                        bb[0] = np.maximum(det[0] - self.margin / 2, 0)
                        bb[1] = np.maximum(det[1] - self.margin / 2, 0)
                        bb[2] = np.minimum(det[2] + self.margin / 2, img_size[1])
                        bb[3] = np.minimum(det[3] + self.margin / 2, img_size[0])
                        cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
                        aligned = np.array(Image.fromarray(cropped).resize((self.image_size, self.image_size)))
                        prewhitened = facenet.prewhiten(aligned)
                        images = np.stack([prewhitened])
                        feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                        emb = sess.run(embeddings, feed_dict=feed_dict)  # 计算向量
                        queue_manager_result.put(emb[0])
                    time.sleep(1)


    def pause(self):
        self.flag.clear()

    def resume(self):
        self.flag.set()

    def stop(self):
        self.flag.set()  # 将线程从暂停状态恢复, 如果已经暂停的话
        self.running.clear()

def manager_login():
    queue_manager_image.put(grab_frame(capture))
    try:
        vector = queue_manager_result.get(timeout=5)
        result = []
        vectors = load_all_manager_face_vector_from_people()
        for v in vectors:
            dist = [v[0], np.sqrt(np.sum(np.square(np.subtract(v[1], vector))))]
            result.append(dist)
        min_value_row = min(enumerate(result), key=lambda x: x[1][1])
        print(min_value_row)
        if min_value_row[1][1] <= 0.8:
            return True
        else:
            return False
    except Exception:
        return False

def register(job_id, name, department_id=0, is_manager=0):
    if job_id and name and department_id:
        queue_register_image.put(grab_frame(capture))
        try:
            vector = queue_register_result.get(timeout=5)
            save_ins_to_people(job_id, name, department_id, vector, is_manager)
            return True
        except Exception:
            return False
    else:
        return False