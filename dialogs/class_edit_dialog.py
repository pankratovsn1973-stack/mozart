# Полный путь: dialogs/class_edit_dialog.py
# -*- coding: utf-8 -*-
"""
Главное окно редактирования структуры класса ERP.
Содержит визуальный редактор (сцену QGraphicsView), панель свойств, тулбар.
Использует CollectionManager для хранения состояния объектов в памяти.
Реализует логику выделения, перемещения и ресайза мышью.
Поддерживает составные классы (Reference) с правильной иерархией.
Интегрируется с ClassDataService для сохранения метаданных.
Не создает новых соединений с БД, использует переданный экземпляр.
Обрабатывает составные контролы как группы объектов с i_parent_id.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QMenu, QSizePolicy, QGraphicsProxyWidget,
    QGraphicsObject
)
from PySide6.QtCore import Qt, QPoint, QRectF, QPointF, Signal, QObject, QEvent
from PySide6.QtGui import QAction, QPen, QColor, QBrush, QKeyEvent, QPainter, QFont
import json
from typing import Optional, Dict, List, Any

from database import DatabaseService
from services.class_data_service import ClassDataService
from dialogs.collection_manager import CollectionManager
from controls import create_control
from lang.local_translator import LocalTranslator


class ControlGraphicsItem(QGraphicsObject):
    """
    Графический элемент контрола на сцене, наследующий QGraphicsObject.
    Это позволяет использовать сигналы PySide6 (selected_changed).
    Отвечает за отрисовку рамки выделения, маркеров изменения размера
    и проксирование реального виджета контрола.
    Хранит прямую ссылку на CollectionManager для синхронизации данных.
    """
    HANDLE_SIZE = 10
    # Сигнал изменения состояния выделения
    selected_changed = Signal(object, bool)

    def __init__(self, element_id: int, control_widget, parent=None, collection=None):
        super().__init__(parent)

        self.element_id = element_id
        self.control_widget = control_widget
        self.collection = collection  # Прямая ссылка на коллекцию

        self.is_selected = False
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start = QPointF()
        self.drag_start_pos = QPointF()
        self.resize_start_size = QRectF()

        # Флаги для QGraphicsItem
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)

        self.proxy = None

        # Устанавливаем начальный размер
        self.set_rect(0, 0, 150, 40)

        # Стиль по умолчанию
        self._pen = QPen(QColor(100, 100, 150), 1.5)
        self._brush = QBrush(QColor(240, 240, 255, 200))

        print(f"[LOG] ControlGraphicsItem.__init__: Создан объект ID={element_id}, тип={type(control_widget).__name__}")

    def boundingRect(self):
        """Обязательный метод для QGraphicsObject"""
        return self._rect.adjusted(-2, -2, 2, 2)

    def set_rect(self, x, y, w, h):
        """Установка внутреннего прямоугольника"""
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)
        if self.proxy:
            self.proxy.setPos(5, 5)
            self.proxy.resize(max(20, w - 10), max(20, h - 10))
        self.update_handles()

    def rect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        """Отрисовка элемента."""
        painter.save()

        # Рисуем фон и рамку
        if self.is_selected:
            painter.setBrush(QBrush(QColor(200, 220, 255, 200)))
            painter.setPen(QPen(QColor(0, 120, 215), 2.5, Qt.PenStyle.SolidLine))
        else:
            painter.setBrush(self._brush)
            painter.setPen(self._pen)

        painter.drawRoundedRect(self._rect, 4, 4)

        # Рисуем маркеры, если выбраны
        if self.is_selected:
            # Маркер перемещения (зеленый)
            if hasattr(self, '_move_handle_rect'):
                painter.setBrush(QBrush(QColor(0, 255, 0, 180)))
                painter.setPen(QPen(QColor(0, 200, 0), 1.5))
                painter.drawRect(self._move_handle_rect)

            # Маркер ресайза (синий)
            if hasattr(self, '_resize_handle_rect'):
                painter.setBrush(QBrush(QColor(0, 120, 255, 180)))
                painter.setPen(QPen(QColor(0, 0, 200), 1.5))
                painter.drawRect(self._resize_handle_rect)

        # Если нет прокси (виджета), рисуем текст
        if not self.proxy or not self.control_widget:
            painter.setPen(QPen(QColor(50, 50, 80)))
            font = QFont("Arial", 8)
            painter.setFont(font)
            text = f"ID: {self.element_id}"
            painter.drawText(self._rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def set_geometry(self, x: float, y: float, width: float, height: float):
        """Установка геометрии элемента. Синхронизирует с коллекцией."""
        self.setPos(x, y)
        self.set_rect(0, 0, max(30, width), max(20, height))

        # Обновляем данные в коллекции, если она доступна
        if self.collection and self.element_id in self.collection.elements:
            elem_data = self.collection.elements[self.element_id]
            elem_data['x'] = x
            elem_data['y'] = y
            elem_data['width'] = width
            elem_data['height'] = height
            print(
                f"[LOG] ControlGraphicsItem.set_geometry: ID={self.element_id} -> Pos=({x:.1f},{y:.1f}), Size={width:.1f}x{height:.1f}")

    def update_handles(self):
        """Обновление координат маркеров для отрисовки."""
        rect = self._rect
        size = self.HANDLE_SIZE

        # Координаты маркера перемещения (центр сверху)
        self._move_handle_rect = QRectF(
            rect.width() / 2 - size / 2,
            -size / 2 - 2,
            size,
            size
        )

        # Координаты маркера ресайза (правый нижний угол)
        self._resize_handle_rect = QRectF(
            rect.width() - size / 2,
            rect.height() - size / 2,
            size,
            size
        )

    def set_selected(self, selected: bool):
        """Установка состояния выделения."""
        print(f"[LOG] ControlGraphicsItem.set_selected: ID={self.element_id}, Selected={selected}")
        if self.is_selected != selected:
            self.is_selected = selected
            self.update_handles()
            self.update()
            self.selected_changed.emit(self, selected)

    def sceneEventFilter(self, watched, event):
        """Перехват кликов по внутреннему виджету для выделения рамки."""
        if watched == self.proxy and event.type() == QEvent.Type.GraphicsSceneMousePress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.set_selected(True)
                return False
        return super().sceneEventFilter(watched, event)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_selected and hasattr(self, '_move_handle_rect') and self._move_handle_rect.contains(event.pos()):
                self.is_dragging = True
                self.drag_start = event.scenePos()
                self.drag_start_pos = self.pos()
                event.accept()
                return

            if self.is_selected and hasattr(self, '_resize_handle_rect') and self._resize_handle_rect.contains(
                    event.pos()):
                self.is_resizing = True
                self.drag_start = event.scenePos()
                self.resize_start_size = self.rect()
                event.accept()
                return

            if self.is_selected:
                self.is_dragging = True
                self.drag_start = event.scenePos()
                self.drag_start_pos = self.pos()
                event.accept()
                return

            self.set_selected(True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши."""
        if self.is_dragging:
            delta = event.scenePos() - self.drag_start
            new_pos = self.drag_start_pos + delta

            self.setPos(new_pos)
            self.update_handles()

            if self.collection and self.element_id in self.collection.elements:
                elem_data = self.collection.elements[self.element_id]
                elem_data['x'] = new_pos.x()
                elem_data['y'] = new_pos.y()

            event.accept()
            return

        if self.is_resizing:
            delta = event.scenePos() - self.drag_start
            rect = self.resize_start_size
            new_width = max(30, rect.width() + delta.x())
            new_height = max(20, rect.height() + delta.y())

            self.set_rect(0, 0, new_width, new_height)
            self.update_handles()

            if self.collection and self.element_id in self.collection.elements:
                elem_data = self.collection.elements[self.element_id]
                elem_data['width'] = new_width
                elem_data['height'] = new_height

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши."""
        if self.is_dragging or self.is_resizing:
            self.is_dragging = False
            self.is_resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ClassEditDialog(QDialog):
    """
    Диалог редактирования класса.
    Содержит визуальный редактор (сцену), панель свойств, тулбар.
    Использует CollectionManager для управления состоянием объектов в памяти.
    """

    def __init__(self, parent=None, db: DatabaseService = None,
                 version_id: int = -1, mode: str = 'add'):
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

        self.setWindowTitle(self.translator.tr('dialog_edit_class'))
        self.resize(1200, 800)

        print(f"[LOG] ClassEditDialog.__init__: Инициализация диалога. Mode={mode}, VersionID={version_id}")

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

        self.view = QGraphicsView(self.scene)
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
        layout.addWidget(self.properties_table)
        return panel

    def load_class_data(self, version_id: int):
        print(f"[LOG] ClassEditDialog.load_class_data: Загрузка данных для версии {version_id}")
        if not self.class_service: return
        try:
            self.class_data = self.class_service.get_class_version(version_id)
            if not self.class_data:
                QMessageBox.warning(self, "Внимание", f"Класс {version_id} не найден");
                return
            version = self.class_data.get('version', {})
            self.class_name = version.get('c_name', '')
            self.class_info_label.setText(f"<b>{self.class_name}</b> (ID: {version_id})")
            self.load_controls_from_db()
            self.setWindowTitle(f"{self.translator.tr('dialog_edit_class')}: {self.class_name}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки класса {version_id}: {e}")
            import traceback;
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_controls_from_db(self):
        print(f"[LOG] ClassEditDialog.load_controls_from_db: Начало загрузки контролов")
        if not self.class_data: return
        self.collection = CollectionManager()
        self.graphics_items.clear()
        version = self.class_data.get('version', {})
        current_version_id = version.get('id')
        if not current_version_id: return

        is_visible = version.get('is_visible', True)
        if is_visible:
            self.collection.elements[current_version_id] = {
                'id': current_version_id, 'parent_id': None, 'calias': version.get('c_name', ''),
                'cclass': 'container', 'x': 50, 'y': 50, 'width': 350, 'height': 100,
                'properties': {'label': version.get("c_name", "")}, 'is_new': False
            }

        sql = """
            SELECT cv.id, mc.c_name, cv.c_base_class, cv.txt_properties, cv.i_parent_id
            FROM class_erp.class_version cv
            JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
            WHERE cv.i_parent_id = %s AND cv.dt_end IS NULL
            ORDER BY cv.id
        """
        rows = self.db.execute_query(sql, (current_version_id,))

        if rows:
            cclass_map = {'QLabel': 'label', 'QLineEdit': 'textbox', 'QPushButton': 'button', 'QCheckBox': 'checkbox',
                          'QComboBox': 'combobox'}
            for row in rows:
                sub_id, sub_name, sub_qt_class, sub_props_json, parent_id = row
                cclass = cclass_map.get(sub_qt_class, 'textbox')
                props = json.loads(sub_props_json) if sub_props_json else {}

                if 'Ref_Label' in sub_name or 'lbl' in sub_name.lower():
                    x, y, w, h = 10, 10, 60, 26
                elif 'Ref_TextEdit' in sub_name or 'txt' in sub_name.lower():
                    x, y, w, h = 75, 10, 150, 26
                elif 'Ref_SelectBtn' in sub_name or 'select' in sub_name.lower():
                    x, y, w, h = 230, 10, 50, 26
                elif 'Ref_ClearBtn' in sub_name or 'clear' in sub_name.lower():
                    x, y, w, h = 285, 10, 50, 26
                else:
                    x, y, w, h = 10 + len(self.collection.elements) * 80, 10, 60, 26

                self.collection.elements[sub_id] = {
                    'id': sub_id, 'parent_id': parent_id, 'calias': sub_name, 'cclass': cclass,
                    'x': x, 'y': y, 'width': w, 'height': h, 'properties': props, 'is_new': False
                }
        else:
            self._create_demo_controls()

        self.render_scene()

    def _create_demo_controls(self):
        for data in [
            {'cclass': 'label', 'calias': 'lbl_demo', 'x': 20, 'y': 50, 'width': 100, 'height': 26,
             'properties': {'text': 'Демо-метка:'}},
            {'cclass': 'textbox', 'calias': 'txt_demo', 'x': 130, 'y': 50, 'width': 150, 'height': 26,
             'properties': {'placeholder': 'Введите текст'}},
            {'cclass': 'button', 'calias': 'btn_demo', 'x': 290, 'y': 50, 'width': 80, 'height': 26,
             'properties': {'text': 'Кнопка'}}
        ]:
            self.collection.add_element({**data, 'parent_id': None, 'is_new': True})

    def render_scene(self):
        self.scene.clear()
        self.graphics_items.clear()
        self._draw_grid()
        sorted_elements = sorted(self.collection.elements.items(),
                                 key=lambda item: (item[1].get('parent_id') is not None, item[0]))
        for elem_id, elem_data in sorted_elements:
            parent_id = elem_data.get('parent_id')
            parent_item = self.graphics_items.get(parent_id) if parent_id else None
            item = self.create_control_item(elem_id, elem_data, parent_item)
            if item:
                item.set_geometry(elem_data.get('x', 50), elem_data.get('y', 50), elem_data.get('width', 150),
                                  elem_data.get('height', 30))
                self.graphics_items[elem_id] = item
                if elem_data.get('cclass') == 'container':
                    item.set_selected(True)
                    self.update_properties_panel()

    def _draw_grid(self):
        if not self.btn_grid.isChecked(): return
        grid_size = int(self.grid_size_combo.currentText())
        scene_rect = self.scene.sceneRect()
        pen = QPen(QColor(200, 200, 200, 150), 0.5)
        x = 0
        while x < scene_rect.width(): self.scene.addLine(x, 0, x, scene_rect.height(), pen); x += grid_size
        y = 0
        while y < scene_rect.height(): self.scene.addLine(0, y, scene_rect.width(), y, pen); y += grid_size

    def create_control_item(self, element_id: int, element_data: Dict,
                            parent_item: Optional[ControlGraphicsItem] = None) -> ControlGraphicsItem:
        cclass = element_data.get('cclass', 'textbox')

        if cclass == 'container':
            from PySide6.QtWidgets import QGroupBox
            widget = QGroupBox()
            widget.setTitle(element_data.get('properties', {}).get('label', 'Контейнер'))
            widget.setStyleSheet(
                "QGroupBox { font-weight: bold; border: 2px solid #8080a0; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
        else:
            widget = create_control(cclass, parent=None, db=self.db)

        if not widget: return None

        # ====================================================================
        # ЯДЕРНАЯ ОЧИСТКА КНОПОК ОТ МУСОРА (Лейблы "Кнопка" из модуля controls)
        # ====================================================================
        if cclass == 'button':
            correct_text = element_data.get('properties', {}).get('text', '')

            # Случай 1: Фабрика вернула обертку (не является QPushButton)
            if not isinstance(widget, QPushButton):
                real_btn = widget.findChild(QPushButton)
                if real_btn:
                    print(f"[LOG] ЯДЕРНАЯ ОЧИСТКА: Извлекаем QPushButton из обертки для ID={element_id}")
                    real_btn.setParent(None)
                    widget.deleteLater()
                    widget = real_btn

                    # Случай 2: Это QPushButton (или MozartButton), но с внутренним мусором
            if isinstance(widget, QPushButton):
                lay = widget.layout()
                if lay:
                    # Передаем layout во временный виджет. Это мгновенно убирает
                    # все отступы и пустые места, которые держал layout.
                    QWidget().setLayout(lay)
                    print(f"[LOG] ЯДЕРНАЯ ОЧИСТКА: Уничтожен внутренний layout у кнопки ID={element_id}")

                # Мгновенно открепляем все QLabel
                for child in widget.findChildren(QWidget):
                    if isinstance(child, QLabel):
                        child.setParent(None)
                        child.deleteLater()

                # Принудительно задаем правильный текст из БД
                if correct_text:
                    widget.setText(correct_text)
        # ====================================================================

        if hasattr(widget, 'properties'):
            widget.properties = element_data.get('properties', {})

        widget.setObjectName(element_data.get('calias', f"control_{element_id}"))

        item = ControlGraphicsItem(element_id, widget, parent=parent_item, collection=self.collection)

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

    def _on_item_selected(self, item, selected):
        if selected:
            for other_id, other_item in self.graphics_items.items():
                if other_item != item and other_item.is_selected:
                    other_item.set_selected(False)
            self.collection.select_element(item.element_id)
            self.update_properties_panel()
        else:
            self.collection.selected_ids.discard(item.element_id)
            if not self.collection.selected_ids:
                self.properties_table.setRowCount(0)

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
        return []

    def update_properties_panel(self):
        self.properties_table.blockSignals(True)
        self.properties_table.setRowCount(0)
        if not self.collection.selected_ids:
            self.properties_table.blockSignals(False);
            return
        last_id = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element(last_id)
        if not elem_data:
            self.properties_table.blockSignals(False);
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

    def _on_property_table_changed(self, item: QTableWidgetItem):
        if item.column() != 1 or not self.collection.selected_ids: return
        prop_key = item.data(Qt.ItemDataRole.UserRole)
        if not prop_key: return
        new_value = item.text()
        last_id = list(self.collection.selected_ids)[-1]
        elem_data = self.collection.get_element(last_id)
        if not elem_data: return

        if prop_key in ['id', 'calias', 'cclass', 'x', 'y', 'width', 'height']:
            if prop_key == 'id':
                return
            elif prop_key in ['x', 'y', 'width', 'height']:
                try:
                    elem_data[prop_key] = float(new_value)
                except ValueError:
                    return
            else:
                elem_data[prop_key] = new_value
        else:
            if 'properties' not in elem_data: elem_data['properties'] = {}
            elem_data['properties'][prop_key] = new_value

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
                if hasattr(item_g.control_widget, 'setObjectName'): item_g.control_widget.setObjectName(new_value)
                if hasattr(item_g.control_widget, 'calias'): item_g.control_widget.calias = new_value

    def toggle_grid(self):
        self._draw_grid()
        self.btn_grid.setText(
            self.translator.tr('btn_grid_off') if self.btn_grid.isChecked() else self.translator.tr('btn_grid_on'))

    def on_grid_size_changed(self, size: str):
        self._draw_grid()

    def show_methods_dialog(self):
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс");
            return
        from dialogs.methods_dialog import MethodsDialog
        MethodsDialog(self, db=self.db, version_id=self.version_id).exec_()

    def show_signals_dialog(self):
        if not self.class_service or self.version_id <= 0:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните класс");
            return
        from dialogs.signals_dialog import SignalsDialog
        SignalsDialog(self, db=self.db, version_id=self.version_id).exec_()

    def inject_class(self, item: QTreeWidgetItem, column: int):
        version_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not version_id: return
        class_data = self.class_service.get_class_version(version_id)
        if not class_data: return
        version = class_data.get('version', {})
        cclass = version.get('c_name', '').lower()
        if not version.get('is_visible', True):
            QMessageBox.warning(self, "Внимание", f"Класс {cclass} является невизуальным");
            return
        element_data = {'parent_id': None, 'calias': f"{cclass}_{self.collection.get_next_id()}", 'cclass': cclass,
                        'x': 100, 'y': 100, 'width': 150, 'height': 30,
                        'properties': {'label': cclass, 'binding_field': ''}}
        self.create_control_item(self.collection.add_element(element_data), element_data)
        self.update_properties_panel()

    def save_class(self):
        if not self.class_service:
            QMessageBox.critical(self, "Ошибка", "Сервис классов не инициализирован");
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
            self.collection.selected_ids.clear()
            self.update_properties_panel()
            event.accept()
        else:
            super().keyPressEvent(event)