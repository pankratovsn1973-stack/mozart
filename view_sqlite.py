#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,                              QHBoxLayout, QPushButton, QTableView, QFileDialog,                              QMessageBox, QLabel, QLineEdit, QHeaderView)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from lang.local_translator import LocalTranslator


class SQLiteTableModel(QAbstractTableModel):
    """Модель для отображения данных из SQLite с поддержкой фильтрации."""
    def __init__(self, data, headers):
        super().__init__()
        self._data = data                     # список записей (кортежи)
        self._headers = headers                # список имён колонок
        self._filtered_rows = list(range(len(data)))
        self._filters = {}                     # {col: pattern}

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered_rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = self._filtered_rows[index.row()]
            col = index.column()
            value = self._data[row][col]
            return str(value) if value is not None else ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def setFilter(self, col, pattern):
        if pattern:
            self._filters[col] = pattern
        else:
            self._filters.pop(col, None)
        self.updateFilter()

    def clearFilters(self):
        self._filters.clear()
        self.updateFilter()

    def updateFilter(self):
        self.beginResetModel()
        self._filtered_rows = []
        for row_idx, row in enumerate(self._data):
            match = True
            for col, pattern in self._filters.items():
                value = str(row[col]) if row[col] is not None else ""
                regex = '^' + re.escape(pattern).replace(r'\?', '.').replace(r'\*', '.*') + '$'
                if not re.match(regex, value):
                    match = False
                    break
            if match:
                self._filtered_rows.append(row_idx)
        self.endResetModel()


class SQLiteViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(translator.tr("title_sqlite_viewer"))
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Верхняя панель
        top_layout = QHBoxLayout()
        self.btn_open = QPushButton("Открыть SQLite файл")
        self.btn_open.clicked.connect(self.open_file)
        top_layout.addWidget(self.btn_open)

        self.btn_apply = QPushButton("Применить фильтр")
        self.btn_apply.clicked.connect(self.apply_filters)
        top_layout.addWidget(self.btn_apply)

        self.btn_clear = QPushButton("Сбросить фильтры")
        self.btn_clear.clicked.connect(self.clear_filters)
        top_layout.addWidget(self.btn_clear)

        self.info_label = QLabel("Файл не открыт")
        top_layout.addStretch()
        top_layout.addWidget(self.info_label)

        main_layout.addLayout(top_layout)

        # Панель фильтров (горизонтальные QLineEdit)
        self.filter_layout = QHBoxLayout()
        main_layout.addLayout(self.filter_layout)

        # Таблица
        self.table_view = QTableView()
        font = self.table_view.font()
        font.setPointSize(12)  # Увеличенный шрифт
        self.table_view.setFont(font)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setSortingEnabled(False)
        main_layout.addWidget(self.table_view)

        self.model = None
        self.filter_edits = []
        self.conn = None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите SQLite файл", "", "SQLite files (*.sqlite *.db);;All files (*)"
        )
        if not file_path:
            return

        try:
            # Подключаемся к базе
            self.conn = sqlite3.connect(file_path)
            cursor = self.conn.cursor()
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            if not tables:
                QMessageBox.warning(self, translator.tr("error"), "В базе нет таблиц")
                return
            # Для простоты используем первую таблицу (kladr или любую)
            # Можно дать выбор, но пока берём первую
            table_name = tables[0]
            # Загружаем данные
            cursor.execute(f"SELECT rowid, * FROM \"{table_name}\"")
            data = cursor.fetchall()
            headers = [description[0] for description in cursor.description]

            # Создаём модель
            self.model = SQLiteTableModel(data, headers)
            self.table_view.setModel(self.model)

            # Создаём фильтры
            self._create_filter_inputs(headers)

            self.info_label.setText(f"Файл: {file_path.split('/')[-1]} | Таблица: {table_name} | Записей: {len(data)}")
        except Exception as e:
            QMessageBox.critical(self, translator.tr("error"), f"Не удалось прочитать файл:\n{str(e)}")
            if self.conn:
                self.conn.close()
                self.conn = None

    def _create_filter_inputs(self, headers):
        self._clear_filter_layout()
        self.filter_edits = []
        for col, header in enumerate(headers):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(header)
            line_edit.returnPressed.connect(self.apply_filters)
            self.filter_layout.addWidget(line_edit)
            self.filter_edits.append((col, line_edit))

    def _clear_filter_layout(self):
        for i in reversed(range(self.filter_layout.count())):
            widget = self.filter_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def apply_filters(self):
        if self.model is None:
            return
        for col, line_edit in self.filter_edits:
            text = line_edit.text().strip()
            self.model.setFilter(col, text if text else None)

    def clear_filters(self):
        if self.model is None:
            return
        self.model.clearFilters()
        for _, line_edit in self.filter_edits:
            line_edit.clear()

    def closeEvent(self, event):
        if self.conn:
            self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SQLiteViewer()
    viewer.show()
    sys.exit(app.exec_())