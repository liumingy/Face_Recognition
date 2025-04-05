from PyQt5.QtWidgets import QDialog
from database_operation import update_department, load_all_name_from_department
from interface.choose_edit_dialog import Ui_Dialog

class RenameDepartment(Ui_Dialog, QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.departments = load_all_name_from_department()
        self.comboBox.addItems(self.departments)
        self.lineEdit.setPlaceholderText("请输入部门名称")
        self.lineEdit.returnPressed.connect(self.on_accept)
        self.pushButton.clicked.connect(self.on_accept)
        self.pushButton_2.clicked.connect(self.on_reject)

    def on_accept(self):
        old_name = self.comboBox.currentText()
        new_name = self.lineEdit.text()
        update_department(old_name, new_name)
        self.accept()

    def on_reject(self):
        self.reject()

