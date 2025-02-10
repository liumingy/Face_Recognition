import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from camera import Camera
from main_interface import Ui_MainWindow


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置窗体
        # 创建摄像头流对象
        self.camera = Camera()
        # 设置定时器来实时更新图像
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.camera.update_image)
        self.timer.start(30)  # 每30毫秒更新一次
        # 将二维画面添加到groupBox里
        layout = QVBoxLayout()
        layout.addWidget(self.camera.canvas)
        self.groupBox.setLayout(layout)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()  # 主界面
    main.show()
    sys.exit(app.exec_())