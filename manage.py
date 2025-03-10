import sys
from PyQt5.QtCore import QDate, QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QVBoxLayout
from camera import Camera, register
from interface.manage_interface import Ui_MainWindow
from database_operation import load_attendance, load_all_name_from_department, load_id_by_name_from_department, \
    load_sign_history, load_people


class Manage(QMainWindow, Ui_MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)  # 设置窗体
        self.parent = parent

        # 为工具栏按钮绑定槽函数
        self.actionCount.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.actionRegister.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.actionHistory.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.actionPeople.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(3))

        # 为跳转按钮绑定槽函数
        self.commandLinkButton.clicked.connect(self.goto_main)
        self.commandLinkButton_2.clicked.connect(self.goto_main)
        self.commandLinkButton_3.clicked.connect(self.goto_main)
        self.commandLinkButton_4.clicked.connect(self.goto_main)

        # 填充出勤统计表，绑定日期切换槽函数
        self.calendarWidget.clicked.connect(self.show_attendance)
        self.calendarWidget.currentPageChanged.connect(self.month_changed)
        self.show_attendance()

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

        # 为人脸注册各组件初始化
        departments = load_all_name_from_department()
        self.comboBox.addItems(["员工", "管理员"])
        self.comboBox_2.addItems(departments)
        self.pushButton.clicked.connect(self.register_ok)

        # 初始化打卡记录表
        sign_history = load_sign_history()
        keys = ["date", "job_id", "name", "department", "sign_in", "sign_out"]
        self.tableWidget_2.setRowCount(len(sign_history))
        for row, record in enumerate(sign_history):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_2.setItem(row, col, item)
        self.tableWidget_2.resizeRowsToContents()

        # 初始化员工信息表
        people_info = load_people()
        keys = ["job_id", "name", "department", "is_manager"]
        self.tableWidget_3.setRowCount(len(people_info))
        for row, record in enumerate(people_info):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_3.setItem(row, col, item)
        self.tableWidget_3.resizeRowsToContents()

    def register_ok(self):
        if self.comboBox.currentText() == "管理员":
            is_manager = 1
        else:
            is_manager = 0
        job_id = self.lineEdit.text()
        name = self.lineEdit_2.text()
        department_id = load_id_by_name_from_department(self.comboBox_2.currentText())
        register(job_id, name, department_id, is_manager)

    def month_changed(self, year, month):
        new_date = QDate(year, month, 1)
        self.calendarWidget.setSelectedDate(new_date)
        self.show_attendance()

    def show_attendance(self):
        date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        attendance_data = load_attendance(date)
        keys = ["job_id", "name", "department", "day_duration", "attendance_day", "month_duration"]
        self.tableWidget.setRowCount(len(attendance_data))
        for row, record in enumerate(attendance_data):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget.setItem(row, col, item)
        self.tableWidget.resizeRowsToContents()

    def goto_main(self):
        self.hide()
        self.parent.recognition.resume()
        self.parent.show()

    def closeEvent(self, event):
        # 在关闭窗口时执行的关闭函数
        self.parent.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    manage = Manage(None)
    manage.show()
    sys.exit(app.exec_())