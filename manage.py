import sys
from PyQt5.QtCore import QDate, QTimer, Qt, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QVBoxLayout, QDialog, QAction, QLineEdit, \
    QMessageBox, QMenu, QProgressBar, QLabel, QFileDialog
from add_history import AddHistory
from camera import Camera, register
from change_department import ChangeDepartment
from change_is_manager import ChangeIsManager
from change_job_id import ChangeJobId
from change_name import ChangeName
from delete_department import DeleteDepartment
from interface.manage_interface import Ui_MainWindow
from database_operation import load_attendance, load_all_name_from_department, load_id_by_name_from_department, \
    load_sign_history, load_people, delete_people_by_job_id, save_history
from add_department import AddDepartment
from rename_department import RenameDepartment
import pandas as pd
import os


def get_row_content(tableWidget, row):
    """
    获取 tableWidget 指定行的内容
    :param tableWidget: QTableWidget 实例
    :param row: 要获取的行号（从0开始）
    :return: 一个列表，包含该行每一列的文本
    """
    row_content = []
    col_count = tableWidget.columnCount()
    for col in range(col_count):
        item = tableWidget.item(row, col)
        # 如果单元格有内容，则获取文本；否则返回空字符串
        text = item.text() if item is not None else ""
        row_content.append(text)
    return row_content

def search(result, text):
    """
    在 result 列表中查找至少有一个字段值包含指定字符串 text 的记录
    :param result: 列表，每个元素是一个字典
    :param text: 要搜索的字符串
    :return: 符合条件的记录列表
    """
    # 对每个字典，检查所有的值中是否存在包含 text 的情况
    return [record for record in result if any(text in str(value) for value in record.values())]

class Manage(QMainWindow, Ui_MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)  # 设置窗体
        self.parent = parent
        action = QAction(QIcon("interface/search.png"), "", self)  # 添加图标
        self.departments = load_all_name_from_department()
        self.sign_history = load_sign_history()
        self.people_info = load_people()
        self.attendance_data = load_attendance(self.calendarWidget.selectedDate().toString("yyyy-MM-dd"))

        # 定义提示框
        self.msg_box = QMessageBox(self)
        self.msg_box.setIcon(QMessageBox.Information)  # 设置图标类型，例如 Information
        self.msg_box.setWindowTitle("提示")  # 设置窗口标题
        self.msg_box.setText("这是一个提示框")  # 主提示信息
        self.msg_box.setStandardButtons(QMessageBox.Ok)
        self.msg_box.button(QMessageBox.Ok).setText("确认")

        # 为工具栏按钮绑定槽函数
        self.actionCount.triggered.connect(self.show_attendance)
        self.actionRegister.triggered.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.actionHistory.triggered.connect(self.show_history)
        self.actionPeople.triggered.connect(self.show_people)

        # 为跳转按钮绑定槽函数
        self.commandLinkButton.clicked.connect(self.goto_main)
        self.commandLinkButton_2.clicked.connect(self.goto_main)
        self.commandLinkButton_3.clicked.connect(self.goto_main)
        self.commandLinkButton_4.clicked.connect(self.goto_main)

        # 第一页界面的初始化
        # 填充出勤统计表，绑定日期切换槽函数
        self.calendarWidget.clicked.connect(self.show_attendance)
        self.calendarWidget.currentPageChanged.connect(self.month_changed)
        self.show_attendance()
        self.lineEdit_3.addAction(action, QLineEdit.LeadingPosition)  # 左侧图标
        self.lineEdit_3.returnPressed.connect(self.on_search_attendance)

        # 第二页界面的初始化
        # 创建摄像头流对象
        self.camera = Camera()
        # 设置定时器来实时更新图像
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.camera.update_image)
        # 将二维画面添加到groupBox里
        layout = QVBoxLayout()
        layout.addWidget(self.camera.canvas)
        self.widget.setLayout(layout)
        # 为人脸注册comboBox初始化
        self.comboBox.addItems(["员工", "管理员"])
        self.comboBox_2.addItems(self.departments)
        # 为人脸注册的确认按钮绑定槽函数
        self.pushButton.clicked.connect(self.register_ok)

        # 第三页界面的初始化
        self.show_history() # 初始化打卡记录表
        self.lineEdit_4.addAction(action, QLineEdit.LeadingPosition)  # 左侧图标
        self.lineEdit_4.returnPressed.connect(self.on_search_history)
        self.pushButton_6.clicked.connect(self.on_add_history)
        self.pushButton_7.clicked.connect(self.on_import_history)
        self.pushButton_8.clicked.connect(self.on_export_history)

        # 第四页界面的初始化
        self.show_people() # 初始化员工信息表
        self.pushButton_3.clicked.connect(self.on_add_department) # 新建部门按钮绑定槽函数
        self.lineEdit_5.addAction(action, QLineEdit.LeadingPosition)  # 左侧图标
        self.lineEdit_5.returnPressed.connect(self.on_search_people)
        self.tableWidget_3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget_3.customContextMenuRequested.connect(self.open_menu)
        self.tableWidget_3.cellDoubleClicked.connect(self.on_update_people)
        self.pushButton_4.clicked.connect(self.on_rename_department)
        self.pushButton_5.clicked.connect(self.on_delete_department)

        # 初始化页面
        self.stackedWidget.setCurrentIndex(0)

    def on_import_history(self):
        # 弹出文件选择对话框
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)", options=options
        )
        
        if not file_path:  # 用户取消了选择
            return
        
        # 提前创建进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("导入进度")
        progress_dialog.setFixedSize(400, 100)
        progress_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        progress_dialog.setModal(True)
        
        # 创建布局
        layout = QVBoxLayout(progress_dialog)
        
        # 添加文本标签
        text_label = QLabel("正在读取Excel文件...", progress_dialog)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        # 添加进度条
        progress_bar = QProgressBar(progress_dialog)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(10)  # 初始进度10%，表示开始读取文件
        progress_bar.setTextVisible(True)
        layout.addWidget(progress_bar)
        
        # 显示对话框
        progress_dialog.show()
        QApplication.processEvents()
            
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, keep_default_na=False)
            
            # 更新进度条和标签，表示文件已读取完成
            progress_bar.setValue(30)
            text_label.setText("验证文件格式...")
            QApplication.processEvents()
            
            # 检查表头
            expected_headers = ["日期", "工号", "姓名", "部门", "签到时间", "签退时间"]
            if not all(header in df.columns for header in expected_headers):
                progress_dialog.close()
                self.msg_box.setText("文件格式错误！表头必须包含：日期，工号，姓名，部门，签到时间，签退时间")
                self.msg_box.exec_()
                return
            
            # 更新进度条和标签，表示开始导入记录    
            progress_bar.setValue(40)
            text_label.setText("正在导入考勤记录...")
            progress_bar.setRange(0, len(df))
            QApplication.processEvents()
            
            # 导入记录
            success_count = 0
            fail_count = 0
            
            for index, row in df.iterrows():
                # 更新进度条，从40%起始点开始计算
                progress_value = 40 + int((index + 1) / len(df) * 60)
                progress_bar.setValue(progress_value)
                QApplication.processEvents()
                
                try:
                    # 获取数据
                    date_str = str(row["日期"]).split()[0]  # 处理可能的时间戳格式
                    job_id = str(row["工号"])
                    sign_in = str(row["签到时间"])
                    sign_out = str(row["签退时间"])
                    
                    # 使用save_history函数保存记录
                    success, message = save_history(date_str, job_id, sign_in, sign_out)
                    
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                        print(f"导入失败: 行 {index+1}, 原因: {message}")
                        
                except Exception as e:
                    fail_count += 1
                    print(f"导入错误: 行 {index+1}, 错误: {str(e)}")
            
            # 完成导入，进度条显示100%
            progress_bar.setValue(100)
            text_label.setText("导入完成！")
            QApplication.processEvents()
            
            # 短暂延迟后关闭对话框
            QTimer.singleShot(500, progress_dialog.close)
            
            # 显示导入结果
            self.msg_box.setText(f"导入完成!\n成功: {success_count} 条记录\n失败: {fail_count} 条记录")
            self.msg_box.exec_()
            
            # 刷新历史记录表
            self.show_history()
            
        except Exception as e:
            # 关闭进度对话框
            progress_dialog.close()
            
            self.msg_box.setText(f"导入失败: {str(e)}")
            self.msg_box.exec_()

    def on_export_history(self):
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹", "")
        
        if not folder_path:  # 用户取消了选择
            return
            
        try:
            # 获取所有考勤记录
            history_data = load_sign_history()
            
            if not history_data:
                self.msg_box.setText("没有可导出的考勤记录")
                self.msg_box.exec_()
                return
                
            # 创建进度对话框
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("导出进度")
            progress_dialog.setFixedSize(400, 100)
            progress_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
            progress_dialog.setModal(True)
            
            # 创建布局
            layout = QVBoxLayout(progress_dialog)
            
            # 添加文本标签
            text_label = QLabel("正在导出考勤记录...", progress_dialog)
            text_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(text_label)
            
            # 添加进度条
            progress_bar = QProgressBar(progress_dialog)
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setTextVisible(True)
            layout.addWidget(progress_bar)
            
            # 显示对话框
            progress_dialog.show()
            QApplication.processEvents()
            
            # 更新进度条到25%，表示开始处理数据
            progress_bar.setValue(25)
            QApplication.processEvents()
            
            # 将记录转换为DataFrame
            df = pd.DataFrame(history_data)
            
            # 设置列顺序
            df = df[["date", "job_id", "name", "department", "sign_in", "sign_out"]]
            
            # 重命名列为中文
            df.columns = ["日期", "工号", "姓名", "部门", "签到时间", "签退时间"]
            
            # 更新进度条到50%，表示数据处理完成
            progress_bar.setValue(50)
            QApplication.processEvents()
            
            # 构建保存路径
            file_path = os.path.join(folder_path, "出勤记录.xlsx")
            
            # 检查文件是否存在，如果存在则为文件名添加(1)、(2)等后缀
            counter = 1
            base_name = "出勤记录"
            while os.path.exists(file_path):
                file_path = os.path.join(folder_path, f"{base_name}({counter}).xlsx")
                counter += 1
            
            # 更新进度条到75%，表示准备写入文件
            progress_bar.setValue(75)
            QApplication.processEvents()
            
            # 将数据写入Excel文件
            df.to_excel(file_path, index=False)
            
            # 完成导出，更新进度条到100%
            progress_bar.setValue(100)
            QApplication.processEvents()
            
            # 关闭进度对话框
            progress_dialog.close()
            
            # 显示导出成功消息
            self.msg_box.setText(f"导出成功!\n文件保存在：{file_path}")
            self.msg_box.exec_()
            
        except Exception as e:
            # 关闭进度对话框（如果已打开）
            if 'progress_dialog' in locals() and progress_dialog.isVisible():
                progress_dialog.close()
                
            self.msg_box.setText(f"导出失败: {str(e)}")
            self.msg_box.exec_()

    def on_add_history(self):
        add_history = AddHistory()
        add_history.exec_()
        self.show_history()

    def on_delete_department(self):
        delete_department = DeleteDepartment()
        delete_department.exec_()
        self.departments = load_all_name_from_department()
        self.comboBox_2.clear()
        self.comboBox_2.addItems(self.departments)
        self.show_attendance()
        self.show_history()
        self.show_people()

    def on_rename_department(self):
        rename_department = RenameDepartment()
        rename_department.exec_()
        self.departments = load_all_name_from_department()
        self.comboBox_2.clear()
        self.comboBox_2.addItems(self.departments)
        self.show_attendance()
        self.show_history()
        self.show_people()

    def on_update_people(self, row, column):
        row_data = get_row_content(self.tableWidget_3, row)
        if column == 0:
            change_job_id = ChangeJobId(row_data)
            change_job_id.exec_()
        elif column == 1:
            change_name = ChangeName(row_data)
            change_name.exec_()
        elif column == 2:
            change_department = ChangeDepartment(row_data)
            change_department.exec_()
        elif column == 3:
            change_is_manager = ChangeIsManager(row_data)
            change_is_manager.exec_()
        self.show_people()
        self.show_attendance()
        self.show_history()
        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidget.setCurrentIndex(3)


    def open_menu(self, pos: QPoint):
        # 将 pos 坐标从 viewport 坐标转换为全局坐标
        global_pos = self.tableWidget_3.viewport().mapToGlobal(pos)
        # 创建右键菜单
        menu = QMenu()
        delete_action = QAction("删除", self.tableWidget_3)
        menu.addAction(delete_action)
        # 当触发删除选项时，调用删除行的方法
        delete_action.triggered.connect(lambda: self.delete_row_at(pos))
        # 弹出菜单
        menu.exec_(global_pos)

    def delete_row_at(self, pos: QPoint):
        # 根据鼠标右键点击位置获取对应的表格索引
        index = self.tableWidget_3.indexAt(pos)
        if index.isValid():
            row = index.row()
            row_data = get_row_content(self.tableWidget_3, row)
            job_id = row_data[0]
            self.tableWidget_3.removeRow(row)
            delete_people_by_job_id(job_id)

    def on_search_attendance(self):
        temp = search(self.attendance_data, self.lineEdit_3.text())
        keys = ["job_id", "name", "department", "day_duration", "attendance_day", "month_duration"]
        self.tableWidget.setRowCount(len(temp))
        for row, record in enumerate(temp):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget.setItem(row, col, item)
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidget.setCurrentIndex(0)

    def on_search_history(self):
        temp = search(self.sign_history, self.lineEdit_4.text())
        keys = ["date", "job_id", "name", "department", "sign_in", "sign_out"]
        self.tableWidget_2.setRowCount(len(temp))
        for row, record in enumerate(temp):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_2.setItem(row, col, item)
        self.tableWidget_2.resizeRowsToContents()
        self.tableWidget_2.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(3)
        self.stackedWidget.setCurrentIndex(2)

    def on_search_people(self):
        temp = search(self.people_info, self.lineEdit_5.text())
        keys = ["job_id", "name", "department", "is_manager"]
        self.tableWidget_3.setRowCount(len(temp))
        for row, record in enumerate(temp):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_3.setItem(row, col, item)
        self.tableWidget_3.resizeRowsToContents()
        self.tableWidget_3.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidget.setCurrentIndex(3)

    def on_add_department(self):
        add_department = AddDepartment()
        add_department.exec_()
        self.departments = load_all_name_from_department()
        self.comboBox_2.clear()
        self.comboBox_2.addItems(self.departments)

    def show_attendance(self):
        self.attendance_data = load_attendance(self.calendarWidget.selectedDate().toString("yyyy-MM-dd"))
        keys = ["job_id", "name", "department", "day_duration", "attendance_day", "month_duration"]
        self.tableWidget.setRowCount(len(self.attendance_data))
        for row, record in enumerate(self.attendance_data):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget.setItem(row, col, item)
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidget.setCurrentIndex(0)

    def show_history(self):
        self.sign_history = load_sign_history()
        keys = ["date", "job_id", "name", "department", "sign_in", "sign_out"]
        self.tableWidget_2.setRowCount(len(self.sign_history))
        for row, record in enumerate(self.sign_history):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_2.setItem(row, col, item)
        self.tableWidget_2.resizeRowsToContents()
        self.tableWidget_2.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(3)
        self.stackedWidget.setCurrentIndex(2)

    def show_people(self):
        self.people_info = load_people()
        keys = ["job_id", "name", "department", "is_manager"]
        self.tableWidget_3.setRowCount(len(self.people_info))
        for row, record in enumerate(self.people_info):
            for col, key in enumerate(keys):
                # 将字典中的值转换为字符串后放入单元格
                item = QTableWidgetItem(str(record[key]))
                self.tableWidget_3.setItem(row, col, item)
        self.tableWidget_3.resizeRowsToContents()
        self.tableWidget_3.resizeColumnsToContents()
        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidget.setCurrentIndex(3)

    def register_ok(self):
        if self.comboBox.currentText() == "管理员":
            is_manager = 1
        else:
            is_manager = 0
        job_id = self.lineEdit.text()
        name = self.lineEdit_2.text()
        if self.comboBox_2.lineEdit().text() in self.departments and job_id and name:
            department_id = load_id_by_name_from_department(self.comboBox_2.currentText())

            # 创建自定义对话框
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("请稍候")
            progress_dialog.setFixedSize(400, 100)
            progress_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
            progress_dialog.setModal(True)
            
            # 创建布局
            layout = QVBoxLayout(progress_dialog)
            
            # 添加文本标签
            text_label = QLabel("正在注册人脸...", progress_dialog)
            text_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(text_label)
            
            # 添加动画进度条
            loading_label = QLabel(progress_dialog)
            loading_label.setAlignment(Qt.AlignCenter)
            
            # 方法一：使用简单的QProgressBar动画
            progress_bar = QProgressBar(progress_dialog)
            progress_bar.setRange(0, 100)  # 设置为确定模式，范围0-100
            progress_bar.setValue(0)       # 初始值为0
            progress_bar.setTextVisible(True)  # 显示百分比文字
            progress_bar.setMinimumHeight(20)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid grey;
                    border-radius: 5px;
                    background-color: #F0F0F0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    margin: 0.5px;
                }
            """)
            layout.addWidget(progress_bar)
            
            # 创建并设置定时器来更新进度条
            self.progress_timer = QTimer()
            self.progress_value = 0
            
            def update_progress():
                if self.progress_value < 95:
                    self.progress_value += 2
                    progress_bar.setValue(self.progress_value)
                QApplication.processEvents()  # 确保UI更新
                
            # 连接定时器和更新函数
            self.progress_timer.timeout.connect(update_progress)
            self.progress_timer.start(100)  # 约7秒内达到95%（168ms更新一次，每次+2%）
            
            # 显示对话框
            progress_dialog.show()
            QApplication.processEvents()
            
            # 创建注册线程
            register_thread = register(job_id, name, department_id, is_manager)
            
            # 注册完成后的回调函数
            def on_register_complete(result):
                # 停止定时器
                self.progress_timer.stop()
                # 完成进度条
                progress_bar.setValue(100)
                QApplication.processEvents()
                
                # 关闭对话框
                progress_dialog.close()
                
                # 显示结果
                if result:
                    self.msg_box.setText("注册成功")
                    self.msg_box.exec_()
                    self.show_people()
                    self.stackedWidget.setCurrentIndex(1)
                else:
                    self.msg_box.setText("注册失败")
                    self.msg_box.exec_()
            
            # 连接信号和回调函数
            register_thread.register_completed.connect(on_register_complete)
            
            # 启动注册线程
            register_thread.start()
        else:
            self.msg_box.setText("注册失败")
            self.msg_box.exec_()

    def month_changed(self, year, month):
        new_date = QDate(year, month, 1)
        self.calendarWidget.setSelectedDate(new_date)
        self.show_attendance()

    def goto_main(self):
        self.hide()
        self.camera_timer.stop()
        self.parent.camera_timer.start(50)
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