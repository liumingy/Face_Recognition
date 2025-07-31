import sys
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from camera import Camera, Recognition, Compare, Manager
from interface.main_interface import Ui_MainWindow
from database_operation import load_name_by_job_id_from_people, save_ins_to_history
from manage import Manage
from manager_login import ManagerLogin
from collections import Counter

def has_element_three_or_more(lst):
    counts = Counter(lst)
    return any(count >= 3 for count in counts.values())

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置窗体
        self.cache = []

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

        # 创建人脸识别对象
        self.recognition = Recognition()
        self.recognition.start()
        # 创建管理员登录人脸识别对象
        self.manager = Manager()
        self.manager.pause()
        self.manager.start()

        # 创建比较神经网络
        self.compare = Compare()
        self.compare.start()

        # 为label绑定槽函数
        self.recognition.result_signal.connect(self.sign)
        self.compare.recognition_fake_face_signal.connect(self.fake_face)

        # 为跳转按钮绑定槽函数
        self.commandLinkButton.clicked.connect(self.goto_manage)

    def fake_face(self, is_fake_face):
        if is_fake_face:
            self.label.setStyleSheet(f"color: red;")
            self.label.setText("虚假人脸")

    def sign(self, result):
        min_value_row = min(enumerate(result), key=lambda x: x[1][1])  # 第二列索引是1
        print(min_value_row)
        print(f"人脸打卡：{min_value_row}")
        if min_value_row[1][1] <= 1:
            info = str(min_value_row[1][0]) + load_name_by_job_id_from_people(min_value_row[1][0]) + " "
            type = save_ins_to_history(min_value_row[1][0])
            if type == 1:
                self.label.setStyleSheet(f"color: blue;")
                info += "签到成功"
            elif type == 2:
                self.label.setStyleSheet(f"color: green;")
                info += "已签到"
            elif type == 3:
                self.label.setStyleSheet(f"color: green;")
                info += "签退成功"
            elif type == 4:
                self.label.setStyleSheet(f"color: blue;")
                info += "已签退"
            elif type == -1:
                self.label.setStyleSheet(f"color: red;")
                info += "签到/签退失败"
        else:
            self.label.setStyleSheet(f"color: red;")
            info = "未知人脸"
        self.label.setText(info)

    def goto_manage(self):
        self.hide()  # 子窗口打开后隐藏主窗口
        self.recognition.pause()  # 暂停recognition线程
        self.camera_timer.stop()
        self.manager.resume()
        manager_login.flag = True
        manager_login.camera_timer.start(50)
        manager_login.show()

    def closeEvent(self, event):
        # 在关闭窗口时执行的关闭函数
        self.manager.stop()
        self.recognition.stop()
        self.compare.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()  # 主界面
    manage = Manage(main)
    manager_login = ManagerLogin(manage)
    main.show()
    sys.exit(app.exec_())