# -*- coding: utf-8 -*-
# dialogs/property_meta_edit_dialog.py
"""
Диалог редактирования МЕТАДАННЫХ свойства (не значения).

Позволяет:
  - изменить ui_label_ru, editor_type, qt_target, translation_strategy;
  - изменить type (0-8);
  - переопределить bridgecalcset / bridgecalcget / fuuncselectionvalue;
  - изменить typesourcevalue, isdefaultepr;
  - изменить c_name (с проверкой уникальности в пределах родителя);
  - загрузить BLOB (пиктограмму, изображение).

Диалог НЕ пишет в модель напрямую. Он возвращает dict через get_data();
ClassEditDialog._on_prop_add / _on_prop_edit передаёт этот dict
в ObjectPropertyCollection.add_property / rename_property / set_property_meta /
set_blob — и только там эмитится change_log.

Логика имени (c_name):
  - унаследовано (owner_version_id != current_version_id) — readonly;
  - создано в текущем объекте, но есть потомки — readonly;
  - создано в текущем объекте, потомков нет — editable (с предупреждением).
"""
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QMessageBox, QDialogButtonBox, QGroupBox,
    QTextEdit
)
from PySide6.QtCore import Qt


EDITOR_TYPES = [
    ('text', 'Текст'),
    ('number', 'Число'),
    ('boolean', 'Логический'),
    ('color', 'Цвет'),
    ('choice', 'Выбор из списка'),
    ('json', 'JSON'),
    ('font', 'Шрифт'),
    ('image', 'Изображение'),
    ('list_items', 'Список элементов'),
    ('entity_ref', 'Ссылка на сущность'),
    ('field_ref', 'Ссылка на поле'),
    ('form_ref', 'Ссылка на форму'),
    ('geometry', 'Геометрия'),
]

TRANSLATION_STRATEGIES = [
    ('DIRECT', 'Прямая'),
    ('CSS', 'CSS'),
    ('GEOMETRY', 'Геометрия'),
    ('CUSTOM', 'Кастомная'),
    ('JSON_MAP', 'JSON-маппинг'),
]

TYPESOURCE_VALUES = [
    ('FONTS', 'Шрифты'),
    ('ENTITY', 'Сущность'),
    ('LIST', 'Список'),
    ('FORM', 'Форма'),
    ('GEOMETRY', 'Геометрия'),
    ('COLOR', 'Цвет'),
    ('IMAGE', 'Изображение'),
]

TYPE_VALUES = [
    (0, 'Text'),
    (1, 'Int'),
    (2, 'Float'),
    (3, 'Boolean'),
    (4, 'Color'),
    (5, 'Font'),
    (6, 'Enum'),
    (7, 'JSON'),
    (8, 'Resource'),
]


class PropertyMetaEditDialog(QDialog):
    """
    Диалог редактирования метаданных свойства.

    Параметры:
        element_id — ID элемента (root или подобъект)
        cname — имя свойства (если редактирование существующего)
        prop — ObjectProperty (если редактирование) или None (если новое)
        version_id — текущий id_class_version (для owner_version_id)
        has_children — есть ли потомки у текущего объекта (для смены имени)
        db — DatabaseService
        superlibre — экземпляр SuperLibre (для combo функций)
        class_methods — список имён методов класса (для combo)
        mode — 'add' | 'edit'
    """

    def __init__(
        self,
        parent=None,
        element_id: int = -1,
        cname: str = '',
        prop=None,
        version_id: int = -1,
        has_children: bool = False,
        db=None,
        superlibre=None,
        class_methods: Optional[list] = None,
        mode: str = 'edit',
    ):
        super().__init__(parent)
        self.element_id = element_id
        self.cname = cname
        self.prop = prop
        self.version_id = version_id
        self.has_children = has_children
        self.db = db
        self.superlibre = superlibre
        self.class_methods = class_methods or []
        self.mode = mode

        self._blob_data: Optional[bytes] = None
        self._blob_name: Optional[str] = None
        self._blob_removed = False

        self.setWindowTitle(
            f"Свойства свойства: {cname}" if mode == 'edit' else "Новое свойство"
        )
        self.resize(650, 750)
        self._setup_ui()
        self._load_data()

    # =====================================================================
    # UI
    # =====================================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Имя свойства ---
        form_name = QFormLayout()
        self.edit_cname = QLineEdit()
        self.edit_cname.setPlaceholderText("c_back_color")
        self.lbl_cname_hint = QLabel()
        self.lbl_cname_hint.setStyleSheet("color: #888; font-size: 10px;")
        form_name.addRow("Имя свойства (c_name):", self.edit_cname)
        form_name.addRow("", self.lbl_cname_hint)
        layout.addLayout(form_name)

        # --- Общие метаданные ---
        group_common = QGroupBox("Метаданные")
        form_common = QFormLayout(group_common)

        self.edit_ui_label = QLineEdit()
        form_common.addRow("UI-метка (ui_label_ru):", self.edit_ui_label)

        self.combo_editor = QComboBox()
        for code, label in EDITOR_TYPES:
            self.combo_editor.addItem(label, code)
        form_common.addRow("Редактор (editor_type):", self.combo_editor)

        self.edit_qt_target = QLineEdit()
        form_common.addRow("Qt-target (qt_target):", self.edit_qt_target)

        self.combo_strategy = QComboBox()
        for code, label in TRANSLATION_STRATEGIES:
            self.combo_strategy.addItem(label, code)
        form_common.addRow("Стратегия (translation_strategy):", self.combo_strategy)

        self.combo_type = QComboBox()
        for code, label in TYPE_VALUES:
            self.combo_type.addItem(f"{code} — {label}", code)
        form_common.addRow("Тип (type):", self.combo_type)

        self.combo_typesource = QComboBox()
        self.combo_typesource.addItem("— не задано —", None)
        for code, label in TYPESOURCE_VALUES:
            self.combo_typesource.addItem(label, code)
        form_common.addRow("Источник (typesourcevalue):", self.combo_typesource)

        self.chk_isdefaultepr = QCheckBox("Обязательно для потомков (isdefaultepr)")
        form_common.addRow(self.chk_isdefaultepr)

        layout.addWidget(group_common)

        # --- Мосты ---
        group_bridges = QGroupBox("Функции моста")
        form_bridges = QFormLayout(group_bridges)

        self.combo_bridgecalcset = self._make_function_combo()
        form_bridges.addRow("bridgecalcset:", self.combo_bridgecalcset)

        self.combo_bridgecalcget = self._make_function_combo()
        form_bridges.addRow("bridgecalcget:", self.combo_bridgecalcget)

        self.combo_fuuncselectionvalue = self._make_function_combo()
        form_bridges.addRow("fuuncselectionvalue:", self.combo_fuuncselectionvalue)

        layout.addWidget(group_bridges)

        # --- BLOB ---
        group_blob = QGroupBox("BLOB (пиктограмма, изображение)")
        blob_layout = QVBoxLayout(group_blob)

        self.lbl_blob_status = QLabel("— BLOB не задан —")
        self.lbl_blob_status.setStyleSheet("color: #666;")
        blob_layout.addWidget(self.lbl_blob_status)

        blob_btn_layout = QHBoxLayout()
        self.btn_load_blob = QPushButton("📂 Загрузить изображение")
        self.btn_load_blob.clicked.connect(self._on_load_blob)
        blob_btn_layout.addWidget(self.btn_load_blob)

        self.btn_remove_blob = QPushButton("🗑️ Удалить BLOB")
        self.btn_remove_blob.clicked.connect(self._on_remove_blob)
        self.btn_remove_blob.setEnabled(False)
        blob_btn_layout.addWidget(self.btn_remove_blob)

        blob_btn_layout.addStretch()
        blob_layout.addLayout(blob_btn_layout)

        layout.addWidget(group_blob)

        # --- Кнопки ---
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText("Сохранить")
        btn_box.button(QDialogButtonBox.Cancel).setText("Отмена")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _make_function_combo(self) -> QComboBox:
        """Combo с автодополнением: SuperLibre + методы класса + свободный ввод."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItem("— не задано —", "")

        if self.superlibre is not None:
            names = [n for n in dir(self.superlibre)
                     if not n.startswith('_')
                     and callable(getattr(self.superlibre, n, None))]
            for n in sorted(names):
                combo.addItem(f"SuperLibre: {n}", n)

        for m in sorted(self.class_methods):
            combo.addItem(f"Метод класса: {m}", m)

        return combo

    # =====================================================================
    # Заполнение данных
    # =====================================================================
    def _load_data(self):
        if self.mode == 'edit' and self.prop is not None:
            self.edit_cname.setText(self.prop.cname or '')
            self.edit_ui_label.setText(self.prop.ui_label_ru or '')
            self.edit_qt_target.setText(self.prop.qt_target or '')

            idx = self.combo_editor.findData(self.prop.editor_type)
            if idx >= 0:
                self.combo_editor.setCurrentIndex(idx)
            else:
                self.combo_editor.setCurrentIndex(-1)

            idx = self.combo_strategy.findData(self.prop.translation_strategy)
            if idx >= 0:
                self.combo_strategy.setCurrentIndex(idx)

            idx = self.combo_type.findData(self.prop.typevalue)
            if idx >= 0:
                self.combo_type.setCurrentIndex(idx)

            idx = self.combo_typesource.findData(self.prop.typesourcevalue)
            if idx >= 0:
                self.combo_typesource.setCurrentIndex(idx)

            self.chk_isdefaultepr.setChecked(bool(self.prop.isdefaultepr))

            self._set_combo_value(self.combo_bridgecalcset, self.prop.bridgecalcset)
            self._set_combo_value(self.combo_bridgecalcget, self.prop.bridgecalcget)
            self._set_combo_value(
                self.combo_fuuncselectionvalue, self.prop.fuuncselectionvalue
            )

            if self.prop.is_blob and self.prop.blob_value:
                self._blob_data = self.prop.blob_value
                self._blob_name = self.prop.blob_name
                self.lbl_blob_status.setText(
                    f"BLOB: {self.prop.blob_name or 'без имени'} "
                    f"({len(self.prop.blob_value)} байт)"
                )
                self.btn_remove_blob.setEnabled(True)

            self._apply_cname_logic()
        else:
            self.edit_cname.setEnabled(True)
            self.lbl_cname_hint.setText("Имя нового свойства")
            self.combo_type.setCurrentIndex(0)
            self.chk_isdefaultepr.setChecked(False)

    def _set_combo_value(self, combo: QComboBox, value: Optional[str]):
        if not value:
            combo.setCurrentIndex(0)
            return
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(value)

    def _apply_cname_logic(self):
        """Логика readonly/editable для c_name."""
        if self.prop is None:
            self.edit_cname.setEnabled(True)
            return

        owner_vid = getattr(self.prop, 'owner_version_id', None)
        is_inherited = (owner_vid is not None and owner_vid != self.version_id)

        if is_inherited:
            self.edit_cname.setEnabled(False)
            self.lbl_cname_hint.setText(
                "Унаследовано от предка — имя менять нельзя. "
                "Можно только переопределить свойства."
            )
        elif self.has_children:
            self.edit_cname.setEnabled(False)
            self.lbl_cname_hint.setText(
                "Создано в текущем объекте, но есть потомки — имя менять нельзя."
            )
        else:
            self.edit_cname.setEnabled(True)
            self.lbl_cname_hint.setText(
                "⚠ Создано в текущем объекте, потомков нет. "
                "Переименование допустимо, но НЕЖЕЛАТЕЛЬНО."
            )

    # =====================================================================
    # BLOB
    # =====================================================================
    def _on_load_blob(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбор изображения", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.svg);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось прочитать файл: {e}"
            )
            return

        import os
        self._blob_data = data
        self._blob_name = os.path.basename(path)
        self._blob_removed = False
        self.lbl_blob_status.setText(
            f"BLOB: {self._blob_name} ({len(data)} байт)"
        )
        self.btn_remove_blob.setEnabled(True)

    def _on_remove_blob(self):
        self._blob_data = None
        self._blob_name = None
        self._blob_removed = True
        self.lbl_blob_status.setText("— BLOB не задан —")
        self.btn_remove_blob.setEnabled(False)

    # =====================================================================
    # Сохранение (валидация перед accept)
    # =====================================================================
    def _on_accept(self):
        new_cname = self.edit_cname.text().strip()
        if not new_cname:
            QMessageBox.warning(
                self, "Ошибка", "Имя свойства не может быть пустым"
            )
            return

        if self.mode == 'edit' and self.prop is not None:
            if new_cname != self.prop.cname:
                owner_vid = getattr(self.prop, 'owner_version_id', None)
                is_inherited = (owner_vid is not None and owner_vid != self.version_id)
                if is_inherited:
                    QMessageBox.warning(
                        self, "Ошибка",
                        "Нельзя переименовать унаследованное свойство."
                    )
                    return
                if self.has_children:
                    QMessageBox.warning(
                        self, "Ошибка",
                        "Нельзя переименовать свойство: есть потомки."
                    )
                    return
                reply = QMessageBox.question(
                    self, "Переименование",
                    f"Переименовать «{self.prop.cname}» → «{new_cname}»?\n\n"
                    "Это НЕЖЕЛАТЕЛЬНО, но допустимо (потомков нет).",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

        if self._blob_removed and self.prop is not None and self.prop.is_blob:
            reply = QMessageBox.question(
                self, "Удаление BLOB",
                "Удалить BLOB у свойства?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.accept()

    # =====================================================================
    # Результат — dict, без прямой записи в модель
    # =====================================================================
    def get_data(self) -> Dict[str, Any]:
        """
        Возвращает словарь с новыми метаданными.
        Класс-вызыватель (ClassEditDialog._on_prop_add / _on_prop_edit)
        сам решает, как применить: add_property / rename_property /
        set_property_meta / set_blob.
        """
        return {
            'cname': self.edit_cname.text().strip(),
            'ui_label_ru': self.edit_ui_label.text().strip() or None,
            'editor_type': self.combo_editor.currentData(),
            'qt_target': self.edit_qt_target.text().strip() or None,
            'translation_strategy': self.combo_strategy.currentData(),
            'typevalue': self.combo_type.currentData(),
            'typesourcevalue': self.combo_typesource.currentData(),
            'isdefaultepr': self.chk_isdefaultepr.isChecked(),
            'bridgecalcset': self._get_combo_value(self.combo_bridgecalcset),
            'bridgecalcget': self._get_combo_value(self.combo_bridgecalcget),
            'fuuncselectionvalue': self._get_combo_value(self.combo_fuuncselectionvalue),
            'blob_data': self._blob_data,
            'blob_name': self._blob_name,
            'blob_removed': self._blob_removed,
        }

    def _get_combo_value(self, combo: QComboBox) -> Optional[str]:
        val = combo.currentData()
        if val:
            return str(val)
        text = combo.currentText().strip()
        if text and text != "— не задано —":
            return text
        return None