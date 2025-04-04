import threading
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from database_operation import save_ins_to_people
from queue import Queue
from database_operation import load_all_face_vector_from_people, load_all_manager_face_vector_from_people
from facenet import Facenet
from PIL import Image
from align import detect_face
import tensorflow as tf

from real_face import is_real_face

capture = cv2.VideoCapture(0)
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

def grab_frame_resize(capture, width=180):
    """
    从摄像头捕获一帧并调整为3:4的宽高比
    
    参数:
        capture: OpenCV的VideoCapture对象
        width: 期望的图像宽度，高度将根据3:4的比例自动计算
        
    返回:
        调整后的RGB图像
    """
    # 捕获原始帧
    ret, frame = capture.read()
    if not ret or frame is None:
        return None
    # 水平镜像
    frame = np.fliplr(frame)
    # 转换为RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 计算目标高度（4:3的宽高比）
    height = int(width * 4 / 3)
    # 调整图像大小，保持纵横比
    original_height, original_width = frame.shape[:2]
    # 先计算中间裁剪部分
    if original_width / original_height > width / height:
        # 原图更宽，需要裁剪宽度
        crop_width = int(original_height * width / height)
        start_x = (original_width - crop_width) // 2
        cropped_frame = rgb_frame[:, start_x:start_x+crop_width]
    else:
        # 原图更高，需要裁剪高度
        crop_height = int(original_width * height / width)
        start_y = (original_height - crop_height) // 2
        cropped_frame = rgb_frame[start_y:start_y+crop_height, :]
    # 调整为目标尺寸
    resized_frame = cv2.resize(cropped_frame, (width, height))
    return resized_frame

class Recognition(QObject, threading.Thread):

    result_signal = pyqtSignal(list)

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
            if not queue_recognition_result.empty():
                try:
                    vector = queue_recognition_result.get(timeout=5)
                except Exception:
                    continue
                self.result = []
                vectors = load_all_face_vector_from_people()
                for v in vectors:
                    dist = [v[0], np.linalg.norm(v[1] - vector)]
                    self.result.append(dist)
                if self.result:
                    self.result_signal.emit(self.result)
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

class Compare(QObject, threading.Thread):

    recognition_fake_face_signal = pyqtSignal(bool)
    manager_fake_face_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # 用于暂停线程的标识
        self.flag = threading.Event()
        self.flag.set()  # 设置为True
        # 用于停止线程的标识
        self.running = threading.Event()
        self.running.set()  # 将running设置为True

    def run(self):
        # mtcnn相关参数
        minsize = 40
        threshold = [0.6, 0.7, 0.7]  # pnet、rnet、onet三个网络输出人脸的阈值，大于阈值则保留，小于阈值则丢弃
        factor = 0.709  # scale factor
        margin = 40
        image_size = 160
        # 创建mtcnn网络
        with tf.Graph().as_default():
            sess = tf.Session()
            with sess.as_default():
                pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')
        # Load the model
        model = Facenet()
        while self.running.is_set():
            self.flag.wait()

            # 打卡人脸识别模块
            if not queue_recognition_image.empty() and queue_recognition_result.empty():
                try:
                    image = queue_recognition_image.get(timeout=5)
                except Exception:
                    continue
                bounding_box, points = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                if len(bounding_box) < 1:
                    continue
                left_eye = (points[0][0], points[5][0])
                right_eye = (points[1][0], points[6][0])
                aligned, resized= align_face(image, left_eye, right_eye, bounding_box, margin, image_size)
                if not is_real_face(resized, "./model/anti_spoof_models", 0):
                    self.recognition_fake_face_signal.emit(True)
                    continue
                emb = np.array(model.detect_image(Image.fromarray(aligned)), dtype=np.float32)  # 计算向量
                queue_recognition_result.put(emb[0])

            # 注册人脸识别模块
            if not queue_register_image.empty() and queue_register_result.empty():
                try:
                    image = queue_register_image.get(timeout=5)
                except Exception:
                    continue
                bounding_box, points = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                if len(bounding_box) < 1:
                    continue
                left_eye = (points[0][0], points[5][0])
                right_eye = (points[1][0], points[6][0])
                aligned, resized = align_face(image, left_eye, right_eye, bounding_box, margin, image_size)
                if not is_real_face(resized, "./model/anti_spoof_models", 0):
                    continue
                emb = np.array(model.detect_image(Image.fromarray(aligned)), dtype=np.float32)  # 计算向量
                queue_register_result.put(emb[0])

            # 管理员登录人脸识别模块
            if not queue_manager_image.empty() and queue_manager_result.empty():
                try:
                    image = queue_manager_image.get(timeout=5)
                except Exception:
                    continue
                bounding_box, points = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
                if len(bounding_box) < 1:
                    continue
                left_eye = (points[0][0], points[5][0])
                right_eye = (points[1][0], points[6][0])
                aligned, resized = align_face(image, left_eye, right_eye, bounding_box, margin, image_size)
                if not is_real_face(resized, "./model/anti_spoof_models", 0):
                    self.manager_fake_face_signal.emit(True)
                    continue
                emb = np.array(model.detect_image(Image.fromarray(aligned)), dtype=np.float32)  # 计算向量
                queue_manager_result.put(emb[0])

            time.sleep(1)


    def pause(self):
        self.flag.clear()

    def resume(self):
        self.flag.set()

    def stop(self):
        self.flag.set()  # 将线程从暂停状态恢复, 如果已经暂停的话
        self.running.clear()

class Manager(QObject, threading.Thread):

    result_signal = pyqtSignal(list)

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
            if queue_manager_image.empty():
                queue_manager_image.put(grab_frame(capture))
            if not queue_manager_image.empty():
                try:
                    vector = queue_manager_result.get(timeout=5)
                except Exception:
                    continue
                self.result = []
                vectors = load_all_manager_face_vector_from_people()
                for v in vectors:
                    dist = [v[0], np.linalg.norm(v[1] - vector)]
                    self.result.append(dist)
                if self.result:
                    self.result_signal.emit(self.result)
            time.sleep(1)

    def pause(self):
        self.flag.clear()

    def resume(self):
        self.flag.set()

    def stop(self):
        self.flag.set()  # 将线程从暂停状态恢复, 如果已经暂停的话
        self.running.clear()

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

def align_face(image, left_eye, right_eye, bounding_box, margin=40, desired_size=160, resize_width=180):
    """
    对人脸图像进行截取和对齐
    
    参数:
        image: 原始图像
        left_eye: 左眼坐标 (x, y)
        right_eye: 右眼坐标 (x, y)
        bounding_box: 人脸边界框
        margin: 边界扩展像素
        desired_size: 输出图像大小
        resize_width: 3:4比例图像的宽度
        
    返回:
        aligned_face: 对齐后的人脸图像（正方形）
        resize_face: 3:4宽高比的人脸图像
    """
    # 计算眼睛中心点
    left_eye_center = (int(left_eye[0]), int(left_eye[1]))
    right_eye_center = (int(right_eye[0]), int(right_eye[1]))
    
    # 计算两眼之间的角度
    dy = right_eye_center[1] - left_eye_center[1]
    dx = right_eye_center[0] - left_eye_center[0]
    angle = np.degrees(np.arctan2(dy, dx))

    # 确定边界框
    det = np.squeeze(bounding_box[0, 0:4])
    bb = np.zeros(4, dtype=np.int32)
    bb[0] = np.maximum(det[0] - margin / 2, 0)  # x1
    bb[1] = np.maximum(det[1] - margin / 2, 0)  # y1
    bb[2] = np.minimum(det[2] + margin / 2, image.shape[1])  # x2
    bb[3] = np.minimum(det[3] + margin / 2, image.shape[0])  # y2
    
    # 截取人脸区域
    cropped = image[bb[1]:bb[3], bb[0]:bb[2], :]
    
    # 计算旋转中心（两眼中点）
    center_x = (left_eye_center[0] + right_eye_center[0]) // 2
    center_y = (left_eye_center[1] + right_eye_center[1]) // 2
    center = (center_x - bb[0], center_y - bb[1])  # 相对于裁剪图像的中心

    # 获取旋转矩阵
    M = cv2.getRotationMatrix2D(center, angle, 1)
    
    # 旋转裁剪后的图像
    rotated = cv2.warpAffine(cropped, M, (cropped.shape[1], cropped.shape[0]), 
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    
    # 调整为期望大小（正方形）
    aligned_face = cv2.resize(rotated, (desired_size, desired_size))
    
    # 计算3:4宽高比的目标尺寸
    target_width = resize_width
    target_height = int(resize_width * 4 / 3)
    
    # 步骤1: 首先在人脸周围扩展更大的margin
    expanded_margin = margin * 2  # 使用更大的margin
    face_bb = np.zeros(4, dtype=np.int32)
    face_bb[0] = np.maximum(det[0] - expanded_margin, 0)  # x1
    face_bb[1] = np.maximum(det[1] - expanded_margin, 0)  # y1
    face_bb[2] = np.minimum(det[2] + expanded_margin, image.shape[1])  # x2
    face_bb[3] = np.minimum(det[3] + expanded_margin, image.shape[0])  # y2
    
    # 步骤2: 计算扩展后的人脸区域中心点
    face_center_x = (face_bb[0] + face_bb[2]) // 2
    face_center_y = (face_bb[1] + face_bb[3]) // 2
    face_width = face_bb[2] - face_bb[0]
    face_height = face_bb[3] - face_bb[1]
    
    # 步骤3: 计算要扩展成的3:4宽高比区域
    # 计算当前宽高比
    current_ratio = face_width / face_height if face_height > 0 else 0
    target_ratio = 3 / 4  # 目标宽高比
    
    if current_ratio > target_ratio:
        # 宽度相对较大，需要增加高度
        adjusted_height = int(face_width / target_ratio)
        adjusted_width = face_width
    else:
        # 高度相对较大，需要增加宽度
        adjusted_width = int(face_height * target_ratio)
        adjusted_height = face_height
    
    # 步骤4: 根据计算的宽高比区域，在原图中截取对应区域
    # 计算截取区域坐标
    half_width = adjusted_width // 2
    half_height = adjusted_height // 2
    
    # 初始尝试截取的区域
    crop_x1 = face_center_x - half_width
    crop_y1 = face_center_y - half_height
    crop_x2 = face_center_x + half_width
    crop_y2 = face_center_y + half_height
    
    # 调整区域，处理边界情况
    if crop_x1 < 0:
        # 左边界越界，向右移动
        crop_x2 += abs(crop_x1)
        crop_x1 = 0
    if crop_y1 < 0:
        # 上边界越界，向下移动
        crop_y2 += abs(crop_y1)
        crop_y1 = 0
    if crop_x2 > image.shape[1]:
        # 右边界越界，向左移动
        crop_x1 -= (crop_x2 - image.shape[1])
        crop_x2 = image.shape[1]
    if crop_y2 > image.shape[0]:
        # 下边界越界，向上移动
        crop_y1 -= (crop_y2 - image.shape[0])
        crop_y2 = image.shape[0]
    
    # 最终边界调整，确保不越界
    crop_x1 = max(0, crop_x1)
    crop_y1 = max(0, crop_y1)
    crop_x2 = min(image.shape[1], crop_x2)
    crop_y2 = min(image.shape[0], crop_y2)
    
    # 截取图像
    resized_face = image[crop_y1:crop_y2, crop_x1:crop_x2]
    
    # 检查截取后的宽高比，如果不是3:4，进行中心裁剪
    if resized_face.shape[0] > 0 and resized_face.shape[1] > 0:
        current_width = resized_face.shape[1]
        current_height = resized_face.shape[0]
        current_ratio = current_width / current_height
        
        if abs(current_ratio - target_ratio) > 0.01:
            if current_ratio > target_ratio:
                # 宽度过大，从中心裁剪宽度
                target_width_crop = int(current_height * target_ratio)
                start_x = (current_width - target_width_crop) // 2
                resized_face = resized_face[:, start_x:start_x + target_width_crop]
            else:
                # 高度过大，从中心裁剪高度
                target_height_crop = int(current_width / target_ratio)
                start_y = (current_height - target_height_crop) // 2
                resized_face = resized_face[start_y:start_y + target_height_crop, :]
    
    # 调整为目标尺寸
    if resized_face.shape[0] > 0 and resized_face.shape[1] > 0:
        resized_face = cv2.resize(resized_face, (target_width, target_height))
    else:
        # 如果截取失败，使用原始图像
        resized_face = cv2.resize(image, (target_width, target_height))
    
    return aligned_face, resized_face