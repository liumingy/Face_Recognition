from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import QDate, QTime
from database_operation import load_name_department_by_job_id_from_people, save_history
from interface.add_history_dialog import Ui_Dialog

class AddHistory(Ui_Dialog, QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 初始化日期为当前日期
        self.dateEdit.setDate(QDate.currentDate())
        
        # 初始化时间
        current_time = QTime.currentTime()
        self.timeEdit.setTime(current_time)
        self.timeEdit_2.setTime(current_time.addSecs(3600))  # 默认签退时间比签到时间晚1小时
        
        # 设置工号输入框
        self.lineEdit.setPlaceholderText("请输入工号")
        self.lineEdit.returnPressed.connect(self.check_job_id)
        self.lineEdit.editingFinished.connect(self.check_job_id)
        
        # 绑定按钮事件
        self.pushButton.clicked.connect(self.on_accept)
        self.pushButton_2.clicked.connect(self.on_reject)
        
        # 创建消息框
        self.msg_box = QMessageBox()
        self.msg_box.setWindowTitle("提示")
        self.msg_box.setIcon(QMessageBox.Information)
        self.msg_box.setStandardButtons(QMessageBox.Ok)

    def check_job_id(self):
        """当用户输入工号后，验证并填充员工信息"""
        job_id = self.lineEdit.text().strip()
        if job_id:
            try:
                # 尝试将输入转换为整数
                job_id = int(job_id)
                # 查询员工信息
                name, department = load_name_department_by_job_id_from_people(job_id)
                if name and department:
                    # 如果找到员工信息，则填充到标签中
                    self.label.setText(name)
                    self.label_2.setText(department)
                else:
                    # 未找到员工信息
                    self.label.setText("未找到员工")
                    self.label_2.setText("未知部门")
            except ValueError:
                # 输入不是有效的整数
                self.label.setText("无效工号")
                self.label_2.setText("未知部门")

    def on_accept(self):
        """确认添加历史记录"""
        # 获取表单数据
        job_id = self.lineEdit.text().strip()
        if not job_id:
            self.show_message("请输入工号")
            return
            
        try:
            job_id = int(job_id)
        except ValueError:
            self.show_message("工号必须是数字")
            return
            
        # 获取并格式化日期
        date_str = self.dateEdit.date().toString("yyyy-MM-dd")
        
        # 获取并格式化时间
        sign_in = self.timeEdit.time().toString("HH:mm")
        sign_out = self.timeEdit_2.time().toString("HH:mm")
        
        # 检查输入的员工姓名是否有效
        if self.label.text() == "未找到员工" or self.label.text() == "无效工号" or not self.label.text():
            self.show_message("请输入有效的工号")
            return
            
        # 验证签到时间和签退时间
        sign_in_time = self.timeEdit.time()
        sign_out_time = self.timeEdit_2.time()
        
        if sign_in_time >= sign_out_time:
            self.show_message("签退时间必须晚于签到时间")
            return
            
        # 添加历史记录
        success, message = save_history(date_str, job_id, sign_in, sign_out)
        
        if success:
            self.show_message("记录添加成功")
            self.accept()  # 关闭对话框
        else:
            self.show_message(f"添加失败: {message}")

    def show_message(self, message):
        """显示消息框"""
        self.msg_box.setText(message)
        self.msg_box.exec_()

    def on_reject(self):
        self.reject()

