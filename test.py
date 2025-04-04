from camera import register, Compare

# # 创建比较神经网络
# compare = Compare()
# # 运行线程
# compare.start()
# register(202112135, "刘明宇", 1, 1)

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
import sys


class ColorLabel(QWidget):
    def __init__(self, flag):
        super().__init__()

        self.label = QLabel("文本颜色变化", self)
        self.update_color(flag)  # 根据 flag 设置颜色

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_color(self, flag):
        """根据 flag 的值更新 QLabel 文本颜色"""
        color_map = {0: "blue", 1: "green", 2: "red"}
        color = color_map.get(flag, "black")  # 默认黑色
        self.label.setStyleSheet(f"color: {color}; font-size: 20px;")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    flag = 1  # 设置 flag 值（0=蓝色，1=绿色，2=红色）
    window = ColorLabel(flag)
    window.show()

    sys.exit(app.exec_())
