# widgets/form_designer_old/statusbar_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsWidget
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont


class StatusBarBar(QGraphicsWidget):
    """
    Статусная строка (подвал) проектируемой формы.
    Отображает:
    - координаты мыши относительно формы
    - текущий масштаб
    - режим (проектирование/выполнение)
    - информационные сообщения
    """

    status_message_changed = Signal(str)

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

        # Задаем жесткие ограничения размеров без использования сложного Layout
        self.setMinimumHeight(self.bar_height)
        self.setMaximumHeight(self.bar_height)
        self.setMinimumWidth(400)

    def set_coordinates(self, x, y):
        """Устанавливает координаты мыши относительно формы"""
        if self._current_x != int(x) or self._current_y != int(y):
            self._current_x = int(x)
            self._current_y = int(y)
            self.update()  # Вызываем перерисовку текста

    def set_zoom(self, zoom_percent):
        """Устанавливает масштаб в процентах"""
        if self._zoom_percent != int(zoom_percent):
            self._zoom_percent = int(zoom_percent)
            self.update()

    def set_design_mode(self, design_mode):
        """Устанавливает режим: True - проектирование, False - просмотр"""
        if self._design_mode != design_mode:
            self._design_mode = design_mode
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
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # 1. Отрисовка базового фона панели подвала
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(QPen(QColor(210, 210, 210), 1))
        painter.drawRect(rect)

        # Верхняя разделительная линия
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawLine(rect.topLeft(), rect.topRight())

        # Эффект внутренней тени сверху (сдвиг по Y на 1 пиксель)
        painter.setPen(QPen(QColor(225, 225, 225), 1))
        painter.drawLine(rect.topLeft() + QPointF(0, 1), rect.topRight() + QPointF(0, 1))

        # 2. Отрисовка текстовой информации (прямо на холсте панели)
        painter.setFont(QFont("Arial", 8))

        # Левая секция: Статусное сообщение
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawText(rect.adjusted(10, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, self._status_text)

        # Центральная секция: Режим
        if self._design_mode:
            painter.setPen(QPen(QColor(100, 100, 150), 1))
            mode_str = "Режим: проектирование"
        else:
            painter.setPen(QPen(QColor(60, 120, 60), 1))
            mode_str = "Режим: просмотр"
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignCenter, mode_str)

        # Правая секция: Масштаб и Координаты мыши
        # Сначала определяем цвет масштаба
        if self._zoom_percent == 100:
            zoom_color = QColor(60, 120, 60)
        elif self._zoom_percent < 100:
            zoom_color = QColor(100, 100, 200)
        else:
            zoom_color = QColor(200, 100, 100)

        zoom_str = f"  {self._zoom_percent}%"
        coord_str = f"x: {self._current_x}, y: {self._current_y}  | "

        # Отрисовка координат мыши (моноширинный шрифт)
        painter.setFont(QFont("Courier New", 8, QFont.Bold))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawText(rect.adjusted(0, 0, -50, 0), Qt.AlignVCenter | Qt.AlignRight, coord_str)

        # Отрисовка процентов масштаба
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QPen(zoom_color, 1))
        painter.drawText(rect.adjusted(0, 0, -10, 0), Qt.AlignVCenter | Qt.AlignRight, zoom_str)
