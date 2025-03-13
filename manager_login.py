import time

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from camera import manager_login, Camera
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

        # 设置定时器来进行人脸检测
        self.login_timer = QTimer(self)
        self.login_timer.timeout.connect(self.login)
        self.login_timer.start(3000)  # 每2000毫秒执行一次

    def login(self):
        if self.flag:
            if manager_login():
                self.flag = False
                self.hide()
                self.parent.show()
            else:
                self.label.setText("验证失败")
        else:
            self.label.setText("人脸验证中")

    def closeEvent(self, event):
        self.parent.goto_main()
