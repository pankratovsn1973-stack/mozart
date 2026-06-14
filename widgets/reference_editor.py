#reference_editor.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QToolButton, QMessageBox
from PySide6.QtCore import Signal
from database import DatabaseService
from lang.local_translator import LocalTranslator


class ReferenceEditor(QWidget):
    valueChanged = Signal(object)

    def __init__(self, parent=None, table_name=None, display_field='cname',
                 id_field='id', dialog=None, db=None):
        super().__init__(parent)
        self.table_name = table_name
        self.display_field = display_field
        self.id_field = id_field
        self.dialog = dialog
        self.db = db or DatabaseService()
        self.current_id = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        layout.addWidget(self.line_edit)

        self.btn_select = QToolButton()
        self.btn_select.setText("📁")
        self.btn_select.clicked.connect(self.select_value)
        layout.addWidget(self.btn_select)

        self.btn_clear = QToolButton()
        self.btn_clear.setText("✖")
        self.btn_clear.clicked.connect(self.clear_value)
        layout.addWidget(self.btn_clear)

    def set_value(self, item_id, display_text=None):
        self.current_id = item_id
        if display_text is not None:
            self.line_edit.setText(display_text)
        else:
            self.line_edit.setText(str(item_id) if item_id else "")
        self.valueChanged.emit(item_id)

    def get_value(self):
        return self.current_id

    def setReadOnly(self, ro):
        self.btn_select.setEnabled(not ro)
        self.btn_clear.setEnabled(not ro)

    def select_value(self):
        if not self.table_name:
            QMessageBox.warning(self, translator.tr("error"), "Не указана таблица-источник")
            return
        if self.dialog:
            dlg = self.dialog(self.table_name, self.display_field, self.id_field, db=self.db)
        else:
            from widgets.reference_selector import ReferenceSelector
            dlg = ReferenceSelector(self.table_name, self.display_field, self.id_field, db=self.db, parent=self)
        if dlg.exec_():
            selected_id, selected_display = dlg.get_selected()
            if selected_id:
                self.set_value(selected_id, selected_display)

    def clear_value(self):
        self.set_value(None, "")