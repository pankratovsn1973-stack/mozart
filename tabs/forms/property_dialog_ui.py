# tabs/forms/property_dialog_ui.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QWidget
from lang.local_translator import LocalTranslator
from widgets import ReferenceEditor
from widgets.visual_form_editor import VisualFormEditor


class PropertyDialogUI(QDialog):
    """Базовый UI-класс диалога, отвечающий только за создание виджетов и верстку."""

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.db = db
        self.form_id = form_id

        self.setWindowTitle(self.translator.tr('title_form_properties'))
        self.resize(1400, 900)
        self._setup_layout()

    def _setup_layout(self):
        layout = QVBoxLayout(self)

        # Верхняя панель свойств бланка
        props_widget = QWidget()
        props_layout = QHBoxLayout(props_widget)
        props_layout.setContentsMargins(5, 5, 5, 5)

        form = QFormLayout()
        form.setSpacing(10)

        self.edit_cname = QLineEdit()
        self.edit_cname.setPlaceholderText("Наименование формы")
        form.addRow(self.translator.tr('field_name') + ":", self.edit_cname)

        self.edit_calias = QLineEdit()
        self.edit_calias.setPlaceholderText("system_alias")
        form.addRow(self.translator.tr('field_alias') + ":", self.edit_calias)

        self.ref_entity = ReferenceEditor(
            table_name='meta.entitytypes',
            display_field='cname',
            db=self.db
        )
        form.addRow(self.translator.tr('field_entity') + ":", self.ref_entity)

        props_layout.addLayout(form)
        props_layout.addStretch()
        layout.addWidget(props_widget)

        # Центр: Холст визуального дизайнера форм
        self.designer = VisualFormEditor(self, db=self.db, form_id=self.form_id)
        layout.addWidget(self.designer, 1)

        # Низ: Системные кнопки диалога
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
