# ide_field_edit.py
# -*- coding: utf-8 -*-

import sys
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,                              QComboBox, QCheckBox, QPushButton, QHBoxLayout, QLabel,                              QTextEdit, QMessageBox)
from PySide6.QtCore import Qt
from ide_core import goProject
from widgets import ReferenceEditor
from database import DatabaseService
from lang.local_translator import LocalTranslator

# Список служебных полей, которые нельзя редактировать и удалять
SYSTEM_FIELDS = ('sourceid', 'data_hash')


class FieldEditDialog(QDialog):
    def __init__(self, field_data=None, status_id=None, read_only_mode=False, is_system=False, db=None):
        super().__init__()
        self.setWindowTitle(translator.tr("title_field_properties"))
        self.setFixedSize(600, 550)

        # Данные: [Имя, ТипКод, Алиас, Описание, Len, Dec, Idx, RefID, Status, is_system, ref_class_id]
        if not field_data:
            self.data = ["new_field", "C", "Новое поле", "", 255, 0, False, None, 1, is_system, None]
        else:
            self.data = field_data
            if len(self.data) < 11:
                self.data.append(None)  # ref_class_id

        self.status_id = status_id or self.data[8] if len(self.data) > 8 else 1
        self.is_system = is_system or (len(self.data) > 9 and self.data[9]) or False
        self.ref_class_id = self.data[10] if len(self.data) > 10 else None
        self.db = db or DatabaseService()

        # Служебные поля всегда только для чтения
        read_only_mode = read_only_mode or self.is_system

        self.read_only_mode = read_only_mode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_name = QLineEdit(str(self.data[0]))
        self.edit_name.textChanged.connect(self.validate_field_name)
        form.addRow("Имя поля (SQL):", self.edit_name)

        self.combo_type = QComboBox()
        types = goProject.f_Execute("SELECT cname, ccode FROM meta.field_types ORDER BY cname")
        for name, code in types:
            self.combo_type.addItem(name, code)

        idx = self.combo_type.findData(str(self.data[1]))
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.combo_type.currentIndexChanged.connect(self.on_type_changed)
        form.addRow("Тип данных:", self.combo_type)

        self.edit_alias = QLineEdit(str(self.data[2]))
        form.addRow("Бизнес-алиас:", self.edit_alias)

        self.edit_comment = QTextEdit()
        self.edit_comment.setPlainText(str(self.data[3]) if self.data[3] else "")
        self.edit_comment.setMaximumHeight(100)
        form.addRow("Описание:", self.edit_comment)

        # Ссылка на другую сущность (ReferenceEditor) - для типа R
        self.ref_editor = ReferenceEditor(
            table_name='meta.entitytypes',
            display_field='cname',
            db=self.db
        )
        if len(self.data) > 7 and self.data[7] and str(self.data[7]).isdigit():
            ref_id = int(self.data[7])
            res = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (ref_id,))
            if res:
                self.ref_editor.set_value(ref_id, res[0][0])
        form.addRow("Ссылается на (Ref):", self.ref_editor)

        # Информация о классе сущности (для ссылочных полей без конкретной цели)
        self.class_info_label = QLabel()
        self.class_info_label.setWordWrap(True)
        self.class_info_label.setStyleSheet("color: gray; font-style: italic;")
        form.addRow("", self.class_info_label)

        # Кнопка выбора целевой сущности для ссылочных полей (если ref_class_id задан)
        self.btn_choose_ref = QPushButton("Выбрать целевую сущность")
        self.btn_choose_ref.clicked.connect(self.choose_target_entity)
        self.btn_choose_ref.setVisible(False)
        form.addRow("", self.btn_choose_ref)

        self.edit_len = QLineEdit(str(self.data[4]))
        form.addRow("Длина (Len):", self.edit_len)

        self.edit_dec = QLineEdit(str(self.data[5]))
        form.addRow("Точность (Dec):", self.edit_dec)

        self.chk_idx = QCheckBox("Создать индекс в БД")
        val_idx = self.data[6]
        self.chk_idx.setChecked(str(val_idx).lower() == 'true' or val_idx is True)
        form.addRow(self.chk_idx)

        # Статус
        self.combo_status = QComboBox()
        statuses = self.db.execute_query("SELECT id, name FROM meta.object_statuses ORDER BY id")
        for sid, sname in statuses:
            self.combo_status.addItem(sname, sid)
        if self.status_id:
            idx_status = self.combo_status.findData(self.status_id)
            if idx_status >= 0:
                self.combo_status.setCurrentIndex(idx_status)
        form.addRow("Статус:", self.combo_status)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Принять")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        self.on_type_changed()
        self.update_class_info()

        # Блокировка для PROD и для служебных полей
        if self.read_only_mode or self.status_id == 2 or self.is_system:
            self.edit_name.setEnabled(False)
            self.combo_type.setEnabled(False)
            self.edit_alias.setEnabled(False)
            self.edit_len.setEnabled(False)
            self.edit_dec.setEnabled(False)
            self.ref_editor.setReadOnly(True)
            self.btn_choose_ref.setEnabled(False)
            self.edit_comment.setEnabled(False if self.is_system else True)
            self.chk_idx.setEnabled(False if self.is_system else True)
            self.combo_status.setEnabled(True)

        # Для служебных полей дополнительно блокируем статус
        if self.is_system:
            self.combo_status.setEnabled(False)
            self.setWindowTitle("Свойства поля (служебное) - только для просмотра")

    def update_class_info(self):
        """Обновляет информацию о классе сущности для ссылочного поля."""
        if self.ref_class_id:
            res = self.db.execute_query(
                "SELECT cname, calias FROM meta.entity_classes WHERE id=%s",
                (self.ref_class_id,)
            )
            if res:
                class_name = res[0][0]
                class_alias = res[0][1]
                self.class_info_label.setText(
                    f"Это ссылочное поле класса «{class_name} ({class_alias})».\n"
                    f"Выберите целевую сущность из этого класса для завершения настройки."
                )
                self.btn_choose_ref.setVisible(True)
            else:
                self.class_info_label.setText("Класс сущности не найден.")
        else:
            self.class_info_label.setText("")
            self.btn_choose_ref.setVisible(False)

    def choose_target_entity(self):
        """Открывает диалог выбора целевой сущности для ссылочного поля."""
        if not self.ref_class_id:
            return

        # Получаем список сущностей указанного класса
        entities = self.db.execute_query(
            "SELECT id, cname, calias FROM meta.entitytypes WHERE class_id = %s ORDER BY cname",
            (self.ref_class_id,)
        )
        if not entities:
            QMessageBox.warning(self, translator.tr("warning"),
                                f"Нет сущностей класса с id={self.ref_class_id}")
            return

        from widgets.reference_selector import ReferenceSelector
        # Временная таблица для селектора
        dlg = ReferenceSelector(
            table_name='meta.entitytypes',
            display_field='cname',
            id_field='id',
            db=self.db,
            parent=self
        )
        # В ReferenceSelector нет фильтрации по классу, поэтому после загрузки отфильтруем
        dlg.table.setRowCount(0)
        for eid, cname, calias in entities:
            row = dlg.table.rowCount()
            dlg.table.insertRow(row)
            dlg.table.setItem(row, 0, QTableWidgetItem(str(eid)))
            dlg.table.setItem(row, 1, QTableWidgetItem(f"{cname} ({calias})"))
            dlg.table.item(row, 0).setData(Qt.UserRole, eid)

        if dlg.exec_():
            selected_id, selected_display = dlg.get_selected()
            if selected_id:
                self.ref_editor.set_value(selected_id, selected_display)
                QMessageBox.information(self, translator.tr("info"),
                                        f"Целевая сущность установлена: {selected_display}")

    def validate_field_name(self, text):
        if not text:
            self.edit_name.setStyleSheet("")
            return
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', text):
            self.edit_name.setStyleSheet("")
        else:
            self.edit_name.setStyleSheet("border: 1px solid red;")

    def on_type_changed(self):
        t = self.combo_type.currentData()
        self.edit_len.setEnabled(t in ('C', 'N'))
        self.edit_dec.setEnabled(t == 'N')
        is_ref = (t == 'R')
        self.ref_editor.setEnabled(is_ref)
        self.btn_choose_ref.setVisible(is_ref and self.ref_class_id is not None)
        self.chk_idx.setEnabled(t not in ('G', 'V', 'F', 'M'))

    def get_data(self):
        return [
            self.edit_name.text(),
            self.combo_type.currentData(),
            self.edit_alias.text(),
            self.edit_comment.toPlainText(),
            int(self.edit_len.text() if self.edit_len.text().isdigit() else 0),
            int(self.edit_dec.text() if self.edit_dec.text().isdigit() else 0),
            self.chk_idx.isChecked(),
            self.ref_editor.get_value(),
            self.combo_status.currentData(),
            self.is_system,
            self.ref_class_id
        ]