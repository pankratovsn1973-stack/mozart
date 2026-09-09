# Полный путь: dialogs/class_edit_dialog.py
# -- coding: utf-8 --
"""
Главное окно редактирования структуры класса ERP.
Часть 1 из 4. Импорты, конфигурация и интерактивные хендлы (Move/Resize).
"""
isDebug = 0  # 1 = печатать отладочные принты, 0 = тихо

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QMenu, QSizePolicy, QGraphicsProxyWidget,
    QGraphicsObject, QGraphicsSimpleTextItem
)
from PySide6.QtCore import Qt, QPoint, QRectF, QPointF, Signal, QObject, QEvent
from PySide6.QtGui import QAction, QPen, QColor, QBrush, QKeyEvent, QPainter, QFont, QCursor
import json
from typing import Optional, Dict, List, Any
from database import DatabaseService
from services.class_data_service import ClassDataService
from dialogs.collection_manager import CollectionManager
from controls import create_control
from lang.local_translator import LocalTranslator


class MoveHandleItem(QGraphicsObject):
    """Плавающий хендл перемещения в виде руки. Позиционируется в ЛЕВОМ нижнем углу."""
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
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start = event.scenePos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

            # Железная эмуляция зажатого Ctrl на этапе нажатия
            event.setModifiers(event.modifiers() | Qt.KeyboardModifier.ControlModifier)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # Удерживаем Ctrl во время движения
            event.setModifiers(event.modifiers() | Qt.KeyboardModifier.ControlModifier)
            delta = event.scenePos() - self.drag_start
            if self.collection and len(self.collection.selected_ids) > 0:
                self.collection.move_selected(delta.x(), delta.y())
            self.drag_start = event.scenePos()
            self.update_position()
            event.accept()
        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

            # ОТЛАДОЧНЫЙ ВЫВОД В КОНСОЛЬ ПОСЛЕ ПЕРЕМЕЩЕНИЯ
            if self.collection:
                selected_ids = list(self.collection.selected_ids)
                print("\n" + "="*50)
                print(f"[CONSOLES LOG] Левая кнопка мыши ОТПУЩЕНА на хендле ПЕРЕМЕЩЕНИЯ (✋)")
                print(f"Количество выделенных объектов в коллекции: {len(selected_ids)}")
                print("Список выделенных объектов:")
                for eid in selected_ids:
                    elem = self.collection.get_element(eid)
                    alias = elem.get('calias', 'Unknown') if elem else 'Unknown'
                    cclass = elem.get('cclass', 'Unknown') if elem else 'Unknown'
                    print(f"  -> ID: {eid} | Алиас: {alias} | Тип: {cclass}")
                print("="*50 + "\n")

            if self.dialog:
                self.dialog._update_selection_visuals()
                self.dialog.update_properties_panel()
                self.dialog._update_active_handles()

            self.update_position()
            event.accept()
            return
        super().mouseReleaseEvent(event)



class ResizeHandleItem(QGraphicsObject):
    """Плавающий хендл ресайза со стрелками. horizontal=ширина, vertical=высота."""
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

        icon_text = "↔" if axis == 'horizontal' else "↕"
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
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = True
            self.drag_start = event.scenePos()

            # Эмулируем Ctrl на этапе нажатия
            event.setModifiers(event.modifiers() | Qt.KeyboardModifier.ControlModifier)
            event.accept()
        else:
            super().mousePressEvent(event)




    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # Удерживаем Ctrl во время изменения размеров
            event.setModifiers(event.modifiers() | Qt.KeyboardModifier.ControlModifier)
            delta = event.scenePos() - self.drag_start
            if self.collection and len(self.collection.selected_ids) > 0:
                if self.axis == 'vertical':
                    self.collection.resize_selected(0, delta.y())
                else:
                    self.collection.resize_selected(delta.x(), 0)
            self.drag_start = event.scenePos()
            self.update_position()
            event.accept()
        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_resizing:
            self.is_resizing = False

            # ОТЛАДОЧНЫЙ ВЫВОД В КОНСОЛЬ ПОСЛЕ ИЗМЕНЕНИЯ РАЗМЕРА
            if self.collection:
                selected_ids = list(self.collection.selected_ids)
                print("\n" + "="*50)
                print(f"[CONSOLES LOG] Левая кнопка мыши ОТПУЩЕНА на хендле РЕСАЙЗА ([{self.axis}])")
                print(f"Количество выделенных объектов в коллекции: {len(selected_ids)}")
                print("Список выделенных объектов:")
                for eid in selected_ids:
                    elem = self.collection.get_element(eid)
                    alias = elem.get('calias', 'Unknown') if elem else 'Unknown'
                    cclass = elem.get('cclass', 'Unknown') if elem else 'Unknown'
                    print(f"  -> ID: {eid} | Алиас: {alias} | Тип: {cclass}")
                print("="*50 + "\n")

            if self.dialog:
                self.dialog._update_selection_visuals()
                self.dialog.update_properties_panel()
                self.dialog._update_active_handles()

            self.update_position()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ControlGraphicsItem(QGraphicsObject):
    """Графический элемент контрола. Эмитит geometry_changed для синхронизации хендлов."""
    selected_changed = Signal(object, bool)
    geometry_changed = Signal(QRectF)

    def __init__(self, element_id: int, control_widget, parent=None, collection=None, is_logical=False):
        super().__init__(parent)
        self.element_id = element_id
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

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def set_rect(self, x, y, w, h):
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)
        if self.proxy:
            self.proxy.setPos(5, 5)
            self.proxy.resize(max(20, w - 10), max(20, h - 10))
        self.update()
        self.geometry_changed.emit(self._rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.geometry_changed.emit(self._rect)
        return super().itemChange(change, value)

    def rect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        painter.save()

        # КРИТИЧЕСКИЙ ФИКС: Отрисовываем синюю рамку ВСЕГДА, когда in-memory модель (CollectionManager)
        # считает этот элемент выделенным. Полностью игнорируем фокус сцены Qt!
        is_really_selected = False
        if self.collection and self.element_id in self.collection.selected_ids:
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
            label = getattr(self.control_widget, 'objectName', f"ID: {self.element_id}")
            if self.is_logical:
                label = f"[COL] {label}"
            painter.drawText(self._rect, Qt.AlignmentFlag.AlignCenter, label)
        painter.restore()

    def set_geometry(self, x: float, y: float, width: float, height: float):
        self.setPos(x, y)
        self.set_rect(0, 0, max(30, width), max(20, height))
        if self.collection:
            self.collection.update_element_data(self.element_id, {
                'x': x, 'y': y, 'width': width, 'height': height
            }, from_graphics=True)

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
    """Кастомный View. Разделяет одиночный клик по контейнеру и протягивание рамки выделения."""

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

        # 1. Плавающие хендлы имеют высший приоритет
        for item in items_at_pos:
            if isinstance(item, (MoveHandleItem, ResizeHandleItem)):
                super().mousePressEvent(event)
                return

        # ФИКС: Берем самый верхний графический элемент, если список не пуст, а не весь список целиком!
        item_at_pos = items_at_pos[0] if items_at_pos else None
        cgi = self._find_cgi(item_at_pos)

        # Правая кнопка - контекстное меню
        if event.button() == Qt.MouseButton.RightButton:
            if cgi and self.dialog and cgi.element_id in self.dialog.collection.selected_ids:
                self.dialog._show_context_menu(scene_pos)
            event.accept()
            return

        # Левая кнопка - запоминаем старт для возможного драга рамки выделения
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

            # Проверяем порог движения для начала выделения рамкой
            if (abs(delta.x()) > self.DRAG_THRESHOLD or abs(delta.y()) > self.DRAG_THRESHOLD) and not self._drag_rect_item:
                is_root_container = False
                if self._potential_cgi and self.dialog:
                    elem = self.dialog.collection.get_element(self._potential_cgi.element_id)
                    if elem and elem.get('cclass') == 'container' and elem.get('parent_id') is None:
                        is_root_container = True

                # Создаем рамку только если тянем из пустоты или главного контейнера
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

            # Обновляем геометрию рамки
            if self._drag_rect_item:
                rect = QRectF(self._drag_rect_start, scene_pos).normalized()
                self._drag_rect_item.setRect(rect)
                event.accept()
                return

        super().mouseMoveEvent(event)



    def mouseReleaseEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        items_at_pos = self.scene().items(scene_pos)

        # КРИТИЧЕСКИЙ ФИКС: Если мышка отпускается НАД хендлом ресайза или перемещения,
        # мы даем хендлу завершить работу и СРАЗУ выходим из метода,
        # не позволяя коду ниже воспринять это как "клик по пустому месту"!
        for item in items_at_pos:
            if isinstance(item, (MoveHandleItem, ResizeHandleItem)):
                super().mouseReleaseEvent(event)
                return  # <-- ВАЖНО: Мгновенный выход! Логика ниже не запустится.

        # Если мы отпускали мышь НЕ над хендлами, то идет стандартная обработка рамки/кликов
        if event.button() == Qt.MouseButton.LeftButton:
            ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

            # СЦЕНАРИЙ А: Было выделение рамкой (был драг)
            if self._drag_rect_item and self._drag_rect_start:
                rect = QRectF(self._drag_rect_start, scene_pos).normalized()

                self.scene().removeItem(self._drag_rect_item)
                self._drag_rect_item = None
                self._drag_rect_start = None
                self._potential_cgi = None

                hit_ids = []
                container_id = None

                if self.dialog:
                    for eid, item in self.dialog.graphics_items.items():
                        elem = self.dialog.collection.get_element(eid)
                        if not elem:
                            continue

                        if elem.get('cclass') == 'container' and elem.get('parent_id') is None:
                            continue

                        item_rect = item.sceneBoundingRect()
                        if rect.intersects(item_rect):
                            hit_ids.append(eid)
                            if container_id is None:
                                container_id = elem.get('parent_id')

                    if hit_ids:
                        same_container_ids = []
                        for eid in hit_ids:
                            elem = self.dialog.collection.get_element(eid)
                            if elem and elem.get('parent_id') == container_id:
                                same_container_ids.append(eid)

                        if same_container_ids:
                            if not ctrl:
                                self.dialog._clear_all_selection_visuals()
                                self.dialog.collection.clear_selection()

                            if ctrl:
                                for eid in same_container_ids:
                                    self.dialog.collection.add_to_selection(eid)
                            else:
                                self.dialog.collection.set_selection(same_container_ids, container_id)

                            for eid in self.dialog.collection.selected_ids:
                                g_item = self.dialog.graphics_items.get(eid)
                                if g_item:
                                    g_item.is_selected = True

                            self.dialog._update_selection_visuals()
                            self.dialog.update_properties_panel()

                    self.dialog._update_active_handles()
                event.accept()
                return

            # СЦЕНАРИЙ Б: Рамка НЕ создавалась (короткий одиночный клик мыши)
            else:
                self._drag_rect_item = None
                self._drag_rect_start = None

                cgi = self._potential_cgi
                self._potential_cgi = None

                if cgi:
                    if self.dialog:
                        elem = self.dialog.collection.get_element(cgi.element_id)
                        if elem and not (elem.get('cclass') == 'container' and elem.get('parent_id') is None):
                            for eid, item in self.dialog.graphics_items.items():
                                el = self.dialog.collection.get_element(eid)
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
        # Страховка: если сюда случайно передали список элементов, берем первый из них
        if isinstance(item, list):
            if not item:
                return None
            item = item[0]

        # Идем вверх по иерархии родителей, пока не найдем ControlGraphicsItem
        while item:
            if isinstance(item, ControlGraphicsItem):
                return item
            item = item.parentItem()
        return None


class ClassEditDialog(QDialog):
    """Диалог редактирования класса."""

    def __init__(self, parent=None, db: DatabaseService = None, version_id: int = -1, mode: str = 'add'):
        super().__init__(parent)
        self.db = db
        self.version_id = version_id
        self.mode = mode
        self.class_service = ClassDataService(db) if db else None
        self.translator = LocalTranslator()
        self.collection = CollectionManager()
        self.graphics_items: Dict[int, ControlGraphicsItem] = {}
        self.class_data = None
        self.class_name = ""

        self._active_move_handle: Optional[MoveHandleItem] = None
        self._active_resize_h_handle: Optional[ResizeHandleItem] = None
        self._active_resize_v_handle: Optional[ResizeHandleItem] = None

        self.setWindowTitle(self.translator.tr('dialog_edit_class'))
        self.resize(1200, 800)
        self.setup_ui()

        if mode == 'edit' and version_id > 0:
            self.load_class_data(version_id)

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
        toolbar.addWidget(QLabel("Шаг:"))
        toolbar.addWidget(self.grid_size_combo)
        toolbar.addSeparator()

        self.btn_methods = QPushButton(self.translator.tr('btn_methods'))
        self.btn_signals = QPushButton(self.translator.tr('btn_signals'))
        toolbar.addWidget(self.btn_methods)
        toolbar.addWidget(self.btn_signals)

        self.class_info_label = QLabel("")
        toolbar.addWidget(self.class_info_label)

        main_layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_source_panel())
        splitter.addWidget(self._create_scene_panel())
        splitter.addWidget(self._create_properties_panel())
        splitter.setSizes([250, 700, 250])
        main_layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

    def _create_source_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Классы для инъекции:"))
        self.source_tree = QTreeWidget()
        self.source_tree.setHeaderLabels(["Имя"])
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
        layout.addWidget(QLabel("Свойства:"))
        self.properties_table = QTableWidget(0, 2)
        self.properties_table.setHorizontalHeaderLabels(["Свойство", "Значение"])
        self.properties_table.horizontalHeader().setStretchLastSection(True)
        self.properties_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.properties_table.cellChanged.connect(self._on_property_table_changed)
        layout.addWidget(self.properties_table)
        return panel

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
            self.class_info_label.setText(f"<b>{self.class_name}</b> (ID: {version_id})")
            self.load_controls_from_db()
            self.setWindowTitle(f"{self.translator.tr('dialog_edit_class')}: {self.class_name}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()

    def load_controls_from_db(self):
        if not self.class_data:
            return
        self.collection = CollectionManager()
        self.graphics_items.clear()

        version = self._normalize_version(self.class_data.get('version'))
        current_version_id = version.get('id')
        if not current_version_id:
            return

        if version.get('is_visible', True):
            root_data = {
                'parent_id': None, 'calias': version.get('c_name', ''),
                'cclass': 'container',
                'x': float(version.get('x', 50)), 'y': float(version.get('y', 50)),
                'width': float(version.get('width', 400)), 'height': float(version.get('height', 300)),
                'properties': {'label': version.get("c_name", "")}, 'is_new': False
            }
            self.collection._elements[current_version_id] = {**root_data, 'id': current_version_id}

        all_classes_raw = self.db.execute_query("SELECT id, c_name FROM class_erp.mozartclasses") or []
        classes_db = {str(r[0]): str(r[1]).strip().strip('"') for r in all_classes_raw}

        all_versions_raw = self.db.execute_query(
            "SELECT id, c_base_class, c_base_source, i_base_class FROM class_erp.class_version"
        ) or []
        versions_db = {
            str(r[0]): {
                'base_class': str(r[1]).strip().strip('"'),
                'source': str(r[2]).strip().strip('"'),
                'base_id': str(r[3]) if r[3] else None
            } for r in all_versions_raw
        }

        def get_root_qt_class(version_id: str) -> str:
            visited, current = set(), version_id
            while current and current in versions_db and current not in visited:
                visited.add(current)
                v_data = versions_db[current]
                if v_data['source'] == 'PYTHON':
                    return v_data['base_class']
                current = v_data['base_id']
            return 'QWidget'

        parent_class_id = str(version.get('i_base_class')) if version.get('i_base_class') else None
        root_parent_qt = get_root_qt_class(parent_class_id) if parent_class_id else 'QWidget'
        is_horizontal_layout = root_parent_qt in ['QTableWidget', 'QTreeView', 'QListWidget', 'QComboBox']

        qt_to_factory = {
            'QLabel': 'label', 'QLineEdit': 'textbox', 'QPushButton': 'button',
            'QCheckBox': 'checkbox', 'QComboBox': 'combobox', 'QDateEdit': 'datebox',
            'QListWidget': 'listbox', 'QPlainTextEdit': 'memo', 'QWidget': 'container',
            'QGroupBox': 'container', 'QTabWidget': 'tabcontainer', 'QRadioButton': 'radiobutton',
            'QObject': 'baseinvisible', 'QTreeView': 'treeview', 'QTableWidget': 'grid',
            'QMainWindow': 'container', 'QDialog': 'container'
        }

        sql = """
            SELECT cv.id, mc.c_name, cv.txt_properties, cv.i_parent_id, cv.is_visible, cv.i_base_class
            FROM class_erp.class_version cv
            JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
            WHERE cv.i_parent_id = %s AND cv.dt_end IS NULL
            ORDER BY cv.id
        """
        rows = self.db.execute_query(sql, (current_version_id,))
        x_offset, y_offset = 10.0, 10.0
        default_w, default_h = 150.0, 30.0

        if rows:
            for row in rows:
                sub_id = row[0]
                sub_name = str(row[1] or '').strip().strip('"')
                sub_props_json = row[2]
                parent_id = row[3]
                is_visible = row[4]
                child_version_id = str(row[5]) if row[5] else None

                root_qt = get_root_qt_class(child_version_id) if child_version_id else 'QWidget'
                factory_type = qt_to_factory.get(root_qt, 'container')

                props = json.loads(sub_props_json) if sub_props_json else {}

                x = float(props.get('x', x_offset if is_horizontal_layout else x_offset))
                y = float(props.get('y', y_offset if is_horizontal_layout else y_offset))
                w = float(props.get('width', default_w))
                h = float(props.get('height', default_h))

                if 'x' not in props and 'y' not in props:
                    if is_horizontal_layout:
                        x_offset += w + 5
                    else:
                        y_offset += h + 5

                elem_data = {
                    'id': sub_id, 'parent_id': parent_id, 'calias': sub_name, 'cclass': factory_type,
                    'x': x, 'y': y, 'width': w, 'height': h, 'properties': props, 'is_new': False,
                    'is_logical': not is_visible
                }
                self.collection._elements[sub_id] = elem_data
        else:
            self._create_demo_controls()

        self.render_scene()


    def _normalize_version(self, version_dict: dict) -> dict:
        def to_str(val):
            if val is None: return ""
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
            'txt_properties': to_str(version_dict.get('txt_properties'))
        }

    def _create_demo_controls(self):
        for data in [
            {'cclass': 'label', 'calias': 'lbl_demo', 'x': 20, 'y': 50, 'width': 100, 'height': 26,
             'properties': {'text': 'Демо-метка:'}},
            {'cclass': 'textbox', 'calias': 'txt_demo', 'x': 130, 'y': 50, 'width': 150, 'height': 26,
             'properties': {'placeholder': 'Введите текст'}},
            {'cclass': 'button', 'calias': 'btn_demo', 'x': 290, 'y': 50, 'width': 80, 'height': 26,
             'properties': {'text': 'Кнопка'}}
        ]:
            self.collection.add_element({**data, 'parent_id': None, 'is_new': True, 'is_logical': False})

    def render_scene(self):
        self.scene.clear()
        self.graphics_items.clear()
        self._draw_grid()

        all_elements = []
        for eid in list(self.collection._elements.keys()):
            elem = self.collection.get_element(eid)
            if elem:
                all_elements.append((eid, elem))

        sorted_elements = sorted(all_elements,
                                 key=lambda item: (item[1].get('parent_id') is not None, item[0]))

        for elem_id, elem_data in sorted_elements:
            parent_id = elem_data.get('parent_id')
            parent_item = self.graphics_items.get(parent_id) if parent_id else None
            item = self.create_control_item(elem_id, elem_data, parent_item)
            if item:
                item.set_geometry(elem_data.get('x', 50), elem_data.get('y', 50), elem_data.get('width', 150),
                                  elem_data.get('height', 30))
                self.graphics_items[elem_id] = item
                self.collection.link_graphic_item(elem_id, item)
                if elem_data.get('cclass') == 'container':
                    self.collection.select_element(elem_id, additive=False)
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

    def create_control_item(self, element_id: int, element_data: Dict,
                            parent_item: Optional[ControlGraphicsItem] = None) -> ControlGraphicsItem:
        cclass = element_data.get('cclass', 'textbox')
        is_logical = element_data.get('is_logical', False)
        widget = None

        if not is_logical:
            if cclass == 'container':
                from PySide6.QtWidgets import QGroupBox
                widget = QGroupBox()
                widget.setTitle(element_data.get('properties', {}).get('label', 'Контейнер'))
                widget.setStyleSheet(
                    "QGroupBox { font-weight: bold; border: 2px solid #8080a0; border-radius: 5px; margin-top: 10px; } "
                    "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }"
                )
            else:
                widget = create_control(cclass, parent=None, db=self.db)

            if widget and cclass == 'button':
                correct_text = element_data.get('properties', {}).get('text', '')
                if not isinstance(widget, QPushButton):
                    real_btn = widget.findChild(QPushButton)
                    if real_btn:
                        real_btn.setParent(None)
                        widget.deleteLater()
                        widget = real_btn
                if isinstance(widget, QPushButton):
                    lay = widget.layout()
                    if lay:
                        QWidget().setLayout(lay)
                    for child in widget.findChildren(QWidget):
                        if isinstance(child, QLabel):
                            child.setParent(None)
                            child.deleteLater()
                    if correct_text:
                        widget.setText(correct_text)
        else:
            widget = QWidget()
            widget.setObjectName(element_data.get('calias', f"col_{element_id}"))

        if not widget:
            return None

        if hasattr(widget, 'properties'):
            widget.properties = element_data.get('properties', {})

        widget.setObjectName(element_data.get('calias', f"control_{element_id}"))

        item = ControlGraphicsItem(element_id, widget, parent=parent_item, collection=self.collection,
                                   is_logical=is_logical)

        if parent_item is None:
            self.scene.addItem(item)

        if self.scene and widget:
            item.proxy = self.scene.addWidget(widget)
            if item.proxy:
                item.proxy.setParentItem(item)
                item.proxy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
                item.proxy.installSceneEventFilter(item)
                widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                for child in widget.findChildren(QWidget):
                    child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                item.proxy.setPos(5, 5)
                rect = item.rect()
                item.proxy.resize(max(20, rect.width() - 10), max(20, rect.height() - 10))

        item.selected_changed.connect(self._on_item_selected)
        return item

    def _on_item_selected(self, item: ControlGraphicsItem, selected: bool):
        if not selected:
            return
        self.update_properties_panel()

    def _handle_click_selection(self, item: ControlGraphicsItem, ctrl_pressed: bool):
        if ctrl_pressed:
            result = self.collection.add_to_selection(item.element_id)
            if not result:
                reply = QMessageBox.question(
                    self,
                    "Смена контейнера",
                    "Вы собираетесь начать выделение контролов другого контейнера.\n"
                    "Имеющееся выделение будет отменено.\n\nПродолжить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self._clear_all_selection_visuals()
                    self.collection.clear_selection()
                    self.collection.add_to_selection(item.element_id)
            else:
                if item.element_id in self.collection.selected_ids:
                    item.set_selected(True)
                else:
                    item.set_selected(False)
        else:
            self._clear_all_selection_visuals()
            self.collection.clear_selection()
            self.collection.select_element(item.element_id, additive=False)
            item.set_selected(True)

        self._update_selection_visuals()
        self.update_properties_panel()
        self._update_active_handles()

    def _clear_all_selection_visuals(self):
        for gid, gitem in self.graphics_items.items():
            if gitem.is_selected:
                gitem.set_selected(False)

    def _update_selection_visuals(self):
        selected = self.collection.selected_ids
        for eid, item in self.graphics_items.items():
            should_be_selected = eid in selected
            if item.is_selected != should_be_selected:
                item.set_selected(should_be_selected)

    def _update_active_handles(self):
        """Управляет плавающими хендлами для ведущего элемента."""
        for handle in [self._active_move_handle, self._active_resize_h_handle, self._active_resize_v_handle]:
            if handle and handle.scene():
                try:
                    target_item = handle.target_item
                    target_item.geometry_changed.disconnect(handle.update_position)
                except (TypeError, RuntimeError):
                    pass
                handle.scene().removeItem(handle)

        self._active_move_handle = None
        self._active_resize_h_handle = None
        self._active_resize_v_handle = None

        if not self.collection.selected_ids:
            return

        last_id = self.collection.last_selected_id
        if last_id and last_id in self.graphics_items:
            target_item = self.graphics_items[last_id]
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

    def _show_context_menu(self, scene_pos: QPointF):
        selected = self.collection.selected_ids
        if len(selected) < 2:
            return

        menu = QMenu(self)
        act_left = menu.addAction("Выровнять слева")
        act_right = menu.addAction("Выровнять справа")
        act_top = menu.addAction("Выровнять сверху")
        act_bottom = menu.addAction("Выровнять снизу")
        menu.addSeparator()
        act_eq_w = menu.addAction("Выровнять ширину")
        act_eq_h = menu.addAction("Выровнять высоту")

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

        self._update_selection_visuals()
        self.update_properties_panel()
        self._update_active_handles()

    def _get_default_properties(self, cclass: str) -> list:
        if cclass == 'button':
            return [('text', 'Текст'), ('icon', 'Рисунок (путь)'), ('is_flat', 'Плоская'),
                    ('is_checkable', 'Залипающая')]
        elif cclass == 'textbox':
            return [('text', 'Текст'), ('placeholder', 'Подсказка'), ('readonly', 'Только чтение'),
                    ('max_length', 'Макс. длина')]
        elif cclass == 'label':
            return [('text', 'Текст'), ('word_wrap', 'Перенос слов')]
        elif cclass == 'combobox':
            return [('items', 'Список значений'), ('editable', 'Редактируемый')]
        elif cclass == 'grid':
            return [('allow_filter', 'Фильтр'), ('allow_sort', 'Сортировка')]
        elif cclass == 'baseinvisible':
            return [('header_text', 'Заголовок'), ('binding_field', 'Привязка к полю'), ('data_type', 'Тип данных'),
                    ('width', 'Ширина'), ('readonly', 'Только чтение')]
        return []

    def update_properties_panel(self):
        self.properties_table.blockSignals(True)
        self.properties_table.setRowCount(0)
        if not self.collection.selected_ids:
            self.properties_table.blockSignals(False)
            return

        last_id = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element(last_id)
        if not elem_data:
            self.properties_table.blockSignals(False)
            return

        calias, cclass = elem_data.get('calias', ''), elem_data.get('cclass', '')
        self.properties_table.setHorizontalHeaderLabels([self.translator.tr('field_property'), f"{calias} ({cclass})"])

        properties = elem_data.get('properties', {})
        row = 0
        for prop_key, prop_label, prop_value in [
            ('id', 'ID', str(elem_data.get('id', ''))), ('calias', 'Алиас', calias),
            ('cclass', 'Тип', cclass), ('x', 'X', str(elem_data.get('x', 0))),
            ('y', 'Y', str(elem_data.get('y', 0))), ('width', 'Ширина', str(elem_data.get('width', 100))),
            ('height', 'Высота', str(elem_data.get('height', 30)))
        ]:
            self.properties_table.insertRow(row)
            self.properties_table.setItem(row, 0, QTableWidgetItem(prop_label))
            self.properties_table.setItem(row, 1, QTableWidgetItem(prop_value))
            self.properties_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, prop_key)
            row += 1

        for prop_key, prop_label in self._get_default_properties(cclass):
            self.properties_table.insertRow(row)
            self.properties_table.setItem(row, 0, QTableWidgetItem(prop_label))
            self.properties_table.setItem(row, 1, QTableWidgetItem(str(properties.get(prop_key, ''))))
            self.properties_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, prop_key)
            row += 1

        schema_keys = [p[0] for p in self._get_default_properties(cclass)]
        for prop_key, prop_value in properties.items():
            if prop_key not in schema_keys:
                self.properties_table.insertRow(row)
                self.properties_table.setItem(row, 0, QTableWidgetItem(prop_key))
                self.properties_table.setItem(row, 1, QTableWidgetItem(str(prop_value)))
                self.properties_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, prop_key)
                row += 1

        self.properties_table.blockSignals(False)

    def _on_property_table_changed(self, row: int, column: int):
        if column != 1 or not self.collection.selected_ids:
            return
        item = self.properties_table.item(row, column)
        if not item:
            return
        prop_key = item.data(Qt.ItemDataRole.UserRole)
        if not prop_key:
            return

        new_value = item.text()
        last_id = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element(last_id)
        if not elem_data:
            return

        update_data = {}
        if prop_key in ['x', 'y', 'width', 'height']:
            try:
                update_data[prop_key] = float(new_value)
            except ValueError:
                return
        elif prop_key in ['calias', 'cclass']:
            update_data[prop_key] = new_value
        elif prop_key == 'id':
            return
        else:
            props = dict(elem_data.get('properties', {}))
            props[prop_key] = new_value
            update_data['properties'] = props

        self.collection.update_element_data(last_id, update_data)


        if last_id in self.graphics_items:
            item_g = self.graphics_items[last_id]
            if prop_key == 'x':
                item_g.setPos(float(new_value), item_g.pos().y())
            elif prop_key == 'y':
                item_g.setPos(item_g.pos().x(), float(new_value))
            elif prop_key == 'width':
                item_g.set_rect(0, 0, float(new_value), item_g.rect().height())
            elif prop_key == 'height':
                item_g.set_rect(0, 0, item_g.rect().width(), float(new_value))
            elif prop_key == 'calias':
                if hasattr(item_g.control_widget, 'setObjectName'):
                    item_g.control_widget.setObjectName(new_value)
                if hasattr(item_g.control_widget, 'calias'):
                    item_g.control_widget.calias = new_value

    def toggle_grid(self):
        self._draw_grid()
        self.btn_grid.setText(
            self.translator.tr('btn_grid_off') if self.btn_grid.isChecked() else self.translator.tr('btn_grid_on'))

    def on_grid_size_changed(self, size: str):
        self._draw_grid()

    def show_methods_dialog(self):
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс")
            return
        from dialogs.methods_dialog import MethodsDialog
        MethodsDialog(self, db=self.db, version_id=self.version_id).exec_()

    def show_signals_dialog(self):
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс")
            return
        from dialogs.signals_dialog import SignalsDialog
        SignalsDialog(self, db=self.db, version_id=self.version_id).exec_()

    def inject_class(self, item: QTreeWidgetItem, column: int):
        version_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not version_id:
            return
        class_data = self.class_service.get_class_version(version_id)
        if not class_data:
            return
        version = class_data.get('version', {})
        cclass = version.get('c_name', '').lower()
        if not version.get('is_visible', True):
            QMessageBox.warning(self, "Внимание", f"Класс {cclass} является невизуальным")
            return

        element_data = {'parent_id': None, 'calias': f"{cclass}_{self.collection.get_next_id()}", 'cclass': cclass,
                        'x': 100, 'y': 100, 'width': 150, 'height': 30,
                        'properties': {'label': cclass, 'binding_field': ''}}
        new_id = self.collection.add_element(element_data)
        self.create_control_item(new_id, element_data)
        self.update_properties_panel()

    def save_class(self):
        if not self.class_service:
            QMessageBox.critical(self, "Ошибка", "Сервис классов не инициализирован")
            return
        try:
            if self.mode == 'add':
                QMessageBox.information(self, "Инфо", "Класс создан (демо)")
            else:
                QMessageBox.information(self, "Инфо", "Класс обновлен (демо)")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            for elem_id in list(self.collection.selected_ids):
                self.collection.remove_element(elem_id)
                if elem_id in self.graphics_items:
                    self.scene.removeItem(self.graphics_items[elem_id])
                    del self.graphics_items[elem_id]
            self.collection.clear_selection()
            self.update_properties_panel()
            self._update_active_handles()
            event.accept()
        else:
            super().keyPressEvent(event)