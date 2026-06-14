# widgets/form_designer_old/form_background.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс FormBackground (наследник QGraphicsRectItem).
Является визуальной подложкой (холстом проектируемой формы) на сцене дизайнера.
Исправлен баг отсутствия метода scene() у объекта title_bar (TitleBarStub).
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QColor, QPainter


class TitleBarStub(QGraphicsRectItem):
    """
    Вспомогательный графический класс для заголовка формы.
    Наследуется от QGraphicsRectItem, чтобы иметь нативный метод scene() для form_scene.py.
    """

    def __init__(self, parent_background):
        # Инициализируем графический элемент, передавая форму как родителя (parent)
        super().__init__(parent_background)
        self.parent_bg = parent_background

        # Скрываем стандартную рамку самого прямоугольника заголовка
        self.setPen(Qt.NoPen)
        self.setBrush(Qt.NoBrush)

    def get_height(self) -> float:
        """Возвращает стандартную высоту заголовка окна формы для дизайнера."""
        return 32.0


class FormBackground(QGraphicsRectItem):
    """
    Класс подложки формы для визуального редактора.
    Управляет физическими размерами холста формы и свойствами для инспектора.
    """

    def __init__(self, width: float = 400, height: float = 300, title: str = "", parent=None):
        super().__init__(parent)

        # Сохраняем метаданные формы
        self.title = str(title)

        # ИСПРАВЛЕНО: Теперь title_bar является честным графическим элементом Qt
        self.title_bar = TitleBarStub(self)

        # Задаем начальную геометрию прямоугольника (x=0, y=0, w, h)
        w = float(width) if not isinstance(width, str) else 400.0
        h = float(height) if not isinstance(height, str) else 300.0
        self.setRect(0.0, 0.0, w, h)

        self.setPos(0.0, 0.0)

        # Настраиваем системные флаги интерактивности Qt Graphics View
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

        self.setPen(QPen(QColor('#a0a0a0'), 1, Qt.SolidLine))
        self.setBrush(QColor('#ffffff'))

    @property
    def width(self) -> float:
        """Возвращает текущую ширину формы для инспектора свойств."""
        return self.rect().width()

    @property
    def height(self) -> float:
        """Возвращает текущую высоту формы для инспектора свойств."""
        return self.rect().height()

    def resize_form(self, width: float, height: float):
        """
        Метод безопасного изменения размеров формы из инспектора свойств.
        Принудительно пересчитывает boundingRect, предотвращая отрыв маркеров.
        """
        w = max(50.0, float(width))
        h = max(50.0, float(height))

        self.prepareGeometryChange()
        self.setRect(0.0, 0.0, w, h)

        if self.scene():
            self.scene().setSceneRect(self.scene().itemsBoundingRect())
            if hasattr(self.scene(), '_refresh_grid_layers'):
                self.scene()._refresh_grid_layers()
            else:
                self.scene().update()

    def set_width(self, width: float):
        """Сеттер ширины для инспектора свойств."""
        self.resize_form(width, self.rect().height())

    def set_height(self, height: float):
        """Сеттер высоты для инспектора свойств."""
        self.resize_form(self.rect().width(), height)

    def paint(self, painter: QPainter, option, widget=None):
        """Отрисовка внешних границ самой формы и её заголовка."""
        painter.save()

        # 1. Рисуем аккуратную внешнюю рамку контура формы
        border_pen = QPen(QColor('#808080'), 1, Qt.SolidLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect())

        # 2. Визуально набрасываем серую полоску заголовка окна формы
        if self.title_bar:
            tb_height = self.title_bar.get_height()
            tb_rect = QRectF(self.rect().left(), self.rect().top(), self.rect().width(), tb_height)

            # Заливаем шапку формы светло-серым «оконным» цветом
            painter.fillRect(tb_rect, QColor('#d8d8d8'))
            painter.drawRect(tb_rect)

            # Выводим текст заголовка формы
            painter.setPen(QPen(QColor('#000000')))
            painter.drawText(tb_rect.adjusted(8, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, self.title)

        painter.restore()
