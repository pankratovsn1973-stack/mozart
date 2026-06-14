# widgets/form_designer_old/code_editor.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton
from PySide6.QtCore import Qt


class CodeEditorDialog(QDialog):
    """Диалог редактирования кода метода"""

    def __init__(self, method_name, current_code="", parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.setWindowTitle(f"Редактирование метода: {method_name}")
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit()
        self.editor.setPlainText(current_code)
        self.editor.setFont(self._get_mono_font())
        layout.addWidget(self.editor)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _get_mono_font(self):
        from PySide6.QtGui import QFont
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.Monospace)
        return font

    def get_code(self):
        return self.editor.toPlainText()