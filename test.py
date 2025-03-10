import sys

import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QPushButton, QVBoxLayout, QLabel
)


class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模态对话框")
        self.setGeometry(150, 150, 300, 200)

        # 设置对话框布局
        layout = QVBoxLayout()
        label = QLabel("这是一个模态对话框，点击确定关闭")
        layout.addWidget(label)

        # 创建按钮，点击按钮调用 accept() 关闭对话框
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主窗口")
        self.setGeometry(100, 100, 400, 300)

        # 创建一个按钮，点击时弹出模态对话框
        self.btn_open_dialog = QPushButton("打开模态对话框", self)
        self.btn_open_dialog.clicked.connect(self.open_modal_dialog)
        self.setCentralWidget(self.btn_open_dialog)

    def open_modal_dialog(self):
        # 创建对话框实例，并以模态方式显示（阻塞调用线程）
        dialog = MyDialog(self)
        result = dialog.exec_()  # 此处阻塞，直到对话框关闭
        if result == QDialog.Accepted:
            print("对话框以 '确定' 关闭")
        else:
            print("对话框被关闭")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
