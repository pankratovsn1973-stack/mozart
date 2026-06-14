# widgets/form_designer_old/methods_panel.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
import re


class MethodsPanel(QWidget):
    """Панель управления встроенными методами (скриптами) формы и её контролов"""

    edit_method_requested = Signal(str)
    add_method_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_object = None
        self.current_alias = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок
        self.lbl_title = QLabel("Методы объекта:")
        self.lbl_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_title)

        # Список методов
        self.methods_list = QListWidget()
        self.methods_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.methods_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self.add_method_requested.emit)
        btn_layout.addWidget(self.btn_add)

        layout.addLayout(btn_layout)
        self.setEnabled(False)

    def _on_item_double_clicked(self, item):
        if item:
            # Генерируем полное имя метода для отправки в CodeEditorDialog
            full_method_name = f"{self.current_alias}_{item.text()}"
            self.edit_method_requested.emit(full_method_name)
    def set_control(self, control_item, calc_code=""):
        """
        Принимает графический ControlItem, либо саму бизнес-форму Form,
        и вытягивает из Python-кода (calc_code) все привязанные методы.
        """
        self.methods_list.clear()
        self.current_object = control_item

        if not control_item:
            self.lbl_title.setText("Методы объекта:")
            self.current_alias = ""
            self.setEnabled(False)
            return

        # ИСПРАВЛЕНО: Безопасное определение алиаса объекта без использования жесткого get_data()
        if hasattr(control_item, 'control_widget') and control_item.control_widget:
            # В руках графический маркер ControlItem -> читаем имя Mozart-виджета
            self.current_alias = control_item.control_widget.objectName()
            self.lbl_title.setText(f"Методы контрола: {self.current_alias}")
        else:
            # В руках сама рантайм бизнес-форма Form -> читаем алиас или заголовок
            self.current_alias = getattr(control_item, 'form_alias', getattr(control_item, 'objectName', 'Form'))
            if not self.current_alias:
                self.current_alias = "Form"
            self.lbl_title.setText(f"Методы формы: {self.current_alias}")

        self.setEnabled(True)

        # Если передан сырой код скриптов формы, парсим его на лету
        if calc_code:
            self._parse_methods_from_code(calc_code)

    def _parse_methods_from_code(self, calc_code):
        """Регулярным выражением находит функции вида 'def алиасОбъекта_имяМетода(context):'"""
        if not self.current_alias:
            return

        # Ищем паттерн функции, завязанной на текущий алиас (например: def textbox_1_on_click)
        pattern = rf"def\s+{self.current_alias}_([a-zA-Z0-9_]+)\s*\("
        matches = re.findall(pattern, calc_code)

        for method_name in matches:
            # Добавляем чистый хвост имени метода в список интерфейса
            self.methods_list.addItem(method_name)
