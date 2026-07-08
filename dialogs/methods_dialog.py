# Полный путь: dialogs/methods_dialog.py
"""
Диалог управления методами класса.
Позволяет просматривать, добавлять и редактировать методы.
Содержит список существующих методов и редактор кода.
Поддерживает версионирование методов (dt_start, dt_end).
Слева отображается полное имя класса (точечная нотация).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QDateTimeEdit, QSplitter,
    QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QDateTime

from database import DatabaseService
from services.class_data_service import ClassDataService
from lang.local_translator import LocalTranslator


class MethodsDialog(QDialog):
    """
    Диалог управления методами класса.

    Свойства:
        - db: DatabaseService - экземпляр БД
        - class_service: ClassDataService - сервис классов
        - translator: LocalTranslator - переводы
        - version_id: int - ID версии класса
        - element_id: int - ID элемента в коллекции
        - class_name: str - полное имя класса
        - current_method_id: Optional[int] - ID редактируемого метода

    Методы:
        - setup_ui() - настройка интерфейса
        - load_methods() - загрузка методов
        - load_available_methods() - загрузка доступных методов
        - on_method_selected() - обработка выбора метода
        - save_method() - сохранение метода
        - add_new_method() - добавление нового метода
        - delete_method() - удаление метода
    """

    def __init__(self, parent=None, db: DatabaseService = None,
                 version_id: int = -1, element_id: int = -1,
                 class_name: str = ""):
        super().__init__(parent)
        self.db = db
        self.class_service = ClassDataService(db) if db else None
        self.translator = LocalTranslator()
        self.version_id = version_id
        self.element_id = element_id
        self.class_name = class_name
        self.current_method_id = None

        self.setWindowTitle(self.translator.tr('btn_methods') + f": {class_name}")
        self.resize(800, 600)

        self.setup_ui()
        self.load_methods()
        self.load_available_methods()

    def setup_ui(self):
        """Настройка интерфейса диалога."""
        layout = QVBoxLayout(self)

        # Верхняя панель: имя класса
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(self.translator.tr('field_class_name') + ":"))
        self.class_name_label = QLabel(self.class_name)
        self.class_name_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        top_layout.addWidget(self.class_name_label)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Основной сплиттер: список методов | редактор
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель: список методов
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel(self.translator.tr('field_methods_list') + ":"))

        self.methods_list = QListWidget()
        self.methods_list.itemClicked.connect(self.on_method_selected)
        self.methods_list.itemDoubleClicked.connect(self.on_method_selected)
        left_layout.addWidget(self.methods_list)

        # Кнопки управления списком
        list_btn_layout = QHBoxLayout()
        self.btn_add_method = QPushButton(self.translator.tr('btn_add'))
        self.btn_add_method.clicked.connect(self.add_new_method)
        self.btn_delete_method = QPushButton(self.translator.tr('btn_delete'))
        self.btn_delete_method.clicked.connect(self.delete_method)
        list_btn_layout.addWidget(self.btn_add_method)
        list_btn_layout.addWidget(self.btn_delete_method)
        left_layout.addLayout(list_btn_layout)

        splitter.addWidget(left_panel)

        # Правая панель: редактор метода
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Группа параметров метода
        params_group = QGroupBox(self.translator.tr('field_method_params'))
        params_layout = QFormLayout(params_group)

        # Имя метода
        self.method_combo = QComboBox()
        self.method_combo.setEditable(True)
        params_layout.addRow(self.translator.tr('field_method_name') + ":", self.method_combo)

        # Даты
        self.dt_start_edit = QDateTimeEdit()
        self.dt_start_edit.setDateTime(QDateTime.currentDateTime())
        self.dt_start_edit.setCalendarPopup(True)
        params_layout.addRow(self.translator.tr('field_start_date') + ":", self.dt_start_edit)

        self.dt_end_edit = QDateTimeEdit()
        self.dt_end_edit.setDateTime(QDateTime.currentDateTime())
        self.dt_end_edit.setCalendarPopup(True)
        self.dt_end_edit.setCheckBox(True)
        self.dt_end_edit.setChecked(False)
        params_layout.addRow(self.translator.tr('field_end_date') + ":", self.dt_end_edit)

        right_layout.addWidget(params_group)

        # Редактор кода
        right_layout.addWidget(QLabel(self.translator.tr('field_code') + ":"))
        self.code_edit = QTextEdit()
        self.code_edit.setFont(self._get_mono_font())
        right_layout.addWidget(self.code_edit)

        # Кнопки сохранения
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_save.clicked.connect(self.save_method)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

    def _get_mono_font(self):
        """Получение моноширинного шрифта."""
        from PySide6.QtGui import QFont
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.Monospace)
        return font

    def load_methods(self):
        """Загрузка методов класса."""
        if not self.class_service or self.version_id <= 0:
            return

        self.methods_list.clear()
        methods = self.class_service.get_class_methods(self.version_id)

        for method in methods:
            item = QListWidgetItem(f"{method.get('c_name', '')}")
            item.setData(Qt.UserRole, method.get('id'))
            self.methods_list.addItem(item)

    def load_available_methods(self):
        """Загрузка доступных методов для ComboBox."""
        if not self.class_service:
            return

        self.method_combo.clear()
        methods = self.class_service.get_all_methods()

        for method in methods:
            self.method_combo.addItem(method.get('c_name', ''), method.get('id'))

        # Добавляем возможность ввода нового имени
        self.method_combo.setEditable(True)

    def on_method_selected(self, item: QListWidgetItem):
        """
        Обработка выбора метода из списка.

        Вход:
            item: QListWidgetItem - выбранный элемент

        Выход: None
        """
        method_id = item.data(Qt.UserRole)
        self.current_method_id = method_id

        # Загружаем данные метода (заглушка, полная реализация требует доп. метода)
        # В реальности нужно загрузить полные данные метода
        method_name = item.text()
        self.method_combo.setCurrentText(method_name)

    def save_method(self):
        """Сохранение метода."""
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                "Не указан ID класса"
            )
            return

        method_name = self.method_combo.currentText().strip()
        if not method_name:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_enter_method_name')
            )
            return

        # Собираем данные
        method_data = {
            'c_name': method_name,
            'c_komment': '',
            'txt_method': self.code_edit.toPlainText()
        }

        try:
            if self.current_method_id:
                # Обновление существующего метода
                # TODO: Реализовать update_method
                QMessageBox.information(
                    self,
                    self.translator.tr('info'),
                    "Обновление метода пока в разработке"
                )
            else:
                # Создание нового метода
                new_method_id = self.class_service.add_method_to_class(
                    self.version_id,
                    method_data
                )
                if new_method_id:
                    self.current_method_id = new_method_id
                    self.load_methods()
                    QMessageBox.information(
                        self,
                        self.translator.tr('info'),
                        self.translator.tr('info_method_saved')
                    )
                    self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translator.tr('error'),
                f"Ошибка сохранения метода: {str(e)}"
            )

    def add_new_method(self):
        """Добавление нового метода."""
        self.current_method_id = None
        self.method_combo.setCurrentText("")
        self.code_edit.clear()
        self.method_combo.setFocus()

    def delete_method(self):
        """Удаление метода."""
        current = self.methods_list.currentItem()
        if not current:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_select_method')
            )
            return

        method_id = current.data(Qt.UserRole)

        if QMessageBox.question(
                self,
                self.translator.tr('confirm_delete'),
                self.translator.tr('confirm_delete_method'),
                QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.class_service:
                self.class_service.remove_method_from_class(
                    self.version_id,
                    method_id
                )
                self.load_methods()