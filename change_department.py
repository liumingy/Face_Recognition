from PyQt5.QtWidgets import QDialog, QMessageBox
from database_operation import update_people, load_id_by_name_from_department, load_all_name_from_department
from interface.choose_dialog import Ui_Dialog

class ChangeDepartment(Ui_Dialog, QDialog):
    def __init__(self, info):
        super().__init__()
        self.setupUi(self)
        self.info = info

        self.departments = load_all_name_from_department()
        self.comboBox.addItems(self.departments)
        self.pushButton.clicked.connect(self.on_accept)
        self.pushButton_2.clicked.connect(self.on_reject)

    def on_accept(self):
        if self.comboBox.lineEdit().text() in self.departments:
            department_id = load_id_by_name_from_department(self.comboBox.currentText())
            if self.info[3] == "管理员":
                is_manager = 1
            else:
                is_manager = 0
            update_people(self.info[0], self.info[0], self.info[1], department_id, is_manager)
            self.accept()
        else:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)  # 设置图标类型，例如 Information
            msg_box.setWindowTitle("提示")  # 设置窗口标题
            msg_box.setText("请选择正确的部门名称")  # 主提示信息
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setText("确认")
            msg_box.exec_()

    def on_reject(self):
        self.reject()

