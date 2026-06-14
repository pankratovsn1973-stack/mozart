
# crud_buttons.py
# crud_buttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal
from lang.local_translator import LocalTranslator

class CrudButtons(QWidget):
    add_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent=None, with_add=True, with_edit=True, with_delete=True):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.with_add = with_add
        self.with_edit = with_edit
        self.with_delete = with_delete
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if with_add:
            self.btn_add = QPushButton()
            self.btn_add.clicked.connect(self.add_clicked.emit)
            layout.addWidget(self.btn_add)

        if with_edit:
            self.btn_edit = QPushButton()
            self.btn_edit.clicked.connect(self.edit_clicked.emit)
            layout.addWidget(self.btn_edit)

        if with_delete:
            self.btn_del = QPushButton()
            self.btn_del.clicked.connect(self.delete_clicked.emit)
            layout.addWidget(self.btn_del)

        layout.addStretch()
        self.retranslate_ui()

    def retranslate_ui(self):
        if self.with_add and hasattr(self, 'btn_add'):
            self.btn_add.setText(self.translator.tr('btn_add'))
        if self.with_edit and hasattr(self, 'btn_edit'):
            self.btn_edit.setText(self.translator.tr('btn_edit'))
        if self.with_delete and hasattr(self, 'btn_del'):
            self.btn_del.setText(self.translator.tr('btn_delete'))