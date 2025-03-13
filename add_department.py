from PyQt5.QtWidgets import QDialog
from database_operation import save_ins_to_department
from interface.edit_dialog import Ui_Dialog

class AddDepartment(Ui_Dialog, QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.lineEdit.setPlaceholderText("请输入部门名称")
        self.lineEdit.returnPressed.connect(self.on_accept)
        self.pushButton.clicked.connect(self.on_accept)
        self.pushButton_2.clicked.connect(self.on_reject)

    def on_accept(self):
        name = self.lineEdit.text()
        save_ins_to_department(name)
        self.accept()

    def on_reject(self):
        self.reject()

