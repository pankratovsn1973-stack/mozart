# widgets/form_designer_old/events_panel.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QComboBox, \
    QMessageBox
from PySide6.QtCore import Qt


class EventsPanel(QWidget):
    """Панель событий контрола"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_control = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.events_table = QTableWidget(0, 2)
        self.events_table.setHorizontalHeaderLabels(["Событие", "Метод"])
        self.events_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.events_table)

        # Список стандартных событий
        self.default_events = [
            "on_click",
            "on_dbl_click",
            "on_change",
            "on_focus",
            "on_blur",
            "on_key_press",
            "on_mouse_enter",
            "on_mouse_leave"
        ]

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Сохранить")
        self.btn_save.clicked.connect(self.save_events)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def set_control(self, control_item, saved_events=None):
        self.current_control = control_item
        self.events_table.setRowCount(0)

        if not control_item:
            self.setEnabled(False)
            return

        self.setEnabled(True)
        saved_events = saved_events or {}

        for row, event_name in enumerate(self.default_events):
            self.events_table.insertRow(row)

            # Событие (только для чтения)
            event_item = QTableWidgetItem(event_name)
            event_item.setFlags(event_item.flags() & ~Qt.ItemIsEditable)
            self.events_table.setItem(row, 0, event_item)

            # Выбор метода
            combo = QComboBox()
            combo.addItem("-- не выбрано --", "")
            self.events_table.setCellWidget(row, 1, combo)

            # Устанавливаем сохранённое значение
            if event_name in saved_events:
                idx = combo.findText(saved_events[event_name])
                if idx >= 0:
                    combo.setCurrentIndex(idx)

    def set_available_methods(self, methods):
        """Устанавливает список доступных методов для выбора"""
        for row in range(self.events_table.rowCount()):
            combo = self.events_table.cellWidget(row, 1)
            if combo:
                current = combo.currentText()
                combo.clear()
                combo.addItem("-- не выбрано --", "")
                for method in methods:
                    combo.addItem(method, method)
                idx = combo.findText(current)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

    def save_events(self):
        """Сохраняет привязку событий"""
        if not self.current_control:
            return

        events = {}
        for row in range(self.events_table.rowCount()):
            event_name = self.events_table.item(row, 0).text()
            combo = self.events_table.cellWidget(row, 1)
            method = combo.currentText() if combo else ""

            if method and method != "-- не выбрано --":
                events[event_name] = method

        # Сигнал или callback для сохранения
        if hasattr(self, 'events_saved'):
            self.events_saved.emit(events)

    def get_events(self):
        """Возвращает текущие привязки событий"""
        events = {}
        for row in range(self.events_table.rowCount()):
            event_name = self.events_table.item(row, 0).text()
            combo = self.events_table.cellWidget(row, 1)
            method = combo.currentText() if combo else ""

            if method and method != "-- не выбрано --":
                events[event_name] = method
        return events