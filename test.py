from add_history import AddHistory
from camera import register, Compare

# # 创建比较神经网络
# compare = Compare()
# # 运行线程
# compare.start()
# register(202112135, "刘明宇", 1, 1)
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QProgressBar
from PyQt5.QtCore import Qt, QTimer

class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()
        self.timer = QTimer()  # 初始化一个定时器
        self.timer.timeout.connect(self.task)  # 连接绑定到任务方法
        self.count = 1  # 计数器

        # 启动定时器
        self.timer.start(100)  # （单位毫秒）每100毫秒秒触发一次方法self.task

    # 样式以及
    def initUI(self):
        self.pbar = QProgressBar(self)  # 进度条默认值是100
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbar.setStyleSheet("QProgressBar {border: 2px solid grey; border-radius: 5px; padding: 1px}"
                                "QProgressBar::chunk {background-color: #3399ff; width: 10px;}")
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setFormat('%p%')

        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('QProgressBar')

    # 定时器任务
    def task(self):
        self.pbar.setValue(self.count)
        self.count += 1
        if self.count == 100:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.setFixedHeight(100)
    ex.setFixedWidth(270)
    ex.show()
    sys.exit(app.exec_())



