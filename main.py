import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from camera import Camera, Recognition, Compare, manager_login
from interface.main_interface import Ui_MainWindow
from database_operation import load_name_by_job_id_from_people, save_ins_to_history
from manage import Manage
from manager_login import ManagerLogin


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置窗体

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
        # 运行线程
        self.recognition.start()

        # 创建比较神经网络
        self.compare = Compare()
        # 运行线程
        self.compare.start()

        # 将文本绑定到textBrowser中
        self.recognition.result_updated.connect(self.sign)

        # 为跳转按钮绑定槽函数
        self.commandLinkButton.clicked.connect(self.goto_manage)

    def sign(self, result):
        min_value_row = min(enumerate(result), key=lambda x: x[1][1])  # 第二列索引是1
        print(min_value_row)
        if min_value_row[1][1] <= 0.8:
            info = load_name_by_job_id_from_people(min_value_row[1][0])
            type = save_ins_to_history(min_value_row[1][0])
            if type == 0:
                info += "已签到"
            elif type == 1:
                info += "签到成功"
            elif type == 2:
                info += "签退成功"
            elif type == -1:
                info += "已签退，签到失败"
            elif type == -2:
                info += "签退失败"
        else:
            info = "未知"
        self.label.setText(info)

    def goto_manage(self):
        self.hide()  # 子窗口打开后隐藏主窗口
        self.recognition.pause()  # 暂停recognition线程
        manager_login.flag = True
        manager_login.show()

    def closeEvent(self, event):
        # 在关闭窗口时执行的关闭函数
        self.recognition.stop()
        self.compare.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()  # 主界面
    manage = Manage(main)
    manager_login = ManagerLogin(manage)
    main.show()
    sys.exit(app.exec_())