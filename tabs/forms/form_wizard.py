# /home/sergey/Documents/configurate/tabs/forms/form_wizard.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QListWidget, QListWidgetItem, QCheckBox,
    QPushButton, QMessageBox, QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from lang.local_translator import LocalTranslator
from database import DatabaseService


class FormWizard(QWizard):
    """Волшебник создания форм"""

    def __init__(self, db, entity_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.entity_id = entity_id
        self.translator = LocalTranslator()

        self.setWindowTitle(self.translator.tr('wizard_title'))
        self.resize(800, 600)

        # Страницы
        self.entity_page = EntitySelectPage(db, self)
        self.type_page = FormTypePage(self)
        self.fields_page = FieldsSelectPage(db, self)

        self.addPage(self.entity_page)
        self.addPage(self.type_page)
        self.addPage(self.fields_page)

        # Если entity_id передан, пропускаем страницу выбора
        if entity_id:
            self.entity_page.entity_id = entity_id
            self.entity_page.load_entity_info()

    def get_result(self):
        """Возвращает результат мастера"""
        return {
            'entity_id': self.entity_page.entity_id,
            'form_type': self.type_page.get_form_type(),
            'form_name': self.type_page.get_form_name(),
            'form_alias': self.type_page.get_form_alias(),
            'selected_fields': self.fields_page.get_selected_fields(),
            'is_grid': self.type_page.is_grid_mode()
        }


class EntitySelectPage(QWizardPage):
    """Страница выбора сущности"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.entity_id = None

        self.setTitle(self.translator.tr('entity_page_title'))
        self.setSubTitle(self.translator.tr('entity_page_subtitle'))

        layout = QVBoxLayout(self)

        self.combo_entity = QComboBox()
        self.combo_entity.currentIndexChanged.connect(self.on_entity_changed)
        layout.addWidget(QLabel(self.translator.tr('select_entity')))
        layout.addWidget(self.combo_entity)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addStretch()

        self.load_entities()

    def load_entities(self):
        """Загружает список сущностей"""
        rows = self.db.execute_query("""
            SELECT id, cname, calias, class_id 
            FROM meta.entitytypes 
            ORDER BY cname
        """)

        self.combo_entity.clear()
        self.combo_entity.addItem(self.translator.tr('select_entity_hint'), None)

        for row in rows:
            eid, cname, calias, class_id = row
            # Определяем класс сущности
            class_res = self.db.execute_query(
                "SELECT calias FROM meta.entity_classes WHERE id = %s", (class_id,)
            )
            class_alias = class_res[0][0] if class_res else "DICT"
            self.combo_entity.addItem(f"{cname} ({calias}) - {class_alias}", eid)

    def on_entity_changed(self, index):
        """При выборе сущности"""
        self.entity_id = self.combo_entity.currentData()
        self.load_entity_info()
        self.completeChanged.emit()

    def load_entity_info(self):
        """Загружает информацию о сущности"""
        if not self.entity_id:
            self.info_label.setText("")
            return

        # Получаем количество полей
        fields_count = self.db.execute_query(
            "SELECT COUNT(*) FROM meta.fields WHERE entitytypeid = %s", (self.entity_id,)
        )
        fields_count = fields_count[0][0] if fields_count else 0

        # Получаем класс сущности
        class_res = self.db.execute_query("""
            SELECT ec.calias, ec.cname 
            FROM meta.entitytypes et
            JOIN meta.entity_classes ec ON et.class_id = ec.id
            WHERE et.id = %s
        """, (self.entity_id,))

        class_info = f"{class_res[0][1]} ({class_res[0][0]})" if class_res else "DICT"

        self.info_label.setText(
            f"{self.translator.tr('entity_info')}:\n"
            f"  • {self.translator.tr('fields_count')}: {fields_count}\n"
            f"  • {self.translator.tr('entity_class')}: {class_info}"
        )

    def isComplete(self):
        return self.entity_id is not None


class FormTypePage(QWizardPage):
    """Страница выбора типа формы"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()

        self.setTitle(self.translator.tr('type_page_title'))
        self.setSubTitle(self.translator.tr('type_page_subtitle'))

        layout = QVBoxLayout(self)

        # Группа выбора типа формы
        group = QGroupBox(self.translator.tr('form_type_group'))
        group_layout = QVBoxLayout(group)

        self.radio_grid = QCheckBox(self.translator.tr('form_type_grid'))
        self.radio_grid.setChecked(True)
        self.radio_grid.toggled.connect(self.on_type_changed)
        group_layout.addWidget(self.radio_grid)

        grid_desc = QLabel(self.translator.tr('form_type_grid_desc'))
        grid_desc.setWordWrap(True)
        grid_desc.setStyleSheet("color: gray; margin-left: 20px;")
        group_layout.addWidget(grid_desc)

        self.radio_edit = QCheckBox(self.translator.tr('form_type_edit'))
        self.radio_edit.toggled.connect(self.on_type_changed)
        group_layout.addWidget(self.radio_edit)

        edit_desc = QLabel(self.translator.tr('form_type_edit_desc'))
        edit_desc.setWordWrap(True)
        edit_desc.setStyleSheet("color: gray; margin-left: 20px;")
        group_layout.addWidget(edit_desc)

        layout.addWidget(group)

        # Название формы
        layout.addSpacing(20)
        layout.addWidget(QLabel(self.translator.tr('form_name_label')))
        self.edit_name = QComboBox()
        self.edit_name.setEditable(True)
        layout.addWidget(self.edit_name)

        layout.addWidget(QLabel(self.translator.tr('form_alias_label')))
        self.edit_alias = QComboBox()
        self.edit_alias.setEditable(True)
        layout.addWidget(self.edit_alias)

        layout.addStretch()

        self.on_type_changed()

    def on_type_changed(self):
        """При изменении типа формы"""
        # Автоматически генерируем имя и алиас
        if self.is_grid_mode():
            prefix = "Список"
            suffix = "grid"
        else:
            prefix = "Карточка"
            suffix = "edit"

        if self.edit_name.currentText():
            base = self.edit_name.currentText().split()[
                0] if ' ' in self.edit_name.currentText() else self.edit_name.currentText()
        else:
            base = "Entity"

        self.edit_name.setEditText(f"{prefix} {base}")
        self.edit_alias.setEditText(f"{base.lower()}_{suffix}")

    def is_grid_mode(self):
        return self.radio_grid.isChecked()

    def get_form_type(self):
        return "grid" if self.is_grid_mode() else "edit"

    def get_form_name(self):
        return self.edit_name.currentText()

    def get_form_alias(self):
        return self.edit_alias.currentText()

    def set_entity_name(self, entity_name):
        """Устанавливает имя сущности для генерации названия"""
        if self.edit_name.currentText() == "":
            self.edit_name.addItem(entity_name)
            self.edit_alias.addItem(entity_name.lower().replace(' ', '_'))
            self.on_type_changed()


class FieldsSelectPage(QWizardPage):
    """Страница выбора полей для отображения"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.entity_id = None

        self.setTitle(self.translator.tr('fields_page_title'))
        self.setSubTitle(self.translator.tr('fields_page_subtitle'))

        layout = QVBoxLayout(self)

        # Кнопки выделения
        btn_layout = QHBoxLayout()
        self.btn_all = QPushButton(self.translator.tr('select_all'))
        self.btn_all.clicked.connect(self.select_all)
        self.btn_none = QPushButton(self.translator.tr('deselect_all'))
        self.btn_none.clicked.connect(self.select_none)
        btn_layout.addWidget(self.btn_all)
        btn_layout.addWidget(self.btn_none)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Список полей
        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.fields_list)

        layout.addStretch()

    def initializePage(self):
        """Загружает поля сущности"""
        wizard = self.wizard()
        if hasattr(wizard, 'entity_page'):
            self.entity_id = wizard.entity_page.entity_id

        if self.entity_id:
            self.load_fields()

    def load_fields(self):
        """Загружает поля сущности"""
        self.fields_list.clear()

        rows = self.db.execute_query("""
            SELECT f.cfieldname, f.calias, f.cfieldtype, f.lisrequired
            FROM meta.fields f
            WHERE f.entitytypeid = %s AND f.is_system = false
            ORDER BY f.isortorder
        """, (self.entity_id,))

        for row in rows:
            cfieldname, calias, cfieldtype, is_required = row
            text = f"{calias} ({cfieldname}) [{cfieldtype}]"
            if is_required:
                text += " *"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, cfieldname)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.fields_list.addItem(item)

    def select_all(self):
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setCheckState(Qt.Checked)

    def select_none(self):
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setCheckState(Qt.Unchecked)

    def get_selected_fields(self):
        """Возвращает список выбранных полей"""
        fields = []
        for i in range(self.fields_list.count()):
            item = self.fields_list.item(i)
            if item.checkState() == Qt.Checked:
                fields.append(item.data(Qt.UserRole))
        return fields