from PyQt5.QtWidgets import QDialog
from database_operation import save_ins_to_department, update_people, load_id_by_name_from_department
from interface.edit_dialog import Ui_Dialog

class ChangeName(Ui_Dialog, QDialog):
    def __init__(self, info):
        super().__init__()
        self.setupUi(self)
        self.info = info

        self.lineEdit.setPlaceholderText("请输入姓名")
        self.lineEdit.returnPressed.connect(self.on_accept)
        self.pushButton.clicked.connect(self.on_accept)
        self.pushButton_2.clicked.connect(self.on_reject)

    def on_accept(self):
        name = self.lineEdit.text()
        department_id = load_id_by_name_from_department(self.info[2])
        if self.info[3] == "管理员":
            is_manager = 1
        else:
            is_manager = 0
        update_people(self.info[0], self.info[0], name, department_id, is_manager)
        self.accept()

    def on_reject(self):
        self.reject()

