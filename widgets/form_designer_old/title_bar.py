# widgets/form_designer_old/title_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QGraphicsWidget, QGraphicsLinearLayout, QGraphicsTextItem,
    QGraphicsItem, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QLinearGradient, QPainter


class LayoutableButton(QGraphicsWidget):
    """Кастомная интерактивная кнопка управления с поддержкой hover-эффектов"""
    clicked = Signal()

    def __init__(self, color, border_color, symbol="", parent=None):
        super().__init__(parent)
        self.base_color = QColor(*color)
        self.border_color = QColor(*border_color)
        self.symbol = symbol
        self.is_hovered = False

        self.setPreferredSize(24, 24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        if self.isEnabled():
            self.is_hovered = True
            self.update()
        event.accept()

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.isEnabled() and event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
            event.accept()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isEnabled() and self.is_hovered:
            color = self.base_color.lighter(115)
        else:
            color = self.base_color

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(self.border_color, 1))
        painter.drawRoundedRect(self.rect(), 3, 3)

        if self.symbol:
            painter.setPen(QPen(Qt.white, 2))
            painter.setFont(self.font())
            painter.drawText(self.rect(), Qt.AlignCenter, self.symbol)


class TitleText(QGraphicsWidget):
    """Обёртка для текста заголовка, совместимая с QGraphicsLayout"""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(Qt.white)
        self.setPreferredSize(200, 24)

    def setPlainText(self, text):
        self.text_item.setPlainText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        text_rect = self.text_item.boundingRect()
        y_pos = (self.rect().height() - text_rect.height()) / 2
        self.text_item.setPos(0, max(0, y_pos))


class TitleBar(QGraphicsWidget):
    """Заголовок формы с кнопками и возможностью перетаскивания"""

    minimize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None, design_mode=True):
        """
        design_mode: True - режим проектирования (кнопки неактивны, только декорация)
                     False - режим выполнения/просмотра (кнопки активны)
        """
        super().__init__(parent)
        self.parent_form = parent
        self.title_height = 32
        self.design_mode = design_mode
        self._drag_pos = None
        self._start_pos = None

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setZValue(100)

        self._setup_ui()

        # В режиме проектирования кнопки неактивны
        if self.design_mode:
            self.btn_minimize.setEnabled(False)
            self.btn_close.setEnabled(False)

    def _setup_ui(self):
        layout = QGraphicsLinearLayout(Qt.Horizontal)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Текст заголовка
        self.title_widget = TitleText("Форма", self)
        layout.addItem(self.title_widget)
        layout.addStretch()

        # Кнопка сворачивания
        self.btn_minimize = LayoutableButton((100, 100, 100), (80, 80, 80), "—", self)
        if not self.design_mode:
            self.btn_minimize.clicked.connect(self._on_minimize_clicked)
        layout.addItem(self.btn_minimize)

        # Кнопка закрытия
        self.btn_close = LayoutableButton((200, 60, 60), (180, 40, 40), "✕", self)
        if not self.design_mode:
            self.btn_close.clicked.connect(self._on_close_clicked)
        layout.addItem(self.btn_close)

        self.setLayout(layout)
        self.setMinimumHeight(self.title_height)
        self.setMaximumHeight(self.title_height)
        self.setMinimumWidth(400)

    def set_title(self, title):
        self.title_widget.setPlainText(title)

    def get_title(self):
        return self.title_widget.text_item.toPlainText()

    def _on_minimize_clicked(self):
        """Только для режима выполнения"""
        self.minimize_clicked.emit()

    def _on_close_clicked(self):
        """Только для режима выполнения"""
        self.close_clicked.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.parent_form:
            self._drag_pos = event.scenePos()
            self._start_pos = self.parent_form.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and self.parent_form:
            delta = event.scenePos() - self._drag_pos
            new_pos = self._start_pos + delta
            self.parent_form.setPos(new_pos)

            if hasattr(self.parent_form, 'update_handles'):
                self.parent_form.update_handles()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        gradient = QLinearGradient(0, 0, 0, self.rect().height())
        gradient.setColorAt(0, QColor(70, 130, 200))
        gradient.setColorAt(1, QColor(50, 100, 170))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(40, 80, 140), 1))
        painter.drawRect(self.rect())

    def get_height(self):
        return self.title_height