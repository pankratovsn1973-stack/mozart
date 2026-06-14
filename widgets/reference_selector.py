
# widgets/reference_selector.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLineEdit, QHeaderView
from PySide6.QtCore import Qt
from database import DatabaseService


class ReferenceSelector(QDialog):
    """
    Универсальный диалог выбора записи из указанной таблицы.
    """
    def __init__(self, table_name, display_field='cname', id_field='id',
                 parent=None, db=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор значения")
        self.resize(600, 400)

        self.table_name = table_name
        self.display_field = display_field
        self.id_field = id_field
        self.db = db or DatabaseService()
        self.selected_id = None
        self.selected_display = None

        layout = QVBoxLayout(self)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")
        self.search_edit.textChanged.connect(self.load_data)
        layout.addWidget(self.search_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Выбрать")
        btn_ok.clicked.connect(self.accept_selection)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        filter_text = self.search_edit.text().strip()
        if filter_text:
            sql = f"SELECT {self.id_field}, {self.display_field} FROM {self.table_name} WHERE {self.display_field} ILIKE %s ORDER BY {self.display_field} LIMIT 200"
            params = (f"%{filter_text}%",)
        else:
            sql = f"SELECT {self.id_field}, {self.display_field} FROM {self.table_name} ORDER BY {self.display_field} LIMIT 200"
            params = None
        rows = self.db.execute_query(sql, params)
        self.table.setRowCount(0)
        for row in rows:
            pos = self.table.rowCount()
            self.table.insertRow(pos)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 0:
                    item.setData(Qt.UserRole, val)
                self.table.setItem(pos, col, item)

    def accept_selection(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            self.selected_id = item.data(Qt.UserRole)
            self.selected_display = self.table.item(current_row, 1).text()
            self.accept()

    def get_selected(self):
        return self.selected_id, self.selected_display