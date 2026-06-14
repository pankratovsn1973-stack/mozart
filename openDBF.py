


import sys
import itertools
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,                              QHBoxLayout, QPushButton, QTableView, QFileDialog,                              QMessageBox, QLabel, QLineEdit, QHeaderView)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, QSortFilterProxyModel
from PySide6.QtGui import QFont
from dbfread import DBF
import dbf
from lang.local_translator import LocalTranslator


class DBFTableModel(QAbstractTableModel):
    """Модель для отображения данных DBF с поддержкой фильтрации."""
    def __init__(self, data, headers):
        super().__init__()
        self._data = data                     # список записей (словарей)
        self._headers = headers                # список имён полей
        self._filtered_rows = list(range(len(data)))   # индексы видимых строк
        self._filters = {}                     # словарь {col: pattern}

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
            value = self._data[row][self._headers[col]]
            return str(value) if value is not None else ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def setFilter(self, col, pattern):
        """Устанавливает фильтр для колонки."""
        if pattern:
            self._filters[col] = pattern
        else:
            self._filters.pop(col, None)
        self.updateFilter()

    def clearFilters(self):
        self._filters.clear()
        self.updateFilter()

    def updateFilter(self):
        """Пересчитывает список видимых строк на основе фильтров."""
        self.beginResetModel()
        self._filtered_rows = []
        for row, record in enumerate(self._data):
            match = True
            for col, pattern in self._filters.items():
                value = str(record[self._headers[col]]) if record[self._headers[col]] is not None else ""
                # Преобразуем маску в регулярное выражение
                regex = '^' + re.escape(pattern).replace(r'\?', '.').replace(r'\*', '.*') + '$'
                if not re.match(regex, value):
                    match = False
                    break
            if match:
                self._filtered_rows.append(row)
        self.endResetModel()


class DBFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Просмотрщик DBF")
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Верхняя панель
        top_layout = QHBoxLayout()
        self.btn_open = QPushButton("Открыть DBF файл")
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
        font.setPointSize(20)
        self.table_view.setFont(font)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setSortingEnabled(False)
        main_layout.addWidget(self.table_view)

        self.model = None
        self.filter_edits = []

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите DBF файл", "", "DBF files (*.DBF);;All files (*)"
        )
        if not file_path:
            return

        try:
            # Определяем кодировку
            encodings = ['cp866', 'utf-8', 'windows-1251']
            dbf = None
            for enc in encodings:
                try:
                    dbf = DBF(file_path, encoding=enc)
                    # Проверяем, что читается первая запись
                    next(iter(dbf))
                    break
                except (UnicodeDecodeError, StopIteration):
                    continue
            if dbf is None:
                dbf = DBF(file_path)

            # Читаем все записи (для больших файлов осторожно, но КЛАДР влезет)
            data = list(dbf)
            headers = [field.name for field in dbf.fields]

            # Создаём модель
            self.model = DBFTableModel(data, headers)
            self.table_view.setModel(self.model)

            # Создаём поля ввода для фильтров
            self._create_filter_inputs(headers)

            self.info_label.setText(f"Файл: {file_path.split('/')[-1]} | Всего записей: {len(data)}")
        except Exception as e:
            QMessageBox.critical(self, translator.tr("error"), f"Не удалось прочитать файл:\n{str(e)}")

    def _create_filter_inputs(self, headers):
        # Очищаем старые фильтры
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = DBFViewer()
    viewer.show()
    sys.exit(app.exec_())