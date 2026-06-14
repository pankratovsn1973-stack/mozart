# /home/sergey/Documents/configurate/tabs/visual_forms_tab.py
# -*- coding: utf-8 -*-
# Вкладка с визуальным редактором форм (замена старому FormElementsWidget)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from widgets.visual_form_editor import VisualFormEditor


class VisualFormsTab(QWidget):
    """
    Вкладка для редактирования формы с визуальным дизайнером.
    Используется в диалоге свойств формы вместо FormElementsWidget.
    """

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db
        self.form_id = form_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = VisualFormEditor(self, db=db, form_id=form_id)
        layout.addWidget(self.editor)

    def set_form_id(self, form_id):
        """Устанавливает ID формы и загружает её контролы"""
        self.form_id = form_id
        self.editor.set_form_id(form_id)