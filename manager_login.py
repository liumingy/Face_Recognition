import time

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from camera import Camera, Manager
from interface.manage_login_interface import Ui_MainWindow

class ManagerLogin(QMainWindow, Ui_MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self.flag = False

        # 创建摄像头流对象
        self.camera = Camera()
        # 设置定时器来实时更新图像
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.camera.update_image)
        self.camera_timer.start(50)  # 每50毫秒更新一次
        # 将二维画面添加到groupBox里
        layout = QVBoxLayout()
        layout.addWidget(self.camera.canvas)
        self.widget.setLayout(layout)

        # 为label绑定槽函数
        self.parent.parent.manager.result_signal.connect(self.sign)
        self.parent.parent.compare.recognition_fake_face_signal.connect(self.fake_face)

    def fake_face(self, is_fake_face):
        if is_fake_face:
            self.label.setStyleSheet(f"color: red;")
            self.label.setText("虚假人脸")

    def sign(self, result):
        if self.flag:
            min_value_row = min(enumerate(result), key=lambda x: x[1][1])  # 第二列索引是1
            print(f"管理员登录：{min_value_row}")
            if min_value_row[1][1] <= 1:
                self.flag = False
                self.parent.parent.manager.pause()
                self.hide()
                self.parent.show()
            else:
                self.label.setStyleSheet(f"color: red;")
                self.label.setText("验证失败")
        else:
            self.label.setText("人脸验证中")

    def closeEvent(self, event):
        self.parent.goto_main()
