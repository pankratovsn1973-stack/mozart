# dialogs/select_entity_dialog.py
"""
Независимое модальное окно выбора сущности из meta.entitytypes.
Отвязано от сцены и родительских виджетов. Всегда поверх всех окон приложения.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QApplication
)
from PySide6.QtCore import Qt
from database import DatabaseService


class SelectEntityDialog(QDialog):
    """Выбор сущности из meta.entitytypes."""

    def __init__(self, parent=None, db: DatabaseService = None,
                 current_value: Optional[str] = None):
        # 🚀 КРИТИЧЕСКИ ВАЖНО: Игнорируем переданный parent!
        # Передаем None -> создается топ-уровневое окно ОС, а не виджет внутри сцены.
        super().__init__(None)


        # Убираем WindowStaysOnTopHint — он ломает модальность дочерних диалогов
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        # Модальность приложения: блокирует ввод во все окна, пока открыто это
        self.setWindowModality(Qt.ApplicationModal)

        self.setWindowTitle("Выбор сущности")
        self.resize(700, 500)

        # Центрируем окно относительно активного окна приложения
        main_window = QApplication.activeWindow()
        if main_window:
            geo = main_window.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

        # Подключение к БД (ОБЯЗАТЕЛЬНО явная передача)
        if db is None:
            raise ValueError("SelectEntityDialog требует активного подключения к БД")
        self.db = db

        # Нормализация текущего значения
        self.current_value = str(current_value).strip() if current_value not in (None, "", "None") else None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите сущность:"))

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Алиас", "Класс"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("Выбрать")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self._load()
        self.table.setFocus()

    def _load(self):
        """Загрузка списка сущностей."""
        sql = """
            SELECT et.id, et.cname, et.calias, COALESCE(ec.cname, '')
            FROM meta.entitytypes et
            LEFT JOIN meta.entity_classes ec ON et.class_id = ec.id
            ORDER BY et.cname
        """
        try:
            rows = self.db.execute_query(sql) or []
        except Exception as e:
            print(f"[SelectEntityDialog] Ошибка SQL: {e}")
            rows = []

        self.table.setRowCount(0)
        target_row = -1

        for r, (eid, cname, calias, class_name) in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(eid)))
            self.table.setItem(r, 1, QTableWidgetItem(str(cname or "")))
            self.table.setItem(r, 2, QTableWidgetItem(str(calias or "")))
            self.table.setItem(r, 3, QTableWidgetItem(str(class_name or "")))
            self.table.item(r, 0).setData(Qt.UserRole, eid)

            # Подсветка текущей сущности
            if self.current_value is not None and str(eid) == self.current_value:
                target_row = r

        if target_row >= 0:
            self.table.selectRow(target_row)
            self.table.scrollToItem(self.table.item(target_row, 0))
        elif self.table.rowCount() > 0:
            self.table.selectRow(0)

    def get_selected_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        val = item.data(Qt.UserRole) if item else None
        return str(val) if val is not None else None

    def accept(self):
        """Переопределяем accept для проверки выбора."""
        if self.get_selected_id() is None:
            return
        super().accept()

    def keyPressEvent(self, event):
        """Обрабатываем Enter и Escape корректно."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)