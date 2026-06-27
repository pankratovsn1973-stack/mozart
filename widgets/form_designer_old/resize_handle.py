# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/resize_handle.py

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainter


class ResizeHandle(QGraphicsRectItem):
    """Интеллектуальный маркер ресайза, поддерживающий групповой синхронный шаг изменений."""

    POSITIONS = {4: "BottomRight"}
    HANDLE_SIZE = 12

    def __init__(self, position_index, target_item, parent=None):
        super().__init__(parent)
        self.target_item = target_item
        self.position_index = int(position_index)

        self.handle_size = 16.0
        self.setRect(0, 0, self.handle_size, self.handle_size)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)
        self.setZValue(10000)

        self.setPen(QPen(QColor('#0066ff'), 2.0, Qt.PenStyle.SolidLine))
        self.setBrush(QColor('#ffffff'))

        self._hovered = False
        self._normal_color = QColor('#0066ff')
        self._hover_color = QColor('#ff5500')

        self._is_resizing = False
        self.start_x = 0.0
        self.start_y = 0.0
        self.start_w = 0.0
        self.start_h = 0.0
        self.start_mouse_scene = QPointF()
        self._start_group_sizes = {}

    def boundingRect(self):
        return QRectF(0, 0, self.handle_size, self.handle_size)

    def update_position(self):
        """Позиционирует маркер СНАРУЖИ правого нижнего угла в АБСОЛЮТНЫХ координатах сцены."""
        if not self.target_item or not self.target_item.scene():
            return

        target_scene_pos = self.target_item.scenePos()

        # Проверяем, есть ли активный внутренний элемент (маскированный txt_of_ref или lbl_of_ref)
        child_widget = getattr(self.target_item, '_focused_child_widget', None) or \
                       getattr(self.target_item, '_active_child_item', None)

        if child_widget:
            child_geo = child_widget.geometry()
            offset = 2.0
            x = target_scene_pos.x() + float(child_geo.right() + offset)
            y = target_scene_pos.y() + float(child_geo.bottom() + offset)
            self.setPos(QPointF(x, y))
            return

        try:
            form_rect = self.target_item.rect()
            w = form_rect.width()
            h = form_rect.height()
        except Exception:
            w = getattr(self.target_item, '_width', 150.0)
            h = getattr(self.target_item, '_height', 30.0)

        offset = 2.0
        new_x = target_scene_pos.x() + w + offset
        new_y = target_scene_pos.y() + h + offset

        self.setPos(QPointF(new_x, new_y))

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.setPen(QPen(self._hover_color, 2.5, Qt.PenStyle.SolidLine))
        self.update()
        event.accept()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.setPen(QPen(self._normal_color, 2.0, Qt.PenStyle.SolidLine))
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(
                f"[RESIZE_DIAG] mousePressEvent на маркере для target: {getattr(self.target_item, 'control_id', 'unknown')}")
            self._is_resizing = True
            self._start_group_sizes.clear()

            form_pos = self.target_item.pos()
            self.start_x = form_pos.x()
            self.start_y = form_pos.y()

            child_widget = getattr(self.target_item, '_focused_child_widget', None) or \
                           getattr(self.target_item, '_active_child_item', None)

            if child_widget:
                print(f"[RESIZE_DIAG] Режим: Ресайз ВНУТРЕННЕГО элемента ({child_widget.objectName()})")
                self.start_w = float(child_widget.width())
                self.start_h = float(child_widget.height())
                if hasattr(self.target_item, 'get_start_child_sizes'):
                    self._start_group_sizes = self.target_item.get_start_child_sizes()
            else:
                print(f"[RESIZE_DIAG] Режим: Ресайз КОНТЕЙНЕРА/ФОРМЫ")
                self.start_w = getattr(self.target_item, '_width', self.target_item.rect().width())
                self.start_h = getattr(self.target_item, '_height', self.target_item.rect().height())

                if self.scene():
                    from .control_item_base import ControlItemBase
                    for item in self.scene().selectedItems():
                        if isinstance(item, ControlItemBase):
                            self._start_group_sizes[item] = (float(item.rect().width()), float(item.rect().height()))

            self.start_mouse_scene = event.scenePos()

            # ✅ КРИТИЧЕСКИЙ ФИКС: Явно захватываем мышь!
            # Без этого mouseMoveEvent не будет вызываться для независимых элементов
            self.grabMouse()
            print(f"[RESIZE_DIAG] grabMouse() выполнен. Начинаем ресайз.")

            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self._is_resizing or not self.target_item:
            super().mouseMoveEvent(event)
            return

        current_mouse_scene = event.scenePos()
        dx = current_mouse_scene.x() - self.start_mouse_scene.x()
        dy = current_mouse_scene.y() - self.start_mouse_scene.y()

        print(f"[RESIZE_DIAG] mouseMoveEvent | dx: {dx:.1f}, dy: {dy:.1f}")

        is_form = hasattr(self.target_item, 'update_geometry')

        if is_form:
            print(f"[RESIZE_DIAG] Применяем размеры к ФОРМЕ через update_geometry")
            self.target_item.update_geometry(self.start_x, self.start_y, max(50.0, self.start_w + dx),
                                             max(50.0, self.start_h + dy))
        else:
            child_widget = getattr(self.target_item, '_focused_child_widget', None) or \
                           getattr(self.target_item, '_active_child_item', None)

            if child_widget:
                print(f"[RESIZE_DIAG] Применяем размеры к ВНУТРЕННЕМУ элементу через setFixedSize")
                if self._start_group_sizes:
                    for child, (orig_w, orig_h) in self._start_group_sizes.items():
                        new_w = max(20.0, orig_w + dx)
                        new_h = max(15.0, orig_h + dy)
                        child.setFixedSize(int(new_w), int(new_h))
                else:
                    new_w = max(20.0, self.start_w + dx)
                    new_h = max(15.0, self.start_h + dy)
                    child_widget.setFixedSize(int(new_w), int(new_h))
            else:
                print(f"[RESIZE_DIAG] Применяем размеры к КОНТЕЙНЕРУ через setWidgetSize")
                from .control_item_base import ControlItemBase
                has_group = len([i for i in self._start_group_sizes.keys() if isinstance(i, ControlItemBase)]) > 1

                if has_group:
                    for item, (orig_w, orig_h) in self._start_group_sizes.items():
                        new_w = max(20.0, orig_w + dx)
                        new_h = max(20.0, orig_h + dy)
                        if hasattr(item, 'setWidgetSize'):
                            item.setWidgetSize(new_w, new_h)
                else:
                    new_w = max(20.0, self.start_w + dx)
                    new_h = max(20.0, self.start_h + dy)
                    if hasattr(self.target_item, 'setWidgetSize'):
                        print(f"[RESIZE_DIAG] Вызываем setWidgetSize({new_w:.1f}, {new_h:.1f})")
                        self.target_item.setWidgetSize(new_w, new_h)
                    else:
                        print(f"[RESIZE_DIAG] ВНИМАНИЕ: у target_item НЕТ метода setWidgetSize!")

        self.update_position()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"[RESIZE_DIAG] mouseReleaseEvent. Завершаем ресайз.")
            self._is_resizing = False
            self._start_group_sizes.clear()

            # ✅ Освобождаем мышь
            self.ungrabMouse()

            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(rect, 3, 3)

        painter.setPen(QPen(QColor('#888888'), 1.0, Qt.PenStyle.SolidLine))
        painter.drawLine(rect.left() + 3, rect.bottom() - 3, rect.right() - 3, rect.top() + 3)
        painter.drawLine(rect.left() + 6, rect.bottom() - 3, rect.right() - 3, rect.top() + 6)

        painter.restore()