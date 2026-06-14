# base_manager.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from database import DatabaseService


class BaseEntityManager(QWidget):
    """
    Базовый класс для виджетов управления справочниками.
    Предоставляет таблицу и виртуальные методы для CRUD.
    """
    def __init__(self, parent=None, db: DatabaseService = None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.entity_name = ""  # должно быть переопределено
        self.table_headers = []  # заголовки колонок
        self.key_column = "id"  # первичный ключ
        self.data = []  # кэш данных

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки CRUD (будут подключены в подклассе)
        self.crud_buttons = None  # будет установлен в подклассе

        # Таблица
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)

        self._setup_table()

    def _setup_table(self):
        if self.table_headers:
            self.table.setColumnCount(len(self.table_headers))
            self.table.setHorizontalHeaderLabels(self.table_headers)

    def set_crud_buttons(self, crud_widget):
        """Привязать виджет с кнопками и подключить сигналы."""
        self.crud_buttons = crud_widget
        self.crud_buttons.add_clicked.connect(self.add_item)
        self.crud_buttons.edit_clicked.connect(self.edit_item)
        self.crud_buttons.delete_clicked.connect(self.delete_item)

    def load_data(self):
        """Загрузить данные из БД и обновить таблицу. Переопределяется в подклассах."""
        pass

    def refresh_table(self):
        """Обновить отображение таблицы на основе self.data."""
        self.table.setRowCount(0)
        if not self.data:
            return
        self.table.setRowCount(len(self.data))
        for row_idx, row_data in enumerate(self.data):
            for col_idx, col_name in enumerate(self.table_headers):
                value = row_data.get(col_name, "")
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, row_data.get(self.key_column))  # сохраняем id
                self.table.setItem(row_idx, col_idx, item)

    def get_selected_id(self):
        """Возвращает id выбранной строки или None."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None

    def add_item(self):
        """Добавление нового элемента. Переопределяется."""
        pass

    def edit_item(self):
        """Редактирование выбранного элемента. Переопределяется."""
        pass

    def delete_item(self):
        """Удаление выбранного элемента. Переопределяется."""
        pass

    def on_item_double_clicked(self, item):
        """По двойному клику вызываем редактирование."""
        self.edit_item()
