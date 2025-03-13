import sys
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot, Qt, QObject
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("加载中")
        self.setModal(True)
        self.resize(300, 100)

        # 用于显示加载动画的标签
        self.label = QLabel("加载中", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 动画相关变量
        self.dot_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
        self.timer.start(500)  # 每500毫秒更新一次

    def update_text(self):
        """更新标签文本，模拟加载动画"""
        self.dot_count = (self.dot_count + 1) % 4  # 0~3个点循环
        self.label.setText("加载中" + "." * self.dot_count)

    @pyqtSlot()
    def task_finished(self):
        """任务完成时关闭弹窗"""
        self.timer.stop()
        self.accept()  # 关闭对话框并返回 Accepted


# 模拟外部任务的对象
class Worker(QObject):
    # 定义任务完成信号
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 模拟任务：5秒后发射 finished 信号
        QTimer.singleShot(5000, self.on_finished)

    def on_finished(self):
        self.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建加载中对话框
    loading_dialog = LoadingDialog()

    # 模拟外部任务
    worker = Worker()
    # 连接外部任务的 finished 信号到对话框的 task_finished 槽函数
    worker.finished.connect(loading_dialog.task_finished)

    # 以模态方式显示加载中弹窗，直到任务完成关闭
    loading_dialog.exec_()

    print("任务完成，对话框已关闭。")
    sys.exit(0)
