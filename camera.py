import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mtcnn import MTCNN
import threading

capture = cv2.VideoCapture(0)

class CutImage (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        if capture is not None:
            while True:
                # 获取一帧
                # frame = cv2.cvtColor(cv2.imread('ivan.jpg'), cv2.COLOR_BGR2RGB)
                frame = grab_frame(capture)
                # 获取图像大小
                max_height, max_width = frame.shape[0], frame.shape[1]
                # 创建检测器
                detector = MTCNN(device="CPU:0")
                # 人脸检测结果
                result = detector.detect_faces(frame)
                # 画出人脸
                # start = (e['box'][0], e['box'][1]) # [x, y]
                # end = (e['box'][0] + e['box'][2], e['box'][1] + e['box'][3])
                # cv2.rectangle(frame, start, end, (0, 0, 255), 2)
                # cv2.circle(frame, e['keypoints']['left_eye'], 1, (0, 0, 255), 4)
                # cv2.circle(frame, e['keypoints']['mouth_left'], 1, (0, 0, 255), 4)
                # cv2.circle(frame, e['keypoints']['mouth_right'], 1, (0, 0, 255), 4)
                # cv2.circle(frame, e['keypoints']['nose'], 1, (0, 0, 255), 4)
                # cv2.circle(frame, e['keypoints']['right_eye'], 1, (0, 0, 255), 4)
                for e in result:
                    if e['confidence'] >= 0.95:
                        width = e['box'][2] # x
                        height = e['box'][3] # y
                        start = [e['box'][0], e['box'][1]] # [x, y]
                        if height > width:
                            start[0] -= round((height - width) / 2)
                            width = height
                        else:
                            start[1] -= round((height - width) / 2)
                            height = width
                        frame = frame[max(0, start[1]):min(max_height, start[1] + height),
                                max(0, start[0]):min(max_width, start[0] + width)] # 裁剪坐标为[y0:y1, x0:x1]
                        # 放缩到160*160
                        frame = cv2.resize(frame, (160, 160))
                        cv2.imwrite('output_image.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    else:
                        continue
                time.sleep(0.5)
                break
        else:
            print("Fail to open camera")

class Camera():
    def __init__(self):
        # 创建新线程
        thread = CutImage()
        # 开启新线程
        thread.start()
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


def grab_frame(capture):
    ret, frame = capture.read()
    # 水平镜像
    frame = np.fliplr(frame)
    return cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)


