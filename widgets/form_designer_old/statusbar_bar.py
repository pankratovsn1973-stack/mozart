# widgets/form_designer_old/statusbar_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout, QGraphicsProxyWidget, QComboBox
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont
from .toolbar_bar import ToolBarButton


class StatusBarBar(QGraphicsWidget):
    """
    Статусная строка (подвал) проектируемой формы.
    Отображает координаты мыши, масштаб, режим и содержит кнопки управления сеткой/привязкой.
    """

    status_message_changed = Signal(str)
    snap_toggled = Signal(bool)
    grid_toggled = Signal(bool)
    grid_size_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bar_height = 26
        self.setZValue(99)

        # Переменные состояния
        self._current_x = 0
        self._current_y = 0
        self._zoom_percent = 100
        self._design_mode = True
        self._status_text = "Готово"

        self._setup_ui()

    def _setup_ui(self):
        # Строим горизонтальный макет подвала формы
        layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        # 1. ТЕКСТОВЫЕ КНОПКИ-ФИКСАТОРЫ С АВТО-ИНДИКАЦИЕЙ ДЛЯ ПОДВАЛА
        self.btn_grid = ToolBarButton("Сетка", "Показать/скрыть сетку", self)
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)  # По умолчанию сетка горит синим (ВКЛ)
        self.btn_grid.setPreferredSize(85, 20)
        self.btn_grid.toggled.connect(lambda checked: self.grid_toggled.emit(checked))
        layout.addItem(self.btn_grid)

        self.btn_bind = ToolBarButton("Отвязано", "Включить/выключить привязку к сетке", self)
        self.btn_bind.setCheckable(True)
        self.btn_bind.setChecked(False)  # По умолчанию отвязано (красный)
        self.btn_bind.setPreferredSize(85, 20)
        self.btn_bind.toggled.connect(lambda checked: self.snap_toggled.emit(checked))
        layout.addItem(self.btn_bind)

        # 2. ПРОКСИ-ВИДЖЕТ ДЛЯ КОМБОБОКСА ВЫБОРА ШАГА СЕТКИ
        self.combo_proxy = QGraphicsProxyWidget(self)
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["2", "5", "10", "15", "20", "25", "30"])
        self.grid_combo.setCurrentText("10")
        self.grid_combo.setFixedWidth(55)
        self.grid_combo.setStyleSheet("""
            QComboBox { 
                font-size: 10px; 
                padding: 1px; 
                border: 1px solid #b0b0b0; 
                background-color: white; 
            }
        """)
        self.grid_combo.currentTextChanged.connect(self._on_grid_size_changed)
        self.combo_proxy.setWidget(self.grid_combo)
        layout.addItem(self.combo_proxy)

        layout.addStretch()
        self.setLayout(layout)

        # Задаем жесткие ограничения размеров подвала
        self.setMinimumHeight(self.bar_height)
        self.setMaximumHeight(self.bar_height)
        self.setMinimumWidth(500)

    def _on_grid_size_changed(self, text):
        """Транслирует выбранный размер сетки в ядро сцены дизайнера."""
        try:
            size = int(text)
            self.grid_size_changed.emit(size)
        except ValueError:
            pass
    def set_coordinates(self, x, y):
        """Устанавливает координаты мыши относительно формы"""
        if self._current_x != int(x) or self._current_y != int(y):
            self._current_x = int(x)
            self._current_y = int(y)
            self.update()

    def set_zoom(self, zoom_percent):
        """Устанавливает масштаб в процентах"""
        if self._zoom_percent != int(zoom_percent):
            self._zoom_percent = int(zoom_percent)
            self.update()

    def set_design_mode(self, design_mode):
        """Устанавливает режим: True - проектирование, False - просмотр"""
        if self._design_mode != design_mode:
            self._design_mode = design_mode
            self.grid_combo.setEnabled(design_mode)
            self.btn_grid.setEnabled(design_mode)
            self.btn_bind.setEnabled(design_mode)
            self.update()

    def set_status(self, text):
        """Устанавливает статусное сообщение"""
        if self._status_text != text:
            self._status_text = text
            self.update()

    def show_message(self, text):
        """Показывает сообщение в статусной строке"""
        self.set_status(text)

    def paint(self, painter: QPainter, option, widget=None):
        """Отрисовка фона и текстовых блоков статусной строки"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # 1. Отрисовка базового фона панели подвала
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(QPen(QColor(210, 210, 210), 1))
        painter.drawRect(rect)

        # Верхняя разделительная линия подвала
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(rect.topLeft(), rect.topRight())

        # 2. Отрисовка текстовой информации справа (смещаем под кнопки)
        painter.setFont(QFont("Arial", 8))

        # Левая секция подвала (после кнопок сетки): Статусное сообщение
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawText(rect.adjusted(260, 0, -10, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._status_text)

        zoom_str = f"  {self._zoom_percent}%"
        coord_str = f"x: {self._current_x}, y: {self._current_y}  | "

        # Отрисовка координат мыши (моноширинный шрифт)
        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawText(rect.adjusted(0, 0, -50, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, coord_str)

        # Отрисовка процентов масштаба
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(60, 120, 60), 1))
        painter.drawText(rect.adjusted(0, 0, -10, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, zoom_str)
