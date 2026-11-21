# dialogs/class_edit_dialog.py
"""
Главное окно редактирования структуры класса ERP.
v7.5: STRICT IDCOL. Вся работа со сценой (выделение, поиск, перемещение,
ресайз, свойства) — ТОЛЬКО по id_col. DB-ID используется исключительно
для сохранения в БД (в _save_*).
Отрисовка сцены — ТОЛЬКО после полного формирования коллекции.
"""
isDebug = True

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsItem, QPushButton, QComboBox, QLabel, QCheckBox,
    QMessageBox, QMenu, QSizePolicy, QGraphicsProxyWidget,
    QGraphicsObject, QGraphicsSimpleTextItem, QTextEdit, QSpinBox
)
from PySide6.QtCore import Qt, QPoint, QRectF, QPointF, Signal, QObject, QEvent
from PySide6.QtGui import QAction, QPen, QColor, QBrush, QKeyEvent, QPainter, QFont, QCursor
import json
import inspect
from typing import Optional, Dict, List, Any

from database import DatabaseService
from services.class_data_service import ClassDataService
from dialogs.collection_manager import CollectionManager
from controls import create_control
from lang.local_translator import LocalTranslator
from ide_core import goProject

from core.constants import SILENT_SOURCES, IDCOL_KIND_ELEMENT, GEOMETRY_PROPS

if isDebug:
    from dialogs.debug_collection_inspector import DebugCollectionInspector


# =====================================================================
# ГРАФИЧЕСКИЕ КЛАССЫ (работают с id_col)
# =====================================================================

class MoveHandleItem(QGraphicsObject):
    """Плавающий хендл перемещения. Работает с id_col."""
    HANDLE_SIZE = 24

    def __init__(self, target_item: 'ControlGraphicsItem', collection: CollectionManager, dialog=None):
        super().__init__()
        self.target_item = target_item
        self.collection = collection
        self.dialog = dialog
        self.is_dragging = False
        self.drag_start = QPointF()
        self.setZValue(10000)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self._icon = QGraphicsSimpleTextItem("✋", self)
        font = QFont("Arial", 14, QFont.Weight.Bold)
        self._icon.setFont(font)
        self._icon.setBrush(QBrush(QColor(255, 255, 255)))
        self._icon.setPos(2, 2)
        self.setRect(0, 0, self.HANDLE_SIZE, self.HANDLE_SIZE)

    def setRect(self, x, y, w, h):
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)

    def rect(self):
        return self._rect

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setBrush(QBrush(QColor(0, 120, 215)))
        painter.setPen(QPen(QColor(0, 90, 180), 2.0))
        painter.drawRoundedRect(self._rect, 4, 4)
        painter.restore()

    def update_position(self):
        if not self.target_item:
            return
        target_rect = self.target_item.rect()
        target_pos = self.target_item.scenePos()
        new_x = target_pos.x() - self.HANDLE_SIZE / 2
        new_y = target_pos.y() + target_rect.height() - self.HANDLE_SIZE / 2
        self.setPos(new_x, new_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.target_item:
            self.is_dragging = True
            self.drag_start = event.scenePos()
            self.grabMouse()

            # idCol-выделение
            selected_ids = list(self.dialog.collection.selected_ids)
            self.start_positions = {}
            for idcol in selected_ids:
                item = self.dialog.graphics_items.get(idcol)
                if item:
                    self.start_positions[idcol] = (item.pos().x(), item.pos().y())
            if not self.start_positions:
                self.start_positions[self.target_item.id_col] = (
                    self.target_item.pos().x(), self.target_item.pos().y()
                )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            total_delta = event.scenePos() - self.drag_start
            grid_enabled = hasattr(self.dialog, 'btn_grid') and self.dialog.btn_grid.isChecked()
            grid_step = 10
            if grid_enabled and hasattr(self.dialog, 'grid_size_combo'):
                try:
                    grid_step = int(self.dialog.grid_size_combo.currentText())
                except ValueError:
                    grid_step = 10

            for idcol, (start_x, start_y) in getattr(self, 'start_positions', {}).items():
                item = self.dialog.graphics_items.get(idcol)
                if item:
                    target_x = start_x + total_delta.x()
                    target_y = start_y + total_delta.y()
                    if grid_enabled:
                        target_x = round(target_x / grid_step) * grid_step
                        target_y = round(target_y / grid_step) * grid_step
                    item.setPos(target_x, target_y)

            self.update_position()
            if getattr(self.dialog, '_active_resize_h_handle', None):
                self.dialog._active_resize_h_handle.update_position()
            if getattr(self.dialog, '_active_resize_v_handle', None):
                self.dialog._active_resize_v_handle.update_position()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.ungrabMouse()

            selected_ids = list(self.dialog.collection.selected_ids)
            if selected_ids:
                if hasattr(self.dialog, 'properties_table') and self.dialog.properties_table:
                    self.dialog.properties_table.blockSignals(True)

                mgr = self.dialog.collection
                changed_props = []

                for idcol in selected_ids:
                    item = self.dialog.graphics_items.get(idcol)
                    if not item or not item.control_widget:
                        continue
                    elem_data = mgr.get_element_by_id_col(idcol)
                    if not elem_data:
                        continue
                    db_id = elem_data['db_id']
                    w = item.control_widget
                    actual_x = int(item.pos().x())
                    actual_y = int(item.pos().y())

                    col = mgr.get_property_collection(db_id)
                    if not col:
                        continue

                    prop_x = col.get('myx')
                    prop_y = col.get('myy')

                    with mgr.silent_mode():
                        if prop_x is not None:
                            mgr.update_property_value_by_id_col(
                                prop_x.id_col, str(actual_x), source='vizivig'
                            )
                            changed_props.append((prop_x.id_col, db_id, prop_x, w))
                        if prop_y is not None:
                            mgr.update_property_value_by_id_col(
                                prop_y.id_col, str(actual_y), source='vizivig'
                            )
                            changed_props.append((prop_y.id_col, db_id, prop_y, w))

                for prop_id_col, _eid, _prop, _w in changed_props:
                    mgr.apply_property_to_widget_by_id_col(prop_id_col)

                if hasattr(self.dialog, 'properties_table') and self.dialog.properties_table:
                    self.dialog.properties_table.blockSignals(False)
                    for prop_id_col, _eid, _prop, _w in changed_props:
                        self.dialog._refresh_cell_by_idcol(prop_id_col)
                    self.dialog.update_properties_panel()

            event.accept()
        else:
            super().mouseReleaseEvent(event)


class ResizeHandleItem(QGraphicsObject):
    """Плавающий хендл ресайза. Работает с id_col."""
    HANDLE_SIZE = 20

    def __init__(self, target_item: 'ControlGraphicsItem', collection: CollectionManager, axis: str, dialog=None):
        super().__init__()
        self.target_item = target_item
        self.collection = collection
        self.axis = axis
        self.dialog = dialog
        self.is_resizing = False
        self.drag_start = QPointF()
        self.setZValue(10000)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        cursor = Qt.CursorShape.SizeHorCursor if axis == 'horizontal' else Qt.CursorShape.SizeVerCursor
        self.setCursor(QCursor(cursor))
        icon_text = "" if axis == 'horizontal' else "↕"
        self._icon = QGraphicsSimpleTextItem(icon_text, self)
        font = QFont("Arial", 12, QFont.Weight.Bold)
        self._icon.setFont(font)
        self._icon.setBrush(QBrush(QColor(255, 255, 255)))
        self._icon.setPos(2, 1)
        self.setRect(0, 0, self.HANDLE_SIZE, self.HANDLE_SIZE)

    def setRect(self, x, y, w, h):
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)

    def rect(self):
        return self._rect

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        painter.save()
        color = QColor(0, 150, 50) if self.axis == 'horizontal' else QColor(150, 0, 150)
        border = QColor(0, 100, 30) if self.axis == 'horizontal' else QColor(100, 0, 100)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(border, 2.0))
        painter.drawRoundedRect(self._rect, 4, 4)
        painter.restore()

    def update_position(self):
        if not self.target_item:
            return
        target_rect = self.target_item.rect()
        target_pos = self.target_item.scenePos()
        if self.axis == 'horizontal':
            new_x = target_pos.x() + target_rect.width() - self.HANDLE_SIZE / 2
            new_y = target_pos.y() + target_rect.height() / 2 - self.HANDLE_SIZE / 2
        else:
            new_x = target_pos.x() + target_rect.width() / 2 - self.HANDLE_SIZE / 2
            new_y = target_pos.y() + target_rect.height() - self.HANDLE_SIZE / 2
        self.setPos(new_x, new_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.target_item:
            self.is_resizing = True
            self.drag_start = event.scenePos()
            self.grabMouse()

            selected_ids = list(self.dialog.collection.selected_ids)
            self.start_geometries = {}
            for idcol in selected_ids:
                item = self.dialog.graphics_items.get(idcol)
                if item and item.control_widget:
                    w = item.control_widget
                    self.start_geometries[idcol] = (w.width(), w.height(), item.pos().x(), item.pos().y())
            if not self.start_geometries:
                self.start_geometries[self.target_item.id_col] = (
                    self.target_item.control_widget.width(),
                    self.target_item.control_widget.height(),
                    self.target_item.pos().x(),
                    self.target_item.pos().y()
                )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing and self.target_item:
            total_delta = event.scenePos() - self.drag_start
            grid_enabled = hasattr(self.dialog, 'btn_grid') and self.dialog.btn_grid.isChecked()
            grid_step = 10
            if grid_enabled and hasattr(self.dialog, 'grid_size_combo'):
                try:
                    grid_step = int(self.dialog.grid_size_combo.currentText())
                except ValueError:
                    grid_step = 10

            for idcol, (start_w, start_h, start_x, start_y) in getattr(self, 'start_geometries', {}).items():
                item = self.dialog.graphics_items.get(idcol)
                if not item:
                    continue
                item.setPos(start_x, start_y)
                if self.axis == 'horizontal':
                    target_w = start_w + total_delta.x()
                    if grid_enabled:
                        target_w = round(target_w / grid_step) * grid_step
                    new_w = max(20, target_w)
                    if item.control_widget:
                        item.control_widget.resize(int(new_w), int(start_h))
                    if hasattr(item, 'set_rect'):
                        item.set_rect(0, 0, new_w + 4, start_h + 4)
                else:
                    target_h = start_h + total_delta.y()
                    if grid_enabled:
                        target_h = round(target_h / grid_step) * grid_step
                    new_h = max(20, target_h)
                    if item.control_widget:
                        item.control_widget.resize(int(start_w), int(new_h))
                    if hasattr(item, 'set_rect'):
                        item.set_rect(0, 0, start_w + 4, new_h + 4)
                if item.proxy and item.control_widget:
                    item.proxy.setGeometry(2, 2, item.control_widget.width(), item.control_widget.height())

            self.update_position()
            event.accept()
            return
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_resizing:
            self.is_resizing = False
            self.ungrabMouse()
            if self.target_item:
                self.target_item.is_resizing = False

            if hasattr(self.dialog, 'properties_table') and self.dialog.properties_table:
                self.dialog.properties_table.blockSignals(True)

            mgr = self.dialog.collection
            changed_props = []

            for idcol, (start_w, start_h, start_x, start_y) in getattr(self, 'start_geometries', {}).items():
                item = self.dialog.graphics_items.get(idcol)
                if not item:
                    continue
                item.is_resizing = False
                if not item.control_widget:
                    continue
                elem_data = mgr.get_element_by_id_col(idcol)
                if not elem_data:
                    continue
                db_id = elem_data['db_id']

                w = item.control_widget
                col = mgr.get_property_collection(db_id)
                if not col:
                    continue

                prop_x = col.get('myx')
                prop_y = col.get('myy')
                if self.axis == 'horizontal':
                    prop_size = col.get('mywidth')
                    actual_size = w.width()
                else:
                    prop_size = col.get('myheight')
                    actual_size = w.height()

                with mgr.silent_mode():
                    if prop_x is not None:
                        mgr.update_property_value_by_id_col(
                            prop_x.id_col, str(int(start_x)), source='vizivig'
                        )
                        changed_props.append((prop_x.id_col, db_id, prop_x, w))
                    if prop_y is not None:
                        mgr.update_property_value_by_id_col(
                            prop_y.id_col, str(int(start_y)), source='vizivig'
                        )
                        changed_props.append((prop_y.id_col, db_id, prop_y, w))
                    if prop_size is not None:
                        mgr.update_property_value_by_id_col(
                            prop_size.id_col, str(actual_size), source='vizivig'
                        )
                        changed_props.append((prop_size.id_col, db_id, prop_size, w))

                for prop_id_col, _eid, _prop, _w in changed_props:
                    mgr.apply_property_to_widget_by_id_col(prop_id_col)

            if hasattr(self.dialog, 'properties_table') and self.dialog.properties_table:
                self.dialog.properties_table.blockSignals(False)
                for prop_id_col, _eid, _prop, _w in changed_props:
                    self.dialog._refresh_cell_by_idcol(prop_id_col)
                self.dialog.update_properties_panel()

            event.accept()
        else:
            super().mouseReleaseEvent(event)


class ControlGraphicsItem(QGraphicsObject):
    """Графический элемент. Индексируется в graphics_items по id_col."""
    selected_changed = Signal(object, bool)
    geometry_changed = Signal(QRectF)

    def __init__(self, id_col: int, db_id: int, control_widget,
                 parent=None, collection=None, is_logical=False):
        super().__init__(parent)
        self.id_col = id_col          # ключ навигации на сцене
        self.db_id = db_id            # DB-ID для сохранения
        self.control_widget = control_widget
        self.collection = collection
        self.is_logical = is_logical
        self.is_selected = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.proxy = None
        self.set_rect(0, 0, 150, 40)

        if self.is_logical:
            self._pen = QPen(QColor(150, 150, 150), 1.0, Qt.PenStyle.DashLine)
            self._brush = QBrush(QColor(245, 245, 245, 150))
        else:
            self._pen = QPen(QColor(100, 100, 150), 1.5)
            self._brush = QBrush(QColor(240, 240, 255, 200))

    def refresh_from_widget(self):
        if not self.control_widget:
            return
        w = self.control_widget
        self.prepareGeometryChange()
        saved_x = self.pos().x()
        saved_y = self.pos().y()
        self._rect = QRectF(0, 0, max(20, w.width() + 4), max(20, w.height() + 4))
        self.setPos(saved_x, saved_y)
        if self.proxy:
            self.proxy.setPos(2, 2)
            self.proxy.resize(max(20, w.width()), max(20, w.height()))
        self.update()
        self.geometry_changed.emit(self._rect)

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def set_rect(self, x, y, w, h):
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)
        if self.proxy:
            self.proxy.setPos(2, 2)
            self.proxy.resize(max(20, w - 4), max(20, h - 4))
        self.update()
        self.geometry_changed.emit(self._rect)

    def itemChange(self, change, value):
        change_name = getattr(change, 'name', '') or str(change)
        if 'ItemChildGeometryChange' in change_name:
            return None
        if 'ItemPositionHasChanged' in change_name:
            if hasattr(self, '_rect'):
                self.geometry_changed.emit(self._rect)
        return super().itemChange(change, value)

    def rect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.save()
        is_really_selected = False
        if self.collection and self.id_col in self.collection.selected_ids:
            is_really_selected = True

        if is_really_selected:
            painter.setBrush(QBrush(QColor(200, 220, 255, 200)))
            painter.setPen(QPen(QColor(0, 120, 215), 2.5, Qt.SolidLine))
        else:
            painter.setBrush(self._brush)
            painter.setPen(self._pen)

        painter.drawRoundedRect(self._rect, 4, 4)

        if self.is_logical or not self.proxy or not self.control_widget:
            painter.setPen(QPen(QColor(120, 120, 120) if self.is_logical else QColor(50, 50, 80)))
            font = QFont("Arial", 8)
            if self.is_logical:
                font.setItalic(True)
            painter.setFont(font)
            label = getattr(self.control_widget, 'objectName', f"idCol={self.id_col} (DB={self.db_id})")
            if self.is_logical:
                label = f"[COL] {label}"
            painter.drawText(self._rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    def set_geometry(self, x: float, y: float, width: float, height: float):
        self.setPos(x, y)
        self.set_rect(0, 0, max(30, width), max(20, height))

    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()
            self.selected_changed.emit(self, selected)

    def sceneEventFilter(self, watched, event):
        if watched == self.proxy and event.type() == QEvent.Type.GraphicsSceneMousePress:
            if event.button() == Qt.MouseButton.LeftButton:
                return False
        return super().sceneEventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            event.accept()
            return
        super().mousePressEvent(event)


class MozartGraphicsView(QGraphicsView):
    """Кастомный View. Работает строго с id_col."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._drag_rect_item: Optional[QGraphicsRectItem] = None
        self._drag_rect_start: Optional[QPointF] = None
        self._potential_cgi: Optional['ControlGraphicsItem'] = None
        self.dialog = None
        self.DRAG_THRESHOLD = 5

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        items_at_pos = self.scene().items(scene_pos)
        for item in items_at_pos:
            if isinstance(item, (MoveHandleItem, ResizeHandleItem)):
                super().mousePressEvent(event)
                return

        item_at_pos = items_at_pos[0] if items_at_pos else None
        cgi = self._find_cgi(item_at_pos)

        if event.button() == Qt.MouseButton.RightButton:
            if cgi and self.dialog and cgi.id_col in self.dialog.collection.selected_ids:
                self.dialog._show_context_menu(scene_pos)
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_rect_start = scene_pos
            self._potential_cgi = cgi
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_rect_start:
            scene_pos = self.mapToScene(event.pos())
            delta = scene_pos - self._drag_rect_start
            if (abs(delta.x()) > self.DRAG_THRESHOLD or abs(delta.y()) > self.DRAG_THRESHOLD) and not self._drag_rect_item:
                is_root_container = False
                if self._potential_cgi and self.dialog:
                    elem = self.dialog.collection.get_element_by_id_col(self._potential_cgi.id_col)
                    if elem and elem.get('cclass') == 'container' and elem.get('parent_id') is None:
                        is_root_container = True

                if not self._potential_cgi or is_root_container:
                    ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
                    if not ctrl and self.dialog:
                        self.dialog._clear_all_selection_visuals()
                        self.dialog.collection.clear_selection()
                        self.dialog._update_active_handles()

                    self._drag_rect_item = QGraphicsRectItem(QRectF(self._drag_rect_start, self._drag_rect_start))
                    self._drag_rect_item.setPen(QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine))
                    self._drag_rect_item.setBrush(QBrush(QColor(0, 120, 215, 40)))
                    self._drag_rect_item.setZValue(5000)
                    self.scene().addItem(self._drag_rect_item)

            if self._drag_rect_item:
                rect = QRectF(self._drag_rect_start, scene_pos).normalized()
                self._drag_rect_item.setRect(rect)
                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        items_at_pos = self.scene().items(scene_pos)
        for item in items_at_pos:
            if isinstance(item, (MoveHandleItem, ResizeHandleItem)):
                super().mouseReleaseEvent(event)
                return

        if event.button() == Qt.MouseButton.LeftButton:
            ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self._drag_rect_item and self._drag_rect_start:
                rect = QRectF(self._drag_rect_start, scene_pos).normalized()
                self.scene().removeItem(self._drag_rect_item)
                self._drag_rect_item = None
                self._drag_rect_start = None
                self._potential_cgi = None

                hit_idcols = []
                container_idcol = None
                if self.dialog:
                    for idcol, item in self.dialog.graphics_items.items():
                        elem = self.dialog.collection.get_element_by_id_col(idcol)
                        if not elem:
                            continue
                        if elem.get('cclass') == 'container' and elem.get('parent_id') is None:
                            continue
                        item_rect = item.sceneBoundingRect()
                        if rect.intersects(item_rect):
                            hit_idcols.append(idcol)
                            if container_idcol is None:
                                parent_db_id = elem.get('parent_id')
                                if parent_db_id:
                                    p_idcol = self.dialog.collection._get_id_col_by_db_id(parent_db_id)
                                    if p_idcol:
                                        container_idcol = p_idcol

                    if hit_idcols:
                        same_container_idcols = []
                        for idcol in hit_idcols:
                            elem = self.dialog.collection.get_element_by_id_col(idcol)
                            if not elem:
                                continue
                            parent_db_id = elem.get('parent_id')
                            if parent_db_id is None and container_idcol is None:
                                same_container_idcols.append(idcol)
                            elif parent_db_id:
                                p_idcol = self.dialog.collection._get_id_col_by_db_id(parent_db_id)
                                if p_idcol == container_idcol:
                                    same_container_idcols.append(idcol)

                        if same_container_idcols:
                            if not ctrl:
                                self.dialog._clear_all_selection_visuals()
                                self.dialog.collection.clear_selection()
                            if ctrl:
                                for idcol in same_container_idcols:
                                    self.dialog.collection.add_to_selection(idcol)
                            else:
                                self.dialog.collection.set_selection(same_container_idcols, container_idcol)

                            for idcol in self.dialog.collection.selected_ids:
                                g_item = self.dialog.graphics_items.get(idcol)
                                if g_item:
                                    g_item.is_selected = True

                            self.dialog._update_selection_visuals()
                            self.dialog.update_properties_panel()

                self.dialog._update_active_handles()
                event.accept()
                return
            else:
                self._drag_rect_item = None
                self._drag_rect_start = None
                cgi = self._potential_cgi
                self._potential_cgi = None

                if cgi:
                    if self.dialog:
                        elem = self.dialog.collection.get_element_by_id_col(cgi.id_col)
                        if elem and not (elem.get('cclass') == 'container' and elem.get('parent_id') is None):
                            for idcol, item in self.dialog.graphics_items.items():
                                el = self.dialog.collection.get_element_by_id_col(idcol)
                                if el and el.get('cclass') == 'container' and el.get('parent_id') is None:
                                    item.set_selected(False)
                        self.dialog._handle_click_selection(cgi, ctrl)
                else:
                    if not ctrl and self.dialog:
                        self.dialog._clear_all_selection_visuals()
                        self.dialog.collection.clear_selection()
                        self.dialog.update_properties_panel()
                        self.dialog._update_active_handles()
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def _find_cgi(self, item) -> Optional['ControlGraphicsItem']:
        if isinstance(item, list):
            if not item:
                return None
            item = item[0]
        while item:
            if isinstance(item, ControlGraphicsItem):
                return item
            item = item.parentItem()
        return None

class ClassEditDialog(QDialog):
    """Диалог редактирования класса. v7.5 STRICT IDCOL."""

    def __init__(self, parent=None, db: DatabaseService = None,
                 version_id: int = -1, mode: str = 'add'):
        super().__init__(None)
        self._is_updating_table = False
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        self.db = db
        self.version_id = version_id
        self.mode = mode
        self.class_service = ClassDataService(db) if db else None
        self.translator = LocalTranslator()

        self.collection = CollectionManager()
        # v7.5: graphics_items — это прямая ссылка на словарь коллекции.
        # Ключи — id_col (НЕ DB-ID). Один источник правды.
        self.graphics_items: Dict[int, 'ControlGraphicsItem'] = self.collection._graphics_items

        self.class_data = None
        self.class_name = ""
        self._loaded_dt_start = None
        self._active_move_handle: Optional['MoveHandleItem'] = None
        self._active_resize_h_handle: Optional['ResizeHandleItem'] = None
        self._active_resize_v_handle: Optional['ResizeHandleItem'] = None

        # === DEBUG INSPECTOR ===
        self.debug_inspector: Optional['DebugCollectionInspector'] = None
        if isDebug:
            from dialogs.debug_collection_inspector import DebugCollectionInspector
            self.debug_inspector = DebugCollectionInspector(self, self.collection)
            self.debug_inspector.save_requested.connect(self._do_debug_save)

        self.setWindowTitle(self.translator.tr('dialog_edit_class'))
        self.resize(1200, 800)

        self.setup_ui()

        from core.change_log import change_log
        change_log.subscribe(self._on_model_changed_reactive)

        self.load_source_classes()
        self.source_tree.itemDoubleClicked.connect(self.inject_class)
        if mode == 'edit' and version_id > 0:
            self.load_class_data(version_id)


    def closeEvent(self, event):
        """Очистка подписок при закрытии окна конфигуратора."""
        from core.change_log import change_log
        change_log.unsubscribe(self._on_model_changed_reactive)

        if self.debug_inspector:
            try:
                self.debug_inspector.close()
            except RuntimeError:
                pass
        super().closeEvent(event)

    def _toggle_debug_panel(self, visible: bool):
        """Переключает видимость панели инспектора."""
        if self.debug_inspector:
            if visible:
                self.debug_inspector.show()
            else:
                self.debug_inspector.hide()

    def _do_debug_save(self):
        """Сохранение по запросу из Debug Inspector."""
        if self.debug_inspector:
            self.debug_inspector.add_log("[DEBUG SAVE] Вызов _do_save(force_new=False, silent=False)")
        try:
            self._do_save(force_new=False, silent=False)
            if self.debug_inspector:
                self.debug_inspector.add_log("[DEBUG SAVE] Сохранение завершено успешно!")
                self.debug_inspector.refresh_tree()
        except Exception as e:
            if self.debug_inspector:
                self.debug_inspector.add_log(f"[DEBUG SAVE ERROR] {e}")
            import traceback
            traceback.print_exc()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        toolbar = QToolBar()

        self.btn_grid = QPushButton(self.translator.tr('btn_grid_on'))
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        toolbar.addWidget(self.btn_grid)
        toolbar.addSeparator()

        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(['5', '10', '15', '20', '25', '30', '50', '100'])
        self.grid_size_combo.setCurrentText('10')
        toolbar.addWidget(QLabel(self.translator.tr('label_grid_step')))
        toolbar.addWidget(self.grid_size_combo)
        toolbar.addSeparator()

        self.btn_methods = QPushButton(self.translator.tr('btn_methods'))
        self.btn_signals = QPushButton(self.translator.tr('btn_signals'))
        toolbar.addWidget(self.btn_methods)
        toolbar.addWidget(self.btn_signals)
        self.btn_methods.clicked.connect(self._on_btn_methods_clicked)
        self.btn_signals.clicked.connect(self.show_signals_dialog)

        self.class_info_label = QLabel("")
        toolbar.addWidget(self.class_info_label)
        toolbar.addSeparator()

        if self.debug_inspector is not None:
            btn_toggle_debug = QPushButton("🔍 Inspector")
            btn_toggle_debug.setCheckable(True)
            btn_toggle_debug.setChecked(True)
            btn_toggle_debug.toggled.connect(lambda checked: self.debug_inspector.setVisible(checked))
            toolbar.addWidget(btn_toggle_debug)
            toolbar.addSeparator()

        toolbar.addWidget(QLabel("Порядок загрузки:"))
        self.load_order_spin = QSpinBox()
        self.load_order_spin.setRange(0, 100000)
        self.load_order_spin.setValue(100)
        toolbar.addWidget(self.load_order_spin)

        main_layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setStyleSheet("""
        QSplitter::handle { background-color: #d0d0d0; }
        QSplitter::handle:hover { background-color: #a0a0a0; }
        """)

        splitter.addWidget(self._create_source_panel())
        splitter.addWidget(self._create_scene_panel())
        splitter.addWidget(self._create_properties_panel())
        splitter.setSizes([250, 700, 250])
        main_layout.addWidget(splitter)

        self.properties_table.itemChanged.connect(self._on_table_item_changed)
        self.properties_table.itemDoubleClicked.connect(self._on_property_double_clicked)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_save.clicked.connect(self.save_class)
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        self.btn_grid.toggled.connect(self.toggle_grid)
        self.grid_size_combo.currentTextChanged.connect(self.on_grid_size_changed)

    def _on_model_changed_reactive(self, event):
        """
        Реактивный слот: ловит изменения из change_log и точечно обновляет UI.
        v7.5: проверка выделения — по idCol элемента (selected_ids хранит idCol).
        """
        from core.constants import SILENT_SOURCES, GEOMETRY_PROPS

        if event.source in SILENT_SOURCES:
            return

        if event.kind in ('prop_value', 'prop_delete', 'prop_meta'):
            elem_data = None
            if event.id_col is not None:
                prop = self.collection.get_property_by_id_col(event.id_col)
                if prop is not None:
                    owner_db_id = prop.owner_element_id
                    owner_idcol = self.collection._get_id_col_by_db_id(owner_db_id)
                    if owner_idcol:
                        elem_data = self.collection.get_element_by_id_col(owner_idcol)

            if not elem_data:
                return

            elem_idcol = elem_data.get('id_col')
            if not elem_idcol or elem_idcol not in self.collection.selected_ids:
                return

            from PySide6.QtCore import QTimer
            prop_cname = event.target_name

            if event.id_col is not None:
                QTimer.singleShot(0, lambda idc=event.id_col: self._refresh_cell_by_idcol(idc))
            else:
                QTimer.singleShot(
                    0,
                    lambda eid=elem_data['db_id'], cn=prop_cname:
                        self._refresh_cell_fallback(eid, cn)
                )

            g_item = self.graphics_items.get(elem_idcol)
            if g_item:
                QTimer.singleShot(0, g_item.update)

                if prop_cname in GEOMETRY_PROPS:
                    if event.source != 'manual':
                        QTimer.singleShot(0, self._update_active_handles)

    def _refresh_cell_fallback(self, element_id_col: int, cname: str):
        """
        Fallback для событий без id_col: найти prop по (id_col элемента, cname).
        """
        col = self.collection.get_property_collection(element_id_col)
        if col is None:
            return
        prop = col.get(cname)
        if prop is None:
            return
        if getattr(prop, 'id_col', 0):
            self._refresh_cell_by_idcol(prop.id_col)


    def _on_delete_value_by_idcol(self, prop_id_col: int):
        """Кнопка "×" в таблице свойств. Сбрасывает значение по idCol."""
        prop = self.collection.get_property_by_id_col(prop_id_col)
        if prop is None:
            return

        reply = QMessageBox.question(
            self, "Сброс значения",
            f"Сбросить значение «{prop.cname}»?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        setattr(prop, 'isDelete', False)
        setattr(prop, 'is_deleted', False)

        ok, _ = self.collection.update_property_value_by_id_col(
            prop_id_col, "", source="user_edit_reset"
        )

        if ok:
            self._refresh_cell_by_idcol(prop_id_col)

    def _get_c_base_class(self, db_id: int) -> str:
        """
        Возвращает имя целевого Qt-класса для версии.
        Приоритет:
          1. system_class_name из VirtualClassNode (если линия упёрлась в системный класс);
          2. c_base_class из VirtualClassNode (если это прямой Qt-класс);
          3. 'QWidget' как fallback.
        """
        if db_id > 0:
            node = goProject.class_registry.get_class_version(db_id)
            if node:
                # Если линия упёрлась в системный класс — берём его имя
                if node.system_class_name:
                    return node.system_class_name
                return node.c_base_class or 'QWidget'
        else:
            idcol = self.collection._get_id_col_by_db_id(db_id)
            if idcol:
                elem_data = self.collection.get_element_by_id_col(idcol)
                if elem_data:
                    donor_id = elem_data.get('donor_version_id')
                    if donor_id and donor_id > 0:
                        node = goProject.class_registry.get_class_version(donor_id)
                        if node:
                            if node.system_class_name:
                                return node.system_class_name
                            return node.c_base_class or 'QWidget'
        return 'QWidget'

    def _get_meta_for_property(self, db_id: int, cname: str) -> dict:
        """Возвращает объединённые метаданные (Bridge + Override) для свойства."""
        if not goProject.property_bridge_manager:
            return {}
        version_for_meta = db_id if db_id > 0 else self.version_id
        return goProject.property_bridge_manager.get_meta_for_property(version_for_meta, cname)

    def _create_source_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(self.translator.tr('label_inject_classes')))
        self.source_tree = QTreeWidget()
        self.source_tree.setHeaderLabels([self.translator.tr('field_name')])
        self.source_tree.setToolTipDuration(5000)
        layout.addWidget(self.source_tree)
        return panel

    def _create_scene_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 1500)
        self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.view = MozartGraphicsView(self.scene)
        self.view.dialog = self
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.view)
        return panel

    def _create_properties_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(f"<b>{self.translator.tr('label_properties')}:</b>"))

        prop_btn_layout = QHBoxLayout()
        self.btn_prop_add = QPushButton("➕")
        self.btn_prop_edit = QPushButton("📝")
        self.btn_prop_del = QPushButton("❌")
        for btn in (self.btn_prop_add, self.btn_prop_edit, self.btn_prop_del):
            btn.setFixedSize(30, 26)
            prop_btn_layout.addWidget(btn)
        prop_btn_layout.addStretch()
        layout.addLayout(prop_btn_layout)

        self.btn_prop_add.clicked.connect(self._on_prop_add)
        self.btn_prop_edit.clicked.connect(self._on_prop_edit)
        self.btn_prop_del.clicked.connect(self._on_prop_del)

        self.properties_table = QTableWidget(0, 3)
        self.properties_table.setHorizontalHeaderLabels([
            self.translator.tr('field_property'),
            self.translator.tr('field_value'),
            ""
        ])
        self.properties_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.properties_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.properties_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.properties_table.setColumnWidth(2, 30)
        self.properties_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)

        layout.addWidget(self.properties_table, 2)

        layout.addWidget(QLabel(f"<b>{self.translator.tr('field_description')} класса:</b>"))
        self.edit_class_comment = QTextEdit()
        self.edit_class_comment.setPlaceholderText("Введите бизнес-описание назначения данного класса...")
        self.edit_class_comment.setMaximumHeight(150)
        layout.addWidget(self.edit_class_comment, 1)

        return panel

    def update_properties_panel(self):
        """
        Обновляет таблицу свойств для последнего выделенного элемента.
        v7.5: selected_ids хранит idCol, извлекаем элемент по idCol.
        get_property_collection принимает id_col.
        """
        from PySide6.QtGui import QBrush, QColor, QFont
        from core.constants import GEOMETRY_PROPS

        self.properties_table.blockSignals(True)
        self.properties_table.setRowCount(0)

        if not self.collection.selected_ids:
            self.properties_table.blockSignals(False)
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element_by_id_col(last_idcol)
        if not elem_data:
            self.properties_table.blockSignals(False)
            return

        db_id = elem_data['db_id']

        sys_props = [
            ('db_id', 'DB-ID', str(db_id)),
            ('calias', self.translator.tr('field_alias'), elem_data.get('calias', '')),
            ('cclass', 'Тип (класс)', str(elem_data.get('cclass', ''))),
        ]
        for prop_key, prop_label, prop_value in sys_props:
            row = self.properties_table.rowCount()
            self.properties_table.insertRow(row)
            self.properties_table.setItem(row, 0, QTableWidgetItem(prop_label))
            val_item = QTableWidgetItem(prop_value)
            val_item.setData(Qt.ItemDataRole.UserRole, prop_key)
            val_item.setData(Qt.ItemDataRole.UserRole + 1, "system")
            val_item.setData(Qt.ItemDataRole.UserRole + 3, None)
            self.properties_table.setItem(row, 1, val_item)
            if prop_key in ('db_id', 'cclass'):
                val_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

        # ✅ FIX: передаём id_col, а не db_id
        col = self.collection.get_property_collection(last_idcol)
        if col is None:
            self.properties_table.blockSignals(False)
            return

        g_item = self.graphics_items.get(last_idcol)
        widget = g_item.control_widget if g_item else None

        base_qt_class = self._get_c_base_class(db_id)
        qt_bridge_props = goProject.property_bridge_manager.get_properties_for_class(base_qt_class) or {}

        for prop in col.all_ordered():
            row = self.properties_table.rowCount()
            self.properties_table.insertRow(row)

            meta = self._get_meta_for_property(db_id, prop.cname) or {}
            ui_label = (meta.get('ui_label_ru') or
                        getattr(prop, 'ui_label_ru', None) or
                        qt_bridge_props.get(prop.cname, {}).get('ui_label', prop.cname))
            self.properties_table.setItem(row, 0, QTableWidgetItem(str(ui_label)))

            raw_value = str(prop.value) if prop.value is not None else ""
            display_value = raw_value

            if getattr(prop, 'isDelete', False):
                display_value = "(удалено)"
            elif prop.is_blob:
                size = len(prop.blob_value) if prop.blob_value else 0
                display_value = f"[BLOB:{prop.blob_name or ''}, {size}B]"
            else:
                bridge_get_method = (meta.get('bridgecalcget') or
                                     getattr(prop, 'bridgecalcget', None) or
                                     qt_bridge_props.get(prop.cname, {}).get('bridgecalcget'))
                if bridge_get_method and widget:
                    try:
                        translated = goProject.property_bridge_manager.read_property_from_widget(
                            widget, prop, version_id=db_id, collection=col
                        )
                        if translated is not None and str(translated).strip() != "":
                            display_value = str(translated)
                        elif raw_value != "":
                            display_value = raw_value
                    except Exception as e:
                        if isDebug:
                            print(f"[Inspector] Ошибка bridgecalcget '{bridge_get_method}' для {prop.cname}: {e}")
                        display_value = raw_value

            item = QTableWidgetItem(display_value)
            item.setData(Qt.ItemDataRole.UserRole, prop.cname)
            item.setData(Qt.ItemDataRole.UserRole + 1, "text")
            item.setData(Qt.ItemDataRole.UserRole + 2, prop.id)
            item.setData(Qt.ItemDataRole.UserRole + 3, prop.id_col)

            func_sel = (meta.get('fuuncselectionvalue') or
                        getattr(prop, 'fuuncselectionvalue', None) or
                        qt_bridge_props.get(prop.cname, {}).get('fuuncselectionvalue'))
            if func_sel:
                item.setText(display_value + " [...]")
                item.setForeground(QBrush(QColor(0, 85, 180)))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole + 1, "select")

            if prop.cname in GEOMETRY_PROPS:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setBackground(QBrush(QColor(235, 235, 235)))
                item.setToolTip("Геометрия меняется только на сцене (визивиг)")

            is_dirty = (getattr(prop, 'isDirty', False) or
                        getattr(prop, 'isDelete', False) or
                        getattr(prop, 'is_changed', False) or
                        getattr(prop, 'is_property_changed', False))
            if is_dirty:
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            self.properties_table.setItem(row, 1, item)

            btn_del = QPushButton("×")
            btn_del.setFixedSize(24, 24)
            btn_del.setToolTip("Удалить значение")
            btn_del.clicked.connect(
                lambda checked=False, idc=prop.id_col:
                    self._on_delete_value_by_idcol(idc)
            )
            self.properties_table.setCellWidget(row, 2, btn_del)

        self.properties_table.blockSignals(False)

        if self.debug_inspector:
            self.debug_inspector.add_log(f"[UI] Панель свойств обновлена для idCol={last_idcol}")

    def _on_property_double_clicked(self, item):
        """v7.5: берём idCol из UserRole + 3."""
        if item.column() != 1:
            return
        prop_id_col = item.data(Qt.ItemDataRole.UserRole + 3)
        if not prop_id_col:
            return

        prop = self.collection.get_property_by_id_col(prop_id_col)
        if prop is None:
            return

        db_id = prop.owner_element_id
        meta = self._get_meta_for_property(db_id, prop.cname) or {}
        func_sel = meta.get('fuuncselectionvalue') or prop.fuuncselectionvalue

        if func_sel:
            self._open_select_dialog_by_idcol(prop_id_col)

    def _on_table_item_changed(self, item):
        """
        Обработчик изменения ячейки в таблице свойств (ручной ввод).
        v7.5: get_property_collection принимает id_col.
        """
        if self._is_updating_table:
            return
        if item.column() != 1:
            return

        cname = item.data(Qt.ItemDataRole.UserRole)
        prop_type = item.data(Qt.ItemDataRole.UserRole + 1)

        if prop_type in ("system", "select"):
            return

        if not self.collection.selected_ids:
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element_by_id_col(last_idcol)
        if not elem_data:
            return
        db_id = elem_data['db_id']

        # ✅ FIX: по id_col
        col = self.collection.get_property_collection(last_idcol)
        if not col:
            return

        prop = col.get(cname)
        if not prop:
            return

        prop_id_col = item.data(Qt.ItemDataRole.UserRole + 3)
        if not prop_id_col:
            prop_id_col = getattr(prop, 'id_col', None)
        if not prop_id_col:
            if isDebug:
                print(f"[_on_table_item_changed] У свойства {cname} нет id_col")
            return

        new_raw_value = item.text().strip()
        if new_raw_value.endswith(" [...]"):
            new_raw_value = new_raw_value[:-5].strip()

        self._is_updating_table = True
        try:
            if getattr(prop, 'isDelete', False):
                prop.isDelete = False

            ok, old_val = self.collection.update_property_value_by_id_col(
                prop_id_col, new_raw_value, source="user_edit"
            )

            if not ok:
                self._refresh_cell_by_idcol(prop_id_col)
                return

            g_item = self.graphics_items.get(last_idcol)
            widget = g_item.control_widget if g_item else None

            display_value = goProject.property_bridge_manager.read_property_from_widget(
                widget, prop, version_id=db_id, collection=col
            )
            if display_value is not None and str(display_value) != new_raw_value:
                item.setText(str(display_value))
        finally:
            self._is_updating_table = False


    def _refresh_cell_by_idcol(self, prop_id_col: int):
        """v7.5: точечно обновляет текст ячейки по idCol свойства."""
        if not prop_id_col:
            return

        prop = self.collection.get_property_by_id_col(prop_id_col)
        if prop is None:
            return

        db_id = prop.owner_element_id
        owner_idcol = self.collection._get_id_col_by_db_id(db_id)
        g_item = self.graphics_items.get(owner_idcol) if owner_idcol else None
        widget = g_item.control_widget if g_item else None

        for row in range(self.properties_table.rowCount()):
            item = self.properties_table.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole + 3) == prop_id_col:

                if getattr(prop, 'isDelete', False):
                    display_value = "(удалено)"
                elif prop.is_blob:
                    size = len(prop.blob_value) if prop.blob_value else 0
                    display_value = f"[BLOB:{prop.blob_name or ''}, {size}B]"
                else:
                    meta = self._get_meta_for_property(db_id, prop.cname) or {}
                    bridge_get_method = meta.get('bridgecalcget') or prop.bridgecalcget
                    display_value = prop.value

                    if bridge_get_method and widget:
                        try:
                            # ✅ FIX: по id_col
                            col = self.collection.get_property_collection(owner_idcol) if owner_idcol else None
                            translated = goProject.property_bridge_manager.read_property_from_widget(
                                widget, prop, version_id=db_id, collection=col
                            )
                            if translated is not None and str(translated).strip() != "":
                                display_value = str(translated)
                        except Exception:
                            pass

                meta = self._get_meta_for_property(db_id, prop.cname) or {}
                func_sel = meta.get('fuuncselectionvalue') or prop.fuuncselectionvalue
                marker = " [...]" if func_sel else ""
                new_text = str(display_value) + marker

                if item.text() != new_text:
                    self.properties_table.blockSignals(True)
                    item.setText(new_text)

                    font = item.font()
                    is_dirty = (getattr(prop, 'isDirty', False) or
                                getattr(prop, 'is_changed', False) or
                                getattr(prop, 'is_property_changed', False))
                    font.setBold(is_dirty)
                    item.setFont(font)

                    self.properties_table.blockSignals(False)
                return

    def _open_select_dialog_by_idcol(self, prop_id_col: int):
        """v7.5: открывает диалог выбора значения по idCol."""
        prop = self.collection.get_property_by_id_col(prop_id_col)
        if prop is None:
            return

        db_id = prop.owner_element_id
        owner_idcol = self.collection._get_id_col_by_db_id(db_id)
        g_item = self.graphics_items.get(owner_idcol) if owner_idcol else None
        widget = g_item.control_widget if g_item else None

        meta = self._get_meta_for_property(db_id, prop.cname) or {}
        func_name = meta.get('fuuncselectionvalue') or prop.fuuncselectionvalue
        if not func_name:
            return

        elem_id_col = self.collection.get_element_id_col_by_property_id_col(prop_id_col)

        new_val = None
        try:
            # ✅ FIX: get_property_collection по id_col
            col = self.collection.get_property_collection(owner_idcol) if owner_idcol else None
            new_val = goProject.bridge_resolver.resolve_select(
                func_name,
                db_id if db_id > 0 else self.version_id,
                widget,
                col,
                prop.cname,
                prop.value,
                prop_id_col=prop_id_col,
                element_id_col=elem_id_col,
            )
        except Exception as e:
            if isDebug:
                print(f"[Inspector] Ошибка resolve_select для {func_name}: {e}")
            new_val = None

        if new_val is None and func_name.startswith('select_'):
            lib = goProject.superlibre
            method = getattr(lib, func_name, None)
            if callable(method):
                try:
                    sig = inspect.signature(method)
                    kwargs = {}
                    if 'db' in sig.parameters:
                        kwargs['db'] = self.db
                    if 'prop_id_col' in sig.parameters:
                        kwargs['prop_id_col'] = prop_id_col
                    if 'element_id_col' in sig.parameters:
                        kwargs['element_id_col'] = elem_id_col
                    new_val = method(
                        widget,
                        col,
                        prop.cname,
                        prop.value,
                        **kwargs,
                    )
                except Exception as e:
                    if isDebug:
                        print(f"[Inspector] Ошибка прямого вызова {func_name}: {e}")

        if new_val is None:
            return

        self.collection.update_property_value_by_id_col(
            prop_id_col, str(new_val), source='select'
        )


    def _on_property_value_changed(self, element_id_col: int, cname: str,
                                   value: str, source: str):
        """
        v7.5: Централизованный метод обновления значения свойства.
        Работает с id_col элемента.
        """
        elem_data = self.collection.get_element_by_id_col(element_id_col)
        if not elem_data:
            return
        db_id = elem_data['db_id']

        # ✅ FIX: по id_col
        col = self.collection.get_property_collection(element_id_col)
        if not col:
            return

        prop = col.get(cname)
        if prop and getattr(prop, 'isDelete', False):
            prop.isDelete = False

        col.set_value(cname, value, source=source)

        g_item = self.graphics_items.get(element_id_col)
        widget = g_item.control_widget if g_item else None

        if prop:
            goProject.property_bridge_manager.apply_property_to_widget(
                widget, prop, version_id=db_id
            )

        if prop and getattr(prop, 'id_col', 0):
            self._refresh_cell_by_idcol(prop.id_col)
        else:
            self._refresh_cell_fallback(db_id, cname)

    # =====================================================================
    # prop_add / prop_edit / prop_del
    # =====================================================================

    def _on_prop_add(self):
        """Добавить новое свойство (переопределение метаданных)."""
        if not self.collection.selected_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите элемент")
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element_by_id_col(last_idcol)
        if not elem_data:
            return
        db_id = elem_data['db_id']

        # ✅ FIX: ensure_property_collection принимает id_col
        col = self.collection.ensure_property_collection(last_idcol)
        if col is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить коллекцию свойств")
            return

        from dialogs.property_meta_edit_dialog import PropertyMetaEditDialog
        class_methods = []
        # ✅ FIX: get_method_collection принимает id_col
        method_col = self.collection.get_method_collection(last_idcol)
        if method_col:
            class_methods = [m.c_name for m in method_col.all_ordered()]

        dlg = PropertyMetaEditDialog(
            parent=self,
            element_id=db_id,
            cname="",
            prop=None,
            version_id=self.version_id if db_id < 0 else db_id,
            has_children=False,
            db=self.db,
            superlibre=goProject.superlibre,
            class_methods=class_methods,
            mode='add',
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_data()
        new_cname = data.get('cname')
        if not new_cname:
            return

        meta_kwargs = {
            'ui_label_ru': data.get('ui_label_ru'),
            'editor_type': data.get('editor_type'),
            'qt_target': data.get('qt_target'),
            'translation_strategy': data.get('translation_strategy'),
            'typevalue': data.get('typevalue'),
            'typesourcevalue': data.get('typesourcevalue'),
            'isdefaultepr': data.get('isdefaultepr'),
            'bridgecalcset': data.get('bridgecalcset'),
            'bridgecalcget': data.get('bridgecalcget'),
            'fuuncselectionvalue': data.get('fuuncselectionvalue'),
        }
        prop = col.add_property(new_cname, **meta_kwargs)
        if prop is None:
            QMessageBox.warning(
                self, "Ошибка",
                f"Свойство «{new_cname}» уже существует у этого родителя"
            )
            return

        if data.get('blob_data') is not None:
            col.set_blob(new_cname, data['blob_data'], data.get('blob_name') or '')

        if db_id < 0:
            prop.owner_version_id = None
        else:
            prop.owner_version_id = db_id

        prop.is_property_changed = True
        self.update_properties_panel()


    def _on_prop_edit(self):
        """Редактировать метаданные выбранного свойства."""
        if not self.collection.selected_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите элемент")
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element_by_id_col(last_idcol)
        if not elem_data:
            return
        db_id = elem_data['db_id']

        # ✅ FIX: по id_col
        col = self.collection.get_property_collection(last_idcol)
        if not col:
            QMessageBox.warning(self, "Ошибка", "Нет коллекции свойств")
            return

        row = self.properties_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку свойства")
            return

        item = self.properties_table.item(row, 1)
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите строку свойства")
            return

        cname = item.data(Qt.ItemDataRole.UserRole)
        prop_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if prop_type == "system":
            QMessageBox.warning(self, "Ошибка", "Нельзя редактировать системное свойство")
            return

        prop = col.get(cname)
        if not prop:
            QMessageBox.warning(self, "Ошибка", "Свойство не найдено в коллекции")
            return

        from dialogs.property_meta_edit_dialog import PropertyMetaEditDialog
        class_methods = []
        # ✅ FIX: get_method_collection по id_col
        method_col = self.collection.get_method_collection(last_idcol)
        if method_col:
            class_methods = [m.c_name for m in method_col.all_ordered()]

        dlg = PropertyMetaEditDialog(
            parent=self,
            element_id=db_id,
            cname=cname,
            prop=prop,
            version_id=self.version_id if db_id < 0 else db_id,
            has_children=False,
            db=self.db,
            superlibre=goProject.superlibre,
            class_methods=class_methods,
            mode='edit',
        )
        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_data()
        new_cname = data.get('cname') or cname

        if new_cname != cname:
            if not col.rename_property(cname, new_cname):
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Не удалось переименовать «{cname}» → «{new_cname}»"
                )
                return
            cname = new_cname

        meta_kwargs = {
            'ui_label_ru': data.get('ui_label_ru'),
            'editor_type': data.get('editor_type'),
            'qt_target': data.get('qt_target'),
            'translation_strategy': data.get('translation_strategy'),
            'typevalue': data.get('typevalue'),
            'typesourcevalue': data.get('typesourcevalue'),
            'isdefaultepr': data.get('isdefaultepr'),
            'bridgecalcset': data.get('bridgecalcset'),
            'bridgecalcget': data.get('bridgecalcget'),
            'fuuncselectionvalue': data.get('fuuncselectionvalue'),
        }
        col.set_property_meta(cname, **meta_kwargs)

        if data.get('blob_data') is not None:
            col.set_blob(cname, data['blob_data'], data.get('blob_name') or '')
        elif data.get('blob_removed'):
            col.set_blob(cname, None, '')

        prop = col.get(cname)
        if prop and db_id > 0:
            prop.owner_version_id = db_id

        self.update_properties_panel()



    def _on_prop_del(self):
        """Удалить переопределение свойства (только для локальных)."""
        if not self.collection.selected_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите элемент")
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element_by_id_col(last_idcol)
        if not elem_data:
            return
        db_id = elem_data['db_id']

        # ✅ FIX: по id_col
        col = self.collection.get_property_collection(last_idcol)
        if not col:
            return

        row = self.properties_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку свойства")
            return
        item = self.properties_table.item(row, 1)
        if not item:
            return

        cname = item.data(Qt.ItemDataRole.UserRole)
        prop_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if prop_type == "system":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить системное свойство")
            return

        prop = col.get(cname)
        if not prop:
            return

        owner_vid = getattr(prop, 'owner_version_id', None)
        is_inherited = (owner_vid is not None and db_id > 0 and owner_vid != db_id)
        if is_inherited:
            QMessageBox.warning(
                self, "Ошибка",
                "Нельзя удалить унаследованное свойство. "
                "Можно только переопределить (кнопка 📝)."
            )
            return

        reply = QMessageBox.question(
            self, "Удаление свойства",
            f"Удалить переопределение свойства «{cname}»?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            col.remove_override(cname)
            self.update_properties_panel()


    def _on_delete_value(self, element_id_col: int, cname: str):
        """
        Устаревший метод (для обратной совместимости).
        v7.5: рекомендуется _on_delete_value_by_idcol(prop_id_col).
        """
        col = self.collection.get_property_collection(element_id_col)
        if not col:
            return
        prop = col.get(cname)
        if not prop:
            return

        reply = QMessageBox.question(
            self, "Сброс значения",
            f"Сбросить значение «{cname}»?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        setattr(prop, 'isDelete', False)
        setattr(prop, 'is_deleted', False)

        prop_id_col = getattr(prop, 'id_col', None)
        if not prop_id_col:
            if isDebug:
                print(f"[_on_delete_value] У свойства {cname} нет id_col")
            return

        ok, old_val = self.collection.update_property_value_by_id_col(
            prop_id_col, "", source="user_edit_reset"
        )

        if not ok:
            if isDebug:
                print(f"[_on_delete_value] Апдейтер отверг сброс для {cname}")
            return

        self._refresh_cell_by_idcol(prop_id_col)

    # =====================================================================
    # КОНТЕКСТНОЕ МЕНЮ + REPARENT
    # =====================================================================

    def _show_context_menu(self, scene_pos: QPointF):
        selected = self.collection.selected_ids  # ✅ хранит id_col
        menu = QMenu(self)

        if selected:
            act_reparent = menu.addAction("📦 Включить в контейнер...")
            act_reparent.triggered.connect(lambda: self._reparent_selected())

        if len(selected) >= 2:
            menu.addSeparator()
            act_left = menu.addAction(self.translator.tr('menu_align_left'))
            act_right = menu.addAction(self.translator.tr('menu_align_right'))
            act_top = menu.addAction(self.translator.tr('menu_align_top'))
            act_bottom = menu.addAction(self.translator.tr('menu_align_bottom'))
            menu.addSeparator()
            act_eq_w = menu.addAction(self.translator.tr('menu_equal_width'))
            act_eq_h = menu.addAction(self.translator.tr('menu_equal_height'))

            action = menu.exec(self.view.mapToGlobal(scene_pos.toPoint()))
            if action == act_left:
                self.collection.align_selected('left')
            elif action == act_right:
                self.collection.align_selected('right')
            elif action == act_top:
                self.collection.align_selected('top')
            elif action == act_bottom:
                self.collection.align_selected('bottom')
            elif action == act_eq_w:
                self.collection.equalize_width()
            elif action == act_eq_h:
                self.collection.equalize_height()
        else:
            menu.exec(self.view.mapToGlobal(scene_pos.toPoint()))

        self._update_selection_visuals()
        self.update_properties_panel()
        self._update_active_handles()

    def _reparent_selected(self):
        """v7.5: Перепривязка выбранного объекта к другому контейнеру по idCol."""
        if not self.collection.selected_ids:
            return

        last_idcol = list(self.collection.selected_ids)[-1]
        elem = self.collection.get_element_by_id_col(last_idcol)
        if elem is None:
            return

        if elem.get('isInherited', False):
            QMessageBox.warning(
                self,
                "Перемещение запрещено",
                "Элемент является частью базовой структуры класса. "
                "Перемещение невозможно. Создайте копию элемента, "
                "если требуется изменить его положение."
            )
            return

        if elem.get('isDelete', False):
            QMessageBox.warning(
                self,
                "Перемещение запрещено",
                "Элемент помечен на удаление. Перемещение невозможно."
            )
            return

        from dialogs.select_container_dialog import SelectContainerDialog
        dlg = SelectContainerDialog(parent=self, collection=self.collection, element_id_col=last_idcol)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_parent_idcol = dlg.get_selected_id_col()
        if new_parent_idcol is None:
            return

        new_parent_elem = self.collection.get_element_by_id_col(new_parent_idcol)
        if not new_parent_elem:
            return
        new_parent_db_id = new_parent_elem['db_id']

        current_db_id = elem['db_id']

        if not self.collection.reparent_element(current_db_id, new_parent_db_id):
            QMessageBox.warning(self, "Ошибка", "Не удалось перепривязать объект")
            return

        g_item = self.graphics_items.get(last_idcol)
        new_parent_g_item = self.graphics_items.get(new_parent_idcol)

        if g_item and g_item.proxy and new_parent_g_item:
            g_item.proxy.setParentItem(new_parent_g_item)
            elem_data = self.collection.get_element_by_id_col(last_idcol)
            if elem_data:
                g_item.set_geometry(elem_data.get('x', 0), elem_data.get('y', 0),
                                    elem_data.get('width', 150), elem_data.get('height', 30))
        elif g_item:
            elem_data = self.collection.get_element_by_id_col(last_idcol)
            if elem_data:
                g_item.set_geometry(elem_data.get('x', 0), elem_data.get('y', 0),
                                    elem_data.get('width', 150), elem_data.get('height', 30))

        self.scene.update()
        self.update_properties_panel()


    # =====================================================================
    # СОХРАНЕНИЕ (без изменений — работает по DB-ID)
    # =====================================================================

    def _on_btn_methods_clicked(self):
        if self.mode == 'add' and self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс")
            return
        if self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс")
            return

        status_id = 1
        try:
            res = self.db.execute_query(
                "SELECT status_id FROM class_erp.class_version WHERE id = %s",
                (self.version_id,)
            )
            if res and res[0][0]:
                status_id = int(res[0][0])
        except Exception:
            pass

        has_children = False
        try:
            res = self.db.execute_query(
                "SELECT count(*) FROM class_erp.class_version "
                "WHERE i_base_class = %s AND dt_end IS NULL",
                (self.version_id,)
            )
            if res and res[0][0] and int(res[0][0]) > 0:
                has_children = True
        except Exception:
            pass

        force_new = (status_id == 2) or has_children
        self._do_save(force_new=force_new, silent=True)
        self._refresh_inspector()

        from dialogs.methods_dialog import MethodsDialog
        MethodsDialog(
            self,
            db=self.db,
            version_id=self.version_id,
            class_name=self.class_name,
            collection=self.collection,
        ).exec_()

    def save_class(self):
        if not self.class_service or not self.db:
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Сохранение класса")
        msg_box.setText("Требуется сохранить новую версию класса или обновить текущую?")
        msg_box.setInformativeText("Новая версия — создаст исторический срез. Обновить — перезапишет текущую.")
        btn_new = msg_box.addButton("Новая версия", QMessageBox.AcceptRole)
        btn_update = msg_box.addButton("Обновить текущую", QMessageBox.ActionRole)
        btn_cancel = msg_box.addButton("Отмена", QMessageBox.RejectRole)
        msg_box.setDefaultButton(btn_new)
        msg_box.exec_()
        clicked = msg_box.clickedButton()
        if clicked == btn_cancel:
            return
        force_new = (clicked == btn_new)
        self._do_save(force_new=force_new, silent=False)

    def _do_save(self, force_new: bool, silent: bool = False):
        """
        Единая точка сохранения класса.

        v9 FIX (сценарий C):
        Новый version_id берётся из RAISE NOTICE процедуры
        p_save_class_version_immutable вместо повторного SELECT.
        Это устраняет гонку при параллельных сохранениях.

        v9 FIX (сценарий B):
        Удалённые элементы закрываются и в сценарии «Обновить текущую»,
        а не только в «Новая версия».

        v9 FIX (root db_id):
        В сценарии C _save_properties_for_version получает db_id=root_db_id
        (старый version_id), а не new_version_id, чтобы коллекция свойств
        root была найдена по правильному ключу.
        """
        class_comment = self.edit_class_comment.toPlainText().strip()
        geometry_json = "{}"

        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                if self.mode == 'edit' and self.version_id > 0:
                    if force_new:
                        # === СЦЕНАРИЙ C: Новая версия ===
                        cur.execute(
                            "CALL class_erp.p_save_class_version_immutable"
                            "(%s, %s, %s, %s);",
                            (self.version_id, class_comment, geometry_json, 1)
                        )

                        # Парсим NEW_VERSION_ID из NOTICE
                        new_version_id = None
                        for notice in conn.notices:
                            notice_str = str(notice)
                            if 'NEW_VERSION_ID:' in notice_str:
                                try:
                                    new_version_id = int(
                                        notice_str.split('NEW_VERSION_ID:')[1].strip()
                                    )
                                except (ValueError, IndexError):
                                    pass
                                break

                        if new_version_id is None:
                            raise RuntimeError(
                                "p_save_class_version_immutable не вернул NEW_VERSION_ID"
                            )

                        # Свойства root: db_id = СТАРЫЙ version_id (ключ коллекции)
                        self._save_properties_for_version(
                            cur, new_version_id,
                            {'db_id': self.version_id},
                            is_new_version=True
                        )

                        # Закрытие удалённых элементов
                        deleted_ids = self.collection.get_deletes()
                        if deleted_ids:
                            cur.execute(
                                "UPDATE class_erp.class_version SET dt_end = now() "
                                "WHERE id = ANY(%s::int[])",
                                (deleted_ids,)
                            )

                        # Подобъекты в новую версию
                        self._save_collection_subobjects_immutable(
                            cur, new_version_id
                        )

                        self.version_id = new_version_id

                    else:
                        # === СЦЕНАРИЙ B: Обновить текущую ===
                        self._save_class_in_place(
                            cur, self.version_id, class_comment, geometry_json
                        )

                        # Закрытие удалённых элементов (раньше было только в C!)
                        deleted_ids = self.collection.get_deletes()
                        if deleted_ids:
                            cur.execute(
                                "UPDATE class_erp.class_version SET dt_end = now() "
                                "WHERE id = ANY(%s::int[])",
                                (deleted_ids,)
                            )

                    # Методы (общий для обоих сценариев)
                    self._save_methods_from_collection(cur)

                else:
                    # === СЦЕНАРИЙ A: Новый класс ===
                    self._save_new_class(cur)

                self._refresh_inspector()

            if not silent:
                QMessageBox.information(
                    self, "Успех", "Класс успешно сохранён!"
                )
            self.accept()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка сохранения класса: {e}"
            )

    def _save_properties_for_version(self, cur, version_id: int, ctrl_data: dict,
                                     is_new_version: bool):
        """
        Атомарно сохраняет значения, переопределения метаданных и BLOB свойств
        ОДНОГО элемента в class_version_properties.

        v9 FIX (адресация):
        Коллекция берётся по idCol (STRICT IDCOL), а не по DB-ID.
        ctrl_data['db_id'] — DB-ID элемента; переводим через обратный индекс.
        Раньше get_property_collection(db_id) возвращал None для root,
        и сохранение молча ничего не делало.

        v9 FIX (отбор):
        Источник правды — col.get_changed_properties() (isDirty OR isDelete).
        Вызов prop.is_changed() убран: это bool-поле, а не метод (TypeError).

        Сценарий B (is_new_version=False, обновление «на месте»):
          • изменённая строка с физическим id > 0 и владельцем этой версии →
            UPDATE по id (без раздувания хроники);
          • изменённая строка, определённая у ПРЕДКА (defined_in_version_id != version_id)
            или мост Qt (id < 0) → INSERT собственного переопределения;
          • isDelete + физическая строка → dt_end = now(), новая не создаётся;
          • isDelete + мост → закрывать нечего, только подавление в модели.

        Сценарий C (is_new_version=True, «Новая версия»):
          • переносятся ВСЕ собственные живые свойства старой версии
            (owner_version_id == старый version_id ИЛИ defined_in_version_id ==
             старый version_id), плюс все dirty-строки;
          • унаследованные от ERP-предков НЕ копируются — они читаются
            через f_get_lineage по i_base_class / donor_object_id;
          • старая версия уже закрыта в p_save_class_version_immutable,
            её свойства трогать не нужно.

        BLOB:
          is_blob=True  → c_value=NULL, blob_value=Binary(bytes)
          is_blob=False → c_value=value, blob_value=NULL   ← честный сброс
          Пустой bytes трактуется как отсутствие блоба.

        c_default_value:
          для новой строки — initial_value, если он непустой; иначе NULL
          (дефолт предка подтянется через COALESCE в f_build_objpropcol).

        После записи: prop.id = новый физический id, owner_version_id = version_id,
        defined_in_version_id = version_id, mark_saved() — флаги сброшены.
        Кэш ClassRegistry / PropertyBridgeManager по этой версии инвалидируется.
        """
        import psycopg2

        # --- STRICT IDCOL: DB-ID элемента → idCol → коллекция --------------
        db_id = ctrl_data.get('db_id', version_id)
        elem_id_col = self.collection._get_id_col_by_db_id(db_id)
        if elem_id_col is None:
            # Элемент уже вылетел из индекса (удалён) — сохранять нечего
            return
        col = self.collection.get_property_collection(elem_id_col)
        if col is None or len(col) == 0:
            return

        changed = col.get_changed_properties()
        changed_names = {p.cname for p in changed}

        # --- Что сохраняем ------------------------------------------------
        if is_new_version:
            to_save = []
            for prop in col.all_ordered():
                if getattr(prop, 'isDelete', False):
                    continue
                is_own_live = (
                    getattr(prop, 'owner_version_id', None) == db_id
                    or getattr(prop, 'defined_in_version_id', None) == db_id
                )
                if prop.cname in changed_names or is_own_live:
                    to_save.append(prop)
        else:
            to_save = [p for p in changed]

        if not to_save:
            return

        saved_count = 0

        for prop in to_save:
            is_deleted = bool(getattr(prop, 'isDelete', False))
            physical_id = prop.id if (prop.id or 0) > 0 else None
            defined_in = getattr(prop, 'defined_in_version_id', None)
            owner_vid = getattr(prop, 'owner_version_id', None)

            # Есть ли физическая строка, принадлежащая ЭТОЙ версии
            owns_row = bool(
                physical_id is not None
                and (owner_vid == version_id or defined_in == version_id)
            )

            # --- Удаление переопределения --------------------------------
            if is_deleted:
                if physical_id is not None and not is_new_version:
                    cur.execute(
                        "UPDATE class_erp.class_version_properties "
                        "SET dt_end = now() WHERE id = %s AND dt_end IS NULL;",
                        (physical_id,)
                    )
                    saved_count += 1
                # Мост Qt / чужая строка / новая версия — закрывать нечего
                prop.mark_saved()
                continue

            # --- Обновление «на месте» (сценарий B) ----------------------
            if not is_new_version and owns_row:
                if prop.is_blob and prop.blob_value:
                    db_c_value = None
                    db_blob = psycopg2.Binary(bytes(prop.blob_value))
                else:
                    db_c_value = prop.value
                    db_blob = None

                cur.execute(
                    """UPDATE class_erp.class_version_properties
                       SET c_name = %s, type = %s, mask = %s, source = %s,
                           c_value = %s,
                           typesourcevalue = %s, fuuncselectionvalue = %s,
                           bridgecalcset = %s, bridgecalcget = %s,
                           ui_label_ru = %s, editor_type = %s, qt_target = %s,
                           translation_strategy = %s, isdefaultepr = %s,
                           blob_value = %s, is_blob = %s
                     WHERE id = %s AND dt_end IS NULL;""",
                    (
                        prop.cname, prop.typevalue,
                        getattr(prop, 'mask', None), prop.sourcevalue,
                        db_c_value,
                        prop.typesourcevalue, prop.fuuncselectionvalue,
                        prop.bridgecalcset, prop.bridgecalcget,
                        prop.ui_label_ru, prop.editor_type, prop.qt_target,
                        prop.translation_strategy, prop.isdefaultepr,
                        db_blob, bool(prop.is_blob and prop.blob_value),
                        physical_id,
                    )
                )
                prop.owner_version_id = version_id
                prop.defined_in_version_id = version_id
                prop.mark_saved()
                saved_count += 1
                continue

            # --- INSERT нового переопределения ---------------------------
            # Если своя строка уже была — закрываем её (историчность)
            if physical_id is not None and owns_row and not is_new_version:
                cur.execute(
                    "UPDATE class_erp.class_version_properties "
                    "SET dt_end = now() WHERE id = %s AND dt_end IS NULL;",
                    (physical_id,)
                )

            if prop.is_blob and prop.blob_value:
                db_c_value = None
                db_blob = psycopg2.Binary(bytes(prop.blob_value))
                db_is_blob = True
            else:
                db_c_value = prop.value
                db_blob = None
                db_is_blob = False

            initial = getattr(prop, 'initial_value', "") or ""
            db_default = initial if initial.strip() else None

            cur.execute(
                """INSERT INTO class_erp.class_version_properties
                   (id_class_version, c_name, type, mask, source,
                    c_value, c_default_value,
                    typesourcevalue, fuuncselectionvalue,
                    bridgecalcset, bridgecalcget,
                    ui_label_ru, editor_type, qt_target, translation_strategy,
                    isdefaultepr, blob_value, is_blob, owner_version_id,
                    dt_start, dt_end)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                           now(), NULL)
                   RETURNING id;""",
                (
                    version_id, prop.cname, prop.typevalue,
                    getattr(prop, 'mask', None), prop.sourcevalue,
                    db_c_value, db_default,
                    prop.typesourcevalue, prop.fuuncselectionvalue,
                    prop.bridgecalcset, prop.bridgecalcget,
                    prop.ui_label_ru, prop.editor_type, prop.qt_target,
                    prop.translation_strategy, prop.isdefaultepr,
                    db_blob, db_is_blob, version_id,
                )
            )
            row = cur.fetchone()
            if row:
                prop.id = row[0]
            prop.owner_version_id = version_id
            prop.defined_in_version_id = version_id
            prop.order = 1
            prop.is_from_qt = False
            prop.mark_saved()
            saved_count += 1

        # --- Инвалидация кэшей прочитанного ------------------------------
        if saved_count:
            try:
                node = goProject.class_registry.get_class_version(version_id)
                if node:
                    node.objpropcol_raw = None
                    node.sub_properties.clear()
                goProject.property_bridge_manager.invalidate_version_cache(version_id)
                goProject.bridge_resolver.invalidate(version_id)
            except Exception as e:
                if isDebug:
                    print(f"[_save_properties] Инвалидация кэша v{version_id}: {e}")

            if isDebug:
                print(f"[_save_properties] v{version_id} (elem db_id={db_id}): "
                      f"записано {saved_count} строк, "
                      f"сценарий={'C (новая версия)' if is_new_version else 'B (на месте)'}")
    def _save_subobject(self, cur, db_id: int, parent_version_id: int,
                        is_new_parent: bool = True):
        """Сохраняет один подобъект (root не передаётся). Работает с DB-ID."""
        ctrl = self.collection.get_element(db_id)
        if ctrl is None:
            return None
        if ctrl.get('parent_id') is None:
            return None

        is_new = ctrl.get('db_id', -1) < 0 and not ctrl.get('is_saved', False)
        real_id = ctrl.get('db_id')
        if not is_new and real_id is not None and real_id < 0:
            real_id = self.collection.get_saved_version_id(real_id)

        geo_json = "{}"

        if is_new:
            cur.execute(
                "INSERT INTO class_erp.mozartclasses (c_name, is_class) VALUES (%s, false) RETURNING id;",
                (ctrl.get('calias', 'subobject'),)
            )
            abs_id = cur.fetchone()[0]
            base_class = self._get_c_base_class(db_id)
            base_source = 'QT'
            base_id = None
            exec_env = 'HYBRID'
        else:
            cur.execute(
                "SELECT id_mozart_class, c_base_class, c_base_source, i_base_class, c_execution_env "
                "FROM class_erp.class_version WHERE id = %s",
                (real_id,)
            )
            old_row = cur.fetchone()
            if old_row:
                abs_id = old_row[0]
                base_class = old_row[1]
                base_source = old_row[2]
                base_id = old_row[3]
                exec_env = old_row[4]
                cur.execute("UPDATE class_erp.class_version SET dt_end = now() WHERE id = %s", (real_id,))
            else:
                return None

        cur.execute(
            """INSERT INTO class_erp.class_version
               (id_mozart_class, is_visible, i_parent_id, txt_properties,
                c_base_class, c_base_source, i_base_class, c_execution_env,
                dt_start, dt_end)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), NULL) RETURNING id;""",
            (abs_id, not ctrl.get('is_logical', False), parent_version_id, geo_json,
             base_class, base_source, base_id, exec_env)
        )
        new_sub_version_id = cur.fetchone()[0]

        self._save_properties_for_version(cur, new_sub_version_id, ctrl, is_new_version=True)

        for s_name, sig in (ctrl.get('sub_signals') or {}).items():
            if getattr(sig, 'is_deleted', False):
                if getattr(sig, 'id', None) and sig.id > 0:
                    cur.execute(
                        "UPDATE class_erp.signal SET dt_end = now() "
                        "WHERE id = %s AND dt_end IS NULL;",
                        (sig.id,)
                    )
                continue

            id_method = getattr(sig, 'id_method', None)

            if getattr(sig, 'id', None) is None:
                cur.execute(
                    "INSERT INTO class_erp.signal "
                    "(c_signal, id_class_version, id_method, dt_start, dt_end) "
                    "VALUES (%s, %s, %s, now(), NULL);",
                    (s_name, new_sub_version_id, id_method)
                )

        if is_new:
            self.collection.mark_element_saved(db_id, new_sub_version_id)

        return new_sub_version_id

    def _save_collection_subobjects_immutable(self, cur, new_parent_version_id: int):
        """Сценарий C: сохранение подобъектов в новую версию."""
        active = self.collection.get_updates() + self.collection.get_saved_new() + self.collection.get_inserts()
        seen = set()
        for ctrl in active:
            db_id = ctrl.get('db_id')
            if db_id in seen:
                continue
            seen.add(db_id)
            if ctrl.get('parent_id') is None:
                continue
            self._save_subobject(cur, db_id, new_parent_version_id, is_new_parent=True)

    def _save_class_in_place(self, cur, version_id: int, class_comment: str,
                             geometry_json: str):
        """
        Сценарий B: обновление текущей версии «на месте» (status=DEV, потомков нет).

        v9 FIX (порядок операций):
        root_col.mark_saved() вызывался ДО _save_properties_for_version →
        isDirty/is_changed сброшены, get_changed_properties() пуст, в БД не
        уходило НИЧЕГО. Теперь mark_saved выполняется только внутри
        _save_properties_for_version, точечно на каждой записанной строке.

        v9 FIX (адресация):
        Коллекция берётся по idCol (DB-ID → _get_id_col_by_db_id → коллекция).
        get_property_collection(version_id) возвращал None для root.

        v9 FIX (паспорт версии):
        • i_load_order пишется из load_order_spin (раньше игнорировался);
        • txt_properties НЕ затирается '{}': собирается JSON-паспорт геометрии
          из GEOMETRY_PROPS коллекции. Если геометрии нет — прежнее значение
          поля сохраняется (COALESCE-логика на уровне Python).

        v9 FIX (иерархия):
        при is_parent_changed пишется реальный ctrl['parent_id'], а не
        version_id. Раньше любой перепривязанный объект уезжал в root.

        Порядок: сначала закрываем удалённые элементы (dt_end), затем root,
        затем подобъекты — чтобы не писать свойства в уже мёртвые строки.

        Новые подобъекты (db_id < 0, не сохранены) идут через _save_subobject;
        существующие обновляются на месте по их реальной версии.
        """
        import json as _json
        from core.constants import GEOMETRY_PROPS

        mgr = self.collection

        # --- Вспомогательное: JSON-паспорт геометрии элемента --------------
        def _build_geo_json(idcol: Optional[int], fallback: str = "{}") -> str:
            if not idcol:
                return fallback or "{}"
            col = mgr.get_property_collection(idcol)
            if col is None:
                return fallback or "{}"
            geo = {}
            for cname in ('myx', 'myy', 'mywidth', 'myheight'):
                p = col.get(cname)
                if p is None or getattr(p, 'isDelete', False):
                    continue
                raw = str(p.value).strip() if p.value is not None else ""
                if not raw:
                    continue
                try:
                    geo[cname] = int(float(raw))
                except (TypeError, ValueError):
                    continue
            return _json.dumps(geo, ensure_ascii=False) if geo else (fallback or "{}")

        # --- 1. Удалённые элементы: закрываем ПЕРЕД записью свойств --------
        deleted_ids = [d for d in mgr.get_deletes() if d and d > 0]
        if deleted_ids:
            cur.execute(
                "UPDATE class_erp.class_version SET dt_end = now() "
                "WHERE id = ANY(%s::int[]) AND dt_end IS NULL;",
                (deleted_ids,)
            )

        # --- 2. Бизнес-описание абстрактного класса -----------------------
        cur.execute(
            "UPDATE class_erp.mozartclasses SET mcomment = %s "
            "WHERE id = (SELECT id_mozart_class FROM class_erp.class_version "
            "            WHERE id = %s);",
            (class_comment, version_id)
        )

        # --- 3. Паспорт root-версии ---------------------------------------
        root_idcol = mgr._get_id_col_by_db_id(version_id)
        root_geo = _build_geo_json(root_idcol, geometry_json)
        load_order = (self.load_order_spin.value()
                      if hasattr(self, 'load_order_spin') else None)

        if load_order is not None:
            cur.execute(
                "UPDATE class_erp.class_version "
                "SET txt_properties = %s, i_load_order = %s "
                "WHERE id = %s;",
                (root_geo, int(load_order), version_id)
            )
        else:
            cur.execute(
                "UPDATE class_erp.class_version SET txt_properties = %s "
                "WHERE id = %s;",
                (root_geo, version_id)
            )

        # --- 4. Свойства root (mark_saved — внутри, не здесь!) -------------
        self._save_properties_for_version(
            cur, version_id, {'db_id': version_id}, is_new_version=False
        )

        # --- 5. Подобъекты ------------------------------------------------
        active_controls = (mgr.get_updates() + mgr.get_saved_new()
                           + mgr.get_inserts())
        seen = set()

        for ctrl in active_controls:
            db_id = ctrl.get('db_id')
            if db_id is None or db_id in seen:
                continue
            seen.add(db_id)

            # root уже обработан
            if ctrl.get('parent_id') is None:
                continue
            # удалённые — пропускаем
            if db_id in deleted_ids or ctrl.get('isDelete', False):
                continue

            is_new = db_id < 0 and not ctrl.get('is_saved', False)

            if is_new:
                # Новый подобъект: mozartclasses + class_version + свойства
                self._save_subobject(cur, db_id, version_id, is_new_parent=False)
                continue

            real_id = db_id if db_id > 0 else mgr.get_saved_version_id(db_id)
            if not real_id or real_id <= 0:
                continue

            idcol = mgr._get_id_col_by_db_id(db_id)
            sub_geo = _build_geo_json(idcol, ctrl.get('txt_properties') or "{}")

            # --- Паспорт подобъекта + перепривязка ----------------------
            if ctrl.get('is_parent_changed'):
                new_parent_db_id = ctrl.get('parent_id')
                cur.execute(
                    "UPDATE class_erp.class_version "
                    "SET txt_properties = %s, i_parent_id = %s "
                    "WHERE id = %s;",
                    (sub_geo, new_parent_db_id, real_id)
                )
                ctrl['is_parent_changed'] = False
            else:
                cur.execute(
                    "UPDATE class_erp.class_version SET txt_properties = %s "
                    "WHERE id = %s;",
                    (sub_geo, real_id)
                )

            # --- Свойства подобъекта ------------------------------------
            self._save_properties_for_version(
                cur, real_id, ctrl, is_new_version=False
            )

        if isDebug:
            print(f"[_save_class_in_place] v{version_id}: "
                  f"load_order={load_order}, удалено={len(deleted_ids)}, "
                  f"подобъектов обработано={len(seen)}")

    def _save_new_class(self, cur):
        """Сценарий A: создание нового класса."""
        class_name = self.class_name or self.translator.tr('dialog_edit_class') or "NewClass"
        class_comment = self.edit_class_comment.toPlainText().strip()
        cur.execute(
            """INSERT INTO class_erp.mozartclasses
               (c_name, mcomment, is_class, owner_class_id, dt_start, dt_end)
               VALUES (%s, %s, TRUE, NULL, now(), NULL) RETURNING id;""",
            (class_name, class_comment or None)
        )
        id_mozart_class = cur.fetchone()[0]

        c_base_class = 'QWidget'
        c_base_source = 'QT'
        c_base_library = 'PySide6.QtWidgets'
        i_base_class = None
        c_execution_env = 'HYBRID'
        is_preload = True
        status_id = 1

        if hasattr(self, 'selected_base_class') and self.selected_base_class:
            c_base_class = self.selected_base_class
        if hasattr(self, 'selected_base_source') and self.selected_base_source:
            c_base_source = self.selected_base_source
        if hasattr(self, 'selected_base_library') and self.selected_base_library:
            c_base_library = self.selected_base_library
        if hasattr(self, 'selected_i_base_class') and self.selected_i_base_class:
            i_base_class = self.selected_i_base_class

        root_col = self.collection.get_property_collection(self.version_id) if self.version_id > 0 else None
        root_props = {}
        if root_col:
            root_props = {p.cname: p.value for p in root_col.all_ordered() if p.value and not p.is_blob}
        geometry_json = json.dumps({'properties': root_props}, ensure_ascii=False) if root_props else "{}"

        cur.execute(
            """INSERT INTO class_erp.class_version
               (id_mozart_class, is_visible, c_base_class, c_base_source,
                i_base_class, i_parent_id, txt_properties, dt_start, dt_end,
                c_execution_env, is_preload, status_id, donor_object_id,
                first_ancestor_class_id, c_base_library, i_load_order)
               VALUES (%s, TRUE, %s, %s, %s, NULL, %s, now(), NULL,
                       %s, %s, %s, NULL, NULL, %s, %s) RETURNING id;""",
            (id_mozart_class, c_base_class, c_base_source,
             i_base_class, geometry_json,
             c_execution_env, is_preload, status_id,
             c_base_library, self.load_order_spin.value() if hasattr(self, 'load_order_spin') else 100)
        )
        id_class_version = cur.fetchone()[0]

        root_elem_id = self.version_id if self.version_id > 0 else None
        if root_elem_id and root_elem_id in self.collection._elements:
            self._save_properties_for_version(
                cur, id_class_version, {'db_id': root_elem_id}, is_new_version=True
            )

        if self.collection:
            for idcol, elem in list(self.collection._elements.items()):
                db_id = elem.get('db_id')
                if elem.get('parent_id') is None:
                    continue
                self._save_subobject(cur, db_id, id_class_version, is_new_parent=True)

        cur.execute(
            "UPDATE class_erp.class_version SET txt_properties = %s WHERE id = %s",
            (geometry_json, id_class_version)
        )

        self.version_id = id_class_version
        self.mode = 'edit'
        self.class_name = class_name

    def _save_sub_collections_relational(self, cur, new_version_id: int, ctrl_data: dict):
        """Оставлено для обратной совместимости."""
        self._save_properties_for_version(cur, new_version_id, ctrl_data, is_new_version=True)

        for s_name, sig in (ctrl_data.get('sub_signals') or {}).items():
            if getattr(sig, 'is_deleted', False):
                continue

            id_method = getattr(sig, 'id_method', None)

            if getattr(sig, 'id', None) is None:
                cur.execute(
                    "INSERT INTO class_erp.signal "
                    "(c_signal, id_class_version, id_method, dt_start, dt_end) "
                    "VALUES (%s, %s, %s, now(), NULL);",
                    (s_name, new_version_id, id_method)
                )

        for m_name, m_text in (ctrl_data.get('sub_methods') or {}).items():
            cur.execute(
                "INSERT INTO class_erp.method (c_name, dt_start) VALUES (%s, now()) "
                "ON CONFLICT (c_name) DO UPDATE SET c_name=EXCLUDED.c_name RETURNING id;",
                (m_name,))
            m_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO class_erp.method_class_relation "
                "(id_method, id_class_version, dt_start, dt_end) VALUES (%s, %s, now(), NULL);",
                (m_id, new_version_id))

    def _save_methods_from_collection(self, cur):
        changed = self.collection.get_changed_methods()
        for db_id, methods in changed.items():
            real_vid = db_id if db_id > 0 else self.collection.get_saved_version_id(db_id)
            if not real_vid:
                continue
            for m in methods:
                if m.is_new:
                    cur.execute(
                        "INSERT INTO class_erp.method (c_name, owner_class_id, dt_start, dt_end) "
                        "VALUES (%s, %s, NOW(), NULL) RETURNING id;",
                        (m.c_name, real_vid)
                    )
                    new_mid = cur.fetchone()[0]
                    m.id = new_mid
                    cur.execute(
                        "INSERT INTO class_erp.method_version (id_method, txt_method, i_lang, dt_start, dt_end) "
                        "VALUES (%s, NULL, %s, NOW(), NULL);",
                        (new_mid, m.i_lang)
                    )
                    cur.execute(
                        "INSERT INTO class_erp.method_class_relation (id_method, id_class_version, dt_start, dt_end) "
                        "VALUES (%s, %s, NOW(), NULL);",
                        (new_mid, real_vid)
                    )
                elif m.is_deleted:
                    cur.execute(
                        "UPDATE class_erp.method_class_relation SET dt_end = NOW() "
                        "WHERE id_method = %s AND id_class_version = %s AND dt_end IS NULL;",
                        (m.id, real_vid)
                    )
                elif m.is_changed:
                    cur.execute(
                        "UPDATE class_erp.method_version SET i_lang = %s "
                        "WHERE id_method = %s AND dt_end IS NULL;",
                        (m.i_lang, m.id)
                    )
        self.collection.mark_methods_saved()

    # =====================================================================
    # ЗАГРУЗКА / ОТРИСОВКА
    # =====================================================================

    def load_class_data(self, version_id: int):
        if not self.class_service:
            return
        try:
            self.class_data = self.class_service.get_class_version(version_id)
            if not self.class_data:
                QMessageBox.warning(self, "Внимание", f"Класс {version_id} не найден")
                return
            version = self.class_data.get('version', {})
            self.class_name = version.get('c_name', '')
            self._loaded_dt_start = version.get('dt_start')
            self.class_info_label.setText(f"<b>{self.class_name}</b> (ID: {version_id})")
            if hasattr(self, 'load_order_spin'):
                self.load_order_spin.setValue(int(version.get('i_load_order') or 100))
            self._ensure_default_methods_sync(version_id)
            self.load_controls_from_db()
            self.setWindowTitle(f"{self.translator.tr('dialog_edit_class')}: {self.class_name}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()

    def _ensure_default_methods_sync(self, version_id: int):
        if not self.db or version_id <= 0:
            return
        try:
            self.db.execute_procedure("class_erp.p_ensure_default_methods", (version_id,))
        except Exception as e:
            if isDebug:
                print(f"[ClassEditDialog] p_ensure_default_methods({version_id}) ошибка: {e}")

    def load_controls_from_db(self):
        """
        Загружает дерево элементов класса из БД на сцену.
        v7.7:
          1) Сортировка по i_load_order (родитель раньше ребёнка).
          2) Убран двойной init_property_collection (доверяем add_element_with_metadata).
          3) isInherited берётся из реального prop.order (не перезаписывается).
        """
        from ide_core import goProject
        session_date_str = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")

        if self.mode == 'edit' and self.version_id > 0 and self.db:
            try:
                res = self.db.execute_query(
                    "SELECT dt_start, dt_end FROM class_erp.class_version WHERE id = %s",
                    (self.version_id,)
                )
                if res:
                    dt_start, dt_end = res[0][0], res[0][1]
                    in_range = True
                    now = goProject.system_date.toPython()
                    if dt_start and now < dt_start:
                        in_range = False
                    if dt_end and now > dt_end:
                        in_range = False
                    if not in_range:
                        QMessageBox.warning(self, "Дата сессии вне диапазона версии", "Данные недоступны.")
            except Exception:
                pass

        if not self.class_data:
            return

        from ide_core import goProject
        lib = goProject.superlibre

        # ============================================================
        # ФАЗА 1: Полное заполнение коллекции (БЕЗ отрисовки)
        # ============================================================
        with self.collection.silent_mode():
            if getattr(self, 'collection', None) is None:
                self.collection = CollectionManager()
                self.graphics_items = self.collection._graphics_items
            else:
                self.collection.clear_all()

            self.scene.clear()

            version = self._normalize_version(self.class_data.get('version'))
            current_version_id = version.get('id')
            if not current_version_id:
                return

            # --- Root ---
            root_data = {
                'db_id': current_version_id,
                'parent_id': None,
                'calias': version.get('c_name', 'Контейнер'),
                'cclass': 'container',
                'is_new': False,
                'is_logical': False,
                'idVersion': current_version_id,
                'chngID': None,
                'chngIDVersion': None,
                'isDelete': False,
                'isInherited': False,
                'isDirty': False,
            }
            # add_element_with_metadata сам инициализирует property_collection (с order из БД)
            root_id_col = self.collection.add_element_with_metadata(
                root_data, current_version_id, self.db
            )

            # isInherited для root-свойств — из реального order (не перезаписываем order!)
            root_col = self.collection.get_property_collection(root_id_col)
            if root_col is not None:
                for prop in root_col.all_ordered():
                    prop.idVersion = current_version_id
                    prop.isInherited = (prop.order > 1)
                    prop.isDelete = False
                    prop.isDirty = False
                    prop.chngID = None
                    prop.chngIDVersion = None

            self._fill_lineage_and_methods(current_version_id)

            # --- Список версий для маппинга Qt-классов ---
            all_versions_raw = self.db.execute_query(
                "SELECT id, c_base_class, c_base_source, i_base_class "
                "FROM class_erp.class_version WHERE dt_end IS NULL"
            ) or []
            versions_db = {
                str(r[0]): {
                    'base_class': str(r[1] or ''),
                    'source': str(r[2] or ''),
                    'base_id': str(r[3]) if r[3] else None,
                }
                for r in all_versions_raw
            }

            def get_root_qt_class(v_id: str) -> str:
                visited, current = set(), v_id
                while current and current in versions_db and current not in visited:
                    visited.add(current)
                    v_data = versions_db[current]
                    if v_data['source'] in ('PYTHON', 'QT'):
                        return v_data['base_class']
                    current = v_data['base_id']
                return 'QWidget'

            qt_to_factory = {
                'QLabel': 'label', 'QLineEdit': 'textbox', 'QPushButton': 'button', 'QCheckBox': 'checkbox',
                'QComboBox': 'combobox', 'QDateEdit': 'datebox', 'QListWidget': 'listbox',
                'QPlainTextEdit': 'memo', 'QWidget': 'container', 'QGroupBox': 'container',
                'QTabWidget': 'tabcontainer', 'QRadioButton': 'radiobutton',
                'QObject': 'baseinvisible', 'QTreeView': 'treeview', 'QTableWidget': 'grid',
                'QMainWindow': 'mainform', 'QDialog': 'dialogform', 'QSpinBox': 'numberbox',
                'QDoubleSpinBox': 'numberbox', 'QTextEdit': 'memo', 'QFrame': 'container',
            }

            # --- Дочерние элементы: сортировка по i_load_order ---
            sql = """
            SELECT cv.id, mc.c_name, cv.i_parent_id, cv.is_visible, cv.i_base_class,
                   cv.i_load_order
            FROM class_erp.class_version cv
            JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
            WHERE cv.i_parent_id = %s AND cv.dt_end IS NULL
            ORDER BY cv.i_load_order ASC, cv.id ASC
            """
            rows = self.db.execute_query(sql, (current_version_id,)) or []

            for row in rows:
                sub_id = row[0]
                sub_name = str(row[1] or '').strip().strip('"')
                parent_id = row[2]
                is_visible = row[3]
                child_version_id = str(row[4]) if row[4] else None
                # i_load_order (row[5]) уже отсортирован в SQL

                root_qt = get_root_qt_class(child_version_id) if child_version_id else 'QWidget'
                factory_type = qt_to_factory.get(root_qt, 'container')

                elem_data = {
                    'db_id': sub_id,
                    'parent_id': parent_id if parent_id else current_version_id,
                    'calias': sub_name,
                    'cclass': factory_type,
                    'is_new': False,
                    'is_saved': True,
                    'saved_version_id': sub_id,
                    'is_logical': not is_visible,
                    'idVersion': sub_id,
                    'chngID': None,
                    'chngIDVersion': None,
                    'isDelete': False,
                    'isInherited': False,
                    'isDirty': False,
                }
                # add_element_with_metadata сам инициализирует property_collection
                sub_id_col = self.collection.add_element_with_metadata(
                    elem_data, sub_id, self.db
                )

                self._fill_lineage_and_methods(sub_id)

                # isInherited для подобъекта-свойств — из реального order
                sub_col = self.collection.get_property_collection(sub_id_col)
                if sub_col is not None:
                    for prop in sub_col.all_ordered():
                        prop.idVersion = sub_id
                        prop.isInherited = (prop.order > 1)
                        prop.isDelete = False
                        prop.isDirty = False
                        prop.chngID = None
                        prop.chngIDVersion = None

                # Инициализация геометрии (0 — валидное значение)
                if sub_col:
                    sx = lib.geometry_get(sub_col, 'myx', 50)
                    sy = lib.geometry_get(sub_col, 'myy', 50)
                    prop_x, prop_y = sub_col.get('myx'), sub_col.get('myy')
                    if not prop_x or prop_x.value == "":
                        sub_col.set_value('myx', str(sx), source='init')
                    if not prop_y or prop_y.value == "":
                        sub_col.set_value('myy', str(sy), source='init')

            self._validate_invariants()

        # ============================================================
        # ФАЗА 2: Отрисовка на основе готовой коллекции
        # ============================================================
        self.render_scene()
        self._refresh_inspector()


    def _refresh_inspector(self):
        """Сброс кэша и перерисовка Debug Inspector."""
        if not isDebug:
            return
        if getattr(self, 'debug_inspector', None) is None:
            return

        if hasattr(goProject, 'class_registry') and goProject.class_registry:
            node = goProject.class_registry.get_class_version(self.version_id)
            if node:
                node.objpropcol_raw = None

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.debug_inspector.refresh_tree)

    def _validate_invariants(self):
        """Проверки после загрузки формы."""
        if not self.collection:
            return

        root_db_id = self.version_id if self.version_id > 0 else None
        if root_db_id is None:
            return

        root_idcol = self.collection._get_id_col_by_db_id(root_db_id)

        # 1. Унаследованные дети внутри собственных контейнеров
        for idcol in list(self.collection._elements.keys()):
            child = self.collection.get_element_by_id_col(idcol)
            if not child:
                continue
            if idcol == root_idcol:
                continue
            if not child.get('isInherited', False):
                continue
            parent_db_id = child.get('parent_id')
            if parent_db_id is None or parent_db_id == root_db_id:
                continue
            parent_idcol = self.collection._get_id_col_by_db_id(parent_db_id)
            if parent_idcol is None:
                continue
            parent = self.collection.get_element_by_id_col(parent_idcol)
            if parent is None:
                continue
            if not parent.get('isInherited', False):
                if isDebug:
                    print(f"[_validate_invariants] НАРУШЕНИЕ: {idcol} внутри {parent_idcol}. Поднимаем в root.")
                child['parent_id'] = root_db_id

        # 2. Битые ссылки
        for idcol in list(self.collection._elements.keys()):
            child = self.collection.get_element_by_id_col(idcol)
            if not child:
                continue
            if idcol == root_idcol:
                continue
            parent_db_id = child.get('parent_id')
            if parent_db_id is None:
                continue
            parent_idcol = self.collection._get_id_col_by_db_id(parent_db_id)
            if parent_idcol is None:
                if isDebug:
                    print(f"[_validate_invariants] БИТАЯ ССЫЛКА: {idcol} → {parent_db_id}. Поднимаем в root.")
                child['parent_id'] = root_db_id

    def _fill_lineage_and_methods(self, db_id: int):
        """Заполняет линию крови и методы (работа с БД по DB-ID)."""
        from ide_core import goProject
        lineage = []
        node = goProject.class_registry.get_class_version(db_id)
        if node:
            order = 1
            current_node = node
            visited = set()
            while current_node and current_node.version_id not in visited:
                visited.add(current_node.version_id)
                lineage.append({
                    'order': order,
                    'version_id': current_node.version_id,
                    'class_name': current_node.class_name,
                    'element_id': current_node.version_id if order == 1 else None,
                    'is_own': (order == 1),
                })
                parent_id = current_node.donor_object_id or current_node.i_base_class_version_id
                if parent_id and parent_id > 0:
                    current_node = goProject.class_registry.get_class_version(parent_id)
                else:
                    current_node = None
                order += 1
        self.collection.set_lineage(db_id, lineage)

        iso_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")
        sql = "SELECT * FROM class_erp.f_get_class_methods_on_date(%s, %s)"
        try:
            rows = self.db.execute_query(sql, (db_id, iso_date)) or []
        except Exception as e:
            if isDebug:
                print(f"[ClassEditDialog] f_get_class_methods_on_date({db_id}) ошибка: {e}")
            rows = []

        self.collection.init_method_collection(db_id, rows)

        method_col = self.collection.get_method_collection(db_id)
        if method_col is not None:
            for m in method_col.all_ordered():
                m.idVersion = db_id
                m.isInherited = (m.order > 1)
                m.isDelete = False
                m.isDirty = False
                m.chngID = None
                m.chngIDVersion = None

        idcol = self.collection._get_id_col_by_db_id(db_id)
        if idcol and idcol in self.collection._elements:
            if lineage and len(lineage) > 1:
                self.collection._elements[idcol]['isInherited'] = True

    def _normalize_version(self, version_dict: dict) -> dict:
        def to_str(val):
            if val is None:
                return ""
            return str(val).strip().strip('"')
        raw_id = version_dict.get('id')
        try:
            norm_id = int(str(raw_id).strip().strip('"')) if raw_id else 0
        except (ValueError, TypeError):
            norm_id = 0
        return {
            'id': norm_id,
            'c_name': to_str(version_dict.get('c_name')),
            'is_visible': bool(version_dict.get('is_visible', True)),
            'c_base_class': to_str(version_dict.get('c_base_class')),
            'c_base_source': to_str(version_dict.get('c_base_source')),
            'i_base_class': to_str(version_dict.get('i_base_class')),
            'i_parent_id': to_str(version_dict.get('i_parent_id')),
            'txt_properties': str(version_dict.get('txt_properties') or '')
        }

    def render_scene(self):
        """
        v7.6: Отрисовка на основе ПОЛНОСТЬЮ сформированной коллекции.
        Порядок — строго по глубине: root → дети → внуки.
        """
        from ide_core import goProject
        lib = goProject.superlibre

        with self.collection.silent_mode():
            self._draw_grid()

            # Собираем (id_col, elem) + глубину вложенности
            all_items = []
            for idcol in list(self.collection._elements.keys()):
                elem = self.collection.get_element_by_id_col(idcol)
                if not elem:
                    continue
                depth = 0
                cur = elem
                seen = set()
                while cur and cur.get('parent_id') is not None:
                    if cur.get('parent_id') in seen:
                        break
                    seen.add(cur.get('parent_id'))
                    parent_idcol = self.collection._get_id_col_by_db_id(cur.get('parent_id'))
                    if parent_idcol is None:
                        break
                    cur = self.collection.get_element_by_id_col(parent_idcol)
                    depth += 1
                all_items.append((depth, idcol, elem))

            # Сортируем: сначала по depth, потом по id_col
            all_items.sort(key=lambda t: (t[0], t[1]))

            for depth, idcol, elem_data in all_items:
                db_id = elem_data['db_id']
                parent_db_id = elem_data.get('parent_id')

                parent_idcol = self.collection._get_id_col_by_db_id(parent_db_id) if parent_db_id else None
                parent_item = self.graphics_items.get(parent_idcol) if parent_idcol else None

                item = self.create_control_item(idcol, db_id, elem_data, parent_item)
                if item:
                    self.collection.link_graphic_item(idcol, item)

                    if elem_data.get('cclass') == 'container':
                        self.collection.select_element(idcol, additive=False)
                        item.set_selected(True)

            self.update_properties_panel()
            self._update_active_handles()

    def _draw_grid(self):
        if not self.btn_grid.isChecked():
            return
        grid_size = int(self.grid_size_combo.currentText())
        scene_rect = self.scene.sceneRect()
        pen = QPen(QColor(200, 200, 200, 150), 0.5)
        x = 0
        while x < scene_rect.width():
            self.scene.addLine(x, 0, x, scene_rect.height(), pen)
            x += grid_size
        y = 0
        while y < scene_rect.height():
            self.scene.addLine(0, y, scene_rect.width(), y, pen)
            y += grid_size

    def create_control_item(self, id_col: int, db_id: int, element_data: Dict,
                            parent_item: Optional['ControlGraphicsItem'] = None) -> Optional['ControlGraphicsItem']:
        from ide_core import goProject
        cclass = element_data.get('cclass', 'textbox')
        is_logical = element_data.get('is_logical', False)

        if is_logical:
            widget = QWidget()
        elif cclass == 'container':
            from PySide6.QtWidgets import QGroupBox
            widget = QGroupBox()
        else:
            widget = create_control(cclass, parent=None, db=self.db)

        if not widget:
            return None

        # ✅ v7.8: setObjectName — ДО apply_bridge_translations, чтобы в логах было читаемое имя
        widget.setObjectName(element_data.get('calias', f"control_{id_col}"))

        # Предварительный resize по mywidth/myheight из модели
        if not is_logical:
            col = self.collection.get_property_collection(id_col)
            if col:
                w_prop = col.get('mywidth')
                h_prop = col.get('myheight')
                explicit_w = None
                explicit_h = None
                if w_prop and w_prop.value and str(w_prop.value).strip():
                    try:
                        explicit_w = max(20, int(float(str(w_prop.value))))
                    except (ValueError, TypeError):
                        pass
                if h_prop and h_prop.value and str(h_prop.value).strip():
                    try:
                        explicit_h = max(20, int(float(str(h_prop.value))))
                    except (ValueError, TypeError):
                        pass
                if explicit_w is not None or explicit_h is not None:
                    current_w = widget.width() if explicit_w is None else explicit_w
                    current_h = widget.height() if explicit_h is None else explicit_h
                    widget.resize(current_w, current_h)

        # Применяем ВСЕ свойства из модели к виджету через мосты (только SET)
        if not is_logical:
            col = self.collection.get_property_collection(id_col)
            if col is not None:
                try:
                    goProject.property_bridge_manager.apply_bridge_translations(
                        widget, col, version_id=db_id
                    )
                except Exception as e:
                    if isDebug:
                        print(f"[ClassEditDialog] Ошибка применения коллекции к виджету {db_id}: {e}")

        # ✅ v7.6: ControlGraphicsItem создаётся с parent=parent_item.
        item = ControlGraphicsItem(
            id_col=id_col,
            db_id=db_id,
            control_widget=widget,
            parent=parent_item,
            collection=self.collection,
            is_logical=is_logical,
        )

        # Root добавляем в сцену явно. Дети попадают в сцену через предка.
        if parent_item is None:
            self.scene.addItem(item)

        # Прокси-виджет: добавляем в сцену, потом привязываем к item
        if self.scene and widget:
            item.proxy = self.scene.addWidget(widget)
            if item.proxy:
                item.proxy.setParentItem(item)
                item.proxy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.proxy.installSceneEventFilter(item)
                widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                item.proxy.setPos(2, 2)
                rect = item.rect()
                item.proxy.resize(max(20, rect.width() - 4), max(20, rect.height() - 4))

        item.selected_changed.connect(self._on_item_selected)
        return item

    # =====================================================================
    # ВЫДЕЛЕНИЕ (строго по idCol)
    # =====================================================================

    def _on_item_selected(self, item: 'ControlGraphicsItem', selected: bool):
        if not selected:
            return
        self.update_properties_panel()

    def _handle_click_selection(self, item: 'ControlGraphicsItem', ctrl_pressed: bool):
        if ctrl_pressed:
            result = self.collection.add_to_selection(item.id_col)
            if not result:
                reply = QMessageBox.question(
                    self, "Смена контейнера",
                    "Вы собираетесь начать выделение контролов другого контейнера.\n"
                    "Имеющееся выделение будет отменено.\nПродолжить?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self._clear_all_selection_visuals()
                    self.collection.clear_selection()
                    self.collection.add_to_selection(item.id_col)
                else:
                    if item.id_col in self.collection.selected_ids:
                        item.set_selected(True)
                    else:
                        item.set_selected(False)
        else:
            self._clear_all_selection_visuals()
            self.collection.clear_selection()
            self.collection.select_element(item.id_col, additive=False)
            item.set_selected(True)

        self._update_selection_visuals()
        self.update_properties_panel()
        self._update_active_handles()

    def _clear_all_selection_visuals(self):
        for idcol, gitem in self.graphics_items.items():
            if gitem.is_selected:
                gitem.set_selected(False)

    def _update_selection_visuals(self):
        selected = self.collection.selected_ids
        for idcol, item in self.graphics_items.items():
            should_be_selected = idcol in selected
            if item.is_selected != should_be_selected:
                item.set_selected(should_be_selected)

    def _update_active_handles(self):
        for handle_attr in ('_active_move_handle', '_active_resize_h_handle', '_active_resize_v_handle'):
            handle = getattr(self, handle_attr, None)
            if handle is None:
                continue
            try:
                scene = handle.scene()
            except RuntimeError:
                setattr(self, handle_attr, None)
                continue
            if scene is not None:
                try:
                    target_item = handle.target_item
                    target_item.geometry_changed.disconnect(handle.update_position)
                except (TypeError, RuntimeError):
                    pass
                try:
                    scene.removeItem(handle)
                except RuntimeError:
                    pass
                setattr(self, handle_attr, None)

        self._active_move_handle = None
        self._active_resize_h_handle = None
        self._active_resize_v_handle = None

        if not self.collection.selected_ids:
            return

        last_idcol = self.collection.last_selected_id
        if not last_idcol:
            return

        target_item = self.graphics_items.get(last_idcol)

        if target_item is not None:
            self._active_move_handle = MoveHandleItem(target_item, self.collection, self)
            self._active_resize_h_handle = ResizeHandleItem(target_item, self.collection, 'horizontal', self)
            self._active_resize_v_handle = ResizeHandleItem(target_item, self.collection, 'vertical', self)

            self.scene.addItem(self._active_move_handle)
            self.scene.addItem(self._active_resize_h_handle)
            self.scene.addItem(self._active_resize_v_handle)

            self._active_move_handle.update_position()
            self._active_resize_h_handle.update_position()
            self._active_resize_v_handle.update_position()

            target_item.geometry_changed.connect(self._active_move_handle.update_position)
            target_item.geometry_changed.connect(self._active_resize_h_handle.update_position)
            target_item.geometry_changed.connect(self._active_resize_v_handle.update_position)

    # =====================================================================
    # СЕТКА / СИГНАЛЫ
    # =====================================================================

    def toggle_grid(self):
        self._draw_grid()
        self.btn_grid.setText(
            self.translator.tr('btn_grid_on') if self.btn_grid.isChecked() else self.translator.tr('btn_grid_off')
        )

    def on_grid_size_changed(self, size: str):
        self._draw_grid()
        self.update_properties_panel()
        if hasattr(self, 'scene') and self.scene:
            self.scene.update()

    def show_signals_dialog(self):
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс")
            return
        from dialogs.signals_dialog import SignalsDialog
        SignalsDialog(self, db=self.db, version_id=self.version_id).exec_()

    # =====================================================================
    # ИНЪЕКЦИЯ КЛАССА
    # =====================================================================

    def inject_class(self, item: QTreeWidgetItem, column: int):
        from PySide6.QtCore import QTimer
        meta_data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not meta_data:
            return

        version_id = meta_data.get('version_id')
        class_name = meta_data.get('name', 'unknown')
        is_visible = meta_data.get('is_visible', True)

        clean_alias = class_name.lower().replace(' ', '_')
        next_id = self.collection.get_next_id()
        instance_alias = f"{clean_alias}_{abs(next_id)}"

        # active_container_id теперь хранит idCol контейнера
        target_parent_idcol = self.collection.active_container_id
        target_parent_db_id = None
        if target_parent_idcol:
            parent_elem = self.collection.get_element_by_id_col(target_parent_idcol)
            if parent_elem:
                target_parent_db_id = parent_elem['db_id']

        if target_parent_db_id is None:
            target_parent_db_id = self.version_id

        element_data = {
            'parent_id': target_parent_db_id,
            'calias': instance_alias,
            'cclass': clean_alias,
            'is_logical': not is_visible,
        }

        # add_element_with_metadata возвращает idCol (v7.5)
        new_id_col = self.collection.add_element_with_metadata(
            element_data, version_id, self.db
        )

        # После регистрации коллекция присвоила db_id
        new_elem = self.collection.get_element_by_id_col(new_id_col)
        new_db_id = new_elem.get('db_id') if new_elem else None

        parent_item = self.graphics_items.get(target_parent_idcol) if target_parent_idcol else None

        g_item = self.create_control_item(new_id_col, new_db_id, element_data, parent_item)
        if g_item:
            g_item.set_geometry(50, 50, 150, 30)
            self.collection.link_graphic_item(new_id_col, g_item)

            def force_post_injection_selection():
                self.collection.select_element(new_id_col, additive=False)
                self._update_selection_visuals()
                self.update_properties_panel()
                self._update_active_handles()

            QTimer.singleShot(0, force_post_injection_selection)

    # =====================================================================
    # ДЕРЕВО ВЛОЖЕННЫХ КЛАССОВ
    # =====================================================================

    def load_source_classes(self):
        if not self.db:
            return
        self.source_tree.clear()
        exclude_id = self.version_id if (self.mode == 'edit' and self.version_id > 0) else -1
        sql = """
        SELECT class_id, class_name, version_id, is_visible, c_base_class,
        category_id, category_name, category_parent_id, class_comment
        FROM class_erp.f_get_safe_base_classes(%s);
        """
        try:
            rows = self.db.execute_query(sql, (exclude_id,)) or []
        except Exception as e:
            if isDebug:
                print(f"[ERROR] Ошибка вызова классификатора: {e}")
            rows = []

        category_items = {}
        for row in rows:
            _, _, _, _, _, cat_id, cat_name, cat_pid, _ = row
            dict_cat_id = cat_id if cat_id is not None else 0
            if dict_cat_id not in category_items:
                folder = QTreeWidgetItem()
                folder.setText(0, f"📁 {cat_name}")
                folder.setData(0, Qt.ItemDataRole.UserRole, -1)
                category_items[dict_cat_id] = folder

        for row in rows:
            _, _, _, _, _, cat_id, _, cat_pid, _ = row
            dict_cat_id = cat_id if cat_id is not None else 0
            folder = category_items[dict_cat_id]
            if folder.parent() is None and self.source_tree.indexOfTopLevelItem(folder) == -1:
                if cat_pid and cat_pid in category_items:
                    category_items[cat_pid].addChild(folder)
                else:
                    self.source_tree.addTopLevelItem(folder)

        self._fill_classes_into_tree(rows, category_items)

    def _fill_classes_into_tree(self, rows: list, category_items: dict):
        for row in rows:
            c_id, c_name, v_id, is_vis, base_str, cat_id, _, _, cls_comment = row
            dict_cat_id = cat_id if cat_id is not None else 0
            parent_folder = category_items[dict_cat_id]

            item = QTreeWidgetItem(parent_folder)
            item.setText(0, f"🧩 {c_name}" if is_vis else f"⚙️ {c_name}")
            if cls_comment:
                item.setToolTip(0, cls_comment)

            meta_data = {
                "class_id": c_id,
                "version_id": v_id,
                "name": c_name,
                "is_visible": bool(is_vis),
                "base_classes": [p.strip() for p in str(base_str or "").split(",") if p.strip()]
            }
            item.setData(0, Qt.ItemDataRole.UserRole + 1, meta_data)

            if not is_vis:
                item.setForeground(0, QBrush(QColor(139, 0, 139)))
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)

        self.source_tree.expandAll()

    # =====================================================================
    # КЛАВИАТУРА
    # =====================================================================

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            inherited_idcols = []
            selected_elements = []

            # selected_ids хранит id_col
            for idcol in list(self.collection.selected_ids):
                elem = self.collection.get_element_by_id_col(idcol)
                if elem:
                    if elem.get('isInherited', False):
                        inherited_idcols.append(idcol)
                    selected_elements.append(elem)

            if inherited_idcols:
                QMessageBox.warning(
                    self,
                    "Удаление запрещено",
                    "Среди выбранных элементов есть унаследованные от базового "
                    "класса. Их удалить нельзя.\n\n"
                    f"Унаследованных элементов в выделении: {len(inherited_idcols)}"
                )

            # remove_element работает с DB-ID
            for elem in selected_elements:
                if not elem.get('isInherited', False):
                    self.collection.remove_element(elem['db_id'])

            self.collection.clear_selection()
            self.update_properties_panel()
            self._update_active_handles()
            event.accept()
        else:
            super().keyPressEvent(event)