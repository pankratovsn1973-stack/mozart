# Полный путь: dialogs/base_class_selector.py
"""
Диалог выбора базового класса при создании нового класса.
Позволяет фильтровать классы по типу (Python/ERP).
Отображает дерево доступных классов для выбора.
Возвращает ID выбранной версии класса.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QTreeWidget, QTreeWidgetItem, QPushButton,
    QMessageBox, QLabel
)
from PySide6.QtCore import Qt

from database import DatabaseService
from services.class_data_service import ClassDataService
from lang.local_translator import LocalTranslator


class BaseClassSelectorDialog(QDialog):
    """
    Диалог выбора базового класса.

    Свойства:
        - db: DatabaseService - экземпляр БД
        - class_service: ClassDataService - сервис классов
        - translator: LocalTranslator - переводы
        - selected_version_id: Optional[int] - выбранный ID версии

    Методы:
        - setup_ui() - настройка интерфейса
        - load_classes(filter_type) - загрузка классов
        - get_selected_version_id() -> Optional[int] - получение выбранного ID
        - on_filter_changed() - обработка смены фильтра
        - on_item_double_clicked() - обработка двойного клика
    """

    def __init__(self, parent=None, db: DatabaseService = None):
        super().__init__(parent)
        self.db = db
        self.class_service = ClassDataService(db) if db else None
        self.translator = LocalTranslator()
        self.selected_version_id = None

        self.setWindowTitle(self.translator.tr('select_base_class'))
        self.resize(600, 500)

        self.setup_ui()
        self.load_classes('all')

    def setup_ui(self):
        """Настройка интерфейса диалога."""
        layout = QVBoxLayout(self)

        # Верхняя панель: фильтр
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.translator.tr('field_filter') + ":"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItem(self.translator.tr('filter_all'), 'all')
        self.filter_combo.addItem(self.translator.tr('filter_python'), 'python')
        self.filter_combo.addItem(self.translator.tr('filter_erp'), 'erp')
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Дерево классов
        self.class_tree = QTreeWidget()
        self.class_tree.setHeaderLabels([
            self.translator.tr('field_class_name'),
            self.translator.tr('field_type'),
            self.translator.tr('field_base_class')
        ])
        self.class_tree.setColumnWidth(0, 250)
        self.class_tree.setColumnWidth(1, 80)
        self.class_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.class_tree)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton(self.translator.tr('btn_select'))
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def load_classes(self, filter_type: str = 'all'):
        """
        Загрузка классов в дерево.

        Вход:
            filter_type: str - 'all', 'python', 'erp'

        Выход: None
        """
        if not self.class_service:
            return

        self.class_tree.clear()

        # Получаем классы
        classes = self.class_service.get_available_base_classes()

        # Фильтруем
        if filter_type == 'python':
            classes = [c for c in classes if c.get('c_base_source') == 'PYTHON']
        elif filter_type == 'erp':
            classes = [c for c in classes if c.get('c_base_source') == 'ERP']

        # Добавляем в дерево
        for cls in classes:
            item = QTreeWidgetItem([
                cls.get('c_name', ''),
                cls.get('c_base_source', ''),
                '...'
            ])
            item.setData(0, Qt.UserRole, cls.get('version_id'))
            self.class_tree.addTopLevelItem(item)

        # Расширяем все узлы
        self.class_tree.expandAll()

    def get_selected_version_id(self) -> int:
        """
        Получение ID выбранной версии класса.

        Вход: Нет

        Выход:
            int - ID версии или -1
        """
        return self.selected_version_id if self.selected_version_id else -1

    def on_filter_changed(self, index: int):
        """
        Обработка смены фильтра.

        Вход:
            index: int - индекс выбранного фильтра

        Выход: None
        """
        filter_type = self.filter_combo.currentData()
        self.load_classes(filter_type)

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Обработка двойного клика по элементу.

        Вход:
            item: QTreeWidgetItem - выбранный элемент
            column: int - колонка

        Выход: None
        """
        self.accept_selection()

    def accept_selection(self):
        """Подтверждение выбора."""
        current = self.class_tree.currentItem()
        if not current:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_select_class')
            )
            return

        self.selected_version_id = current.data(0, Qt.UserRole)
        self.accept()