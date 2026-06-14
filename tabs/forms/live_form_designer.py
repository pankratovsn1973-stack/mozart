# /home/sergey/Documents/configurate/tabs/forms/live_form_designer.py
# -*- coding: utf-8 -*-

"""
Живая форма для конфигуратора.
Показывает форму с контролами, но без возможности перемещения.
Поддерживает клики для выбора контролов.
"""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsProxyWidget, QLabel, QPushButton, QLineEdit,
    QCheckBox, QComboBox, QPlainTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen

from database import DatabaseService
from lang.local_translator import LocalTranslator


class LiveControlItem(QGraphicsProxyWidget):
    """Визуальное представление контрола на живой форме"""

    clicked = Signal(object)  # сигнал при клике на контрол

    def __init__(self, control_widget, control_id, control_type, control_alias, parent=None):
        super().__init__(parent)
        self.control_widget = control_widget
        self.control_id = control_id
        self.control_type = control_type
        self.control_alias = control_alias

        self.setWidget(control_widget)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

        # В режиме программирования — не перемещаем
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

        self._is_selected = False

    def set_selected_state(self, selected):
        """Устанавливает состояние выделения"""
        self._is_selected = selected
        if selected:
            self.setPen(QPen(QColor(0, 120, 215), 2))
        else:
            self.setPen(QPen(QColor(200, 200, 200), 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)
            self.scene().clearSelection()
            self.setSelected(True)
            self._is_selected = True
            self.setPen(QPen(QColor(0, 120, 215), 2))
        super().mousePressEvent(event)


class LiveFormScene(QGraphicsScene):
    """Сцена с живой формой"""

    control_selected = Signal(object)  # выбран контрол

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.setSceneRect(0, 0, 2000, 1500)

        self.form_background = None
        self.controls = {}  # {control_id: LiveControlItem}
        self.selected_control = None

    def set_form_background(self, width, height, title):
        """Устанавливает фон формы"""
        if self.form_background:
            self.removeItem(self.form_background)

        self.form_background = QGraphicsProxyWidget()
        background_widget = QWidget()
        background_widget.setStyleSheet(f"""
            background-color: #f5f5f5;
            border: 1px solid #aaa;
            border-radius: 5px;
        """)
        background_widget.resize(width, height)
        self.form_background.setWidget(background_widget)
        self.form_background.setPos(50, 50)
        self.form_background.setZValue(-1)
        self.addItem(self.form_background)

        # Заголовок формы
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-weight: bold;
            padding: 5px;
            background-color: #e0e0e0;
            border-bottom: 1px solid #aaa;
        """)
        title_label.resize(width, 30)
        title_label.move(50, 50)
        self.addWidget(title_label)

    def load_controls(self, controls_data):
        """Загружает контролы из данных"""
        self.clear_controls()

        form_pos = self.form_background.pos() if self.form_background else QPointF(50, 80)

        for data in controls_data:
            control_type = data.get('cclass', 'textbox')
            control_alias = data.get('calias', '')
            control_id = data.get('id')

            # Создаём виджет контрола
            control_widget = self._create_control_widget(control_type, control_alias, data.get('properties', {}))
            if not control_widget:
                continue

            # Устанавливаем позицию
            x = data.get('x', 10)
            y = data.get('y', 50)
            width = data.get('width', 150)
            height = data.get('height', 30)

            control_widget.resize(width, height)

            # Создаём графический элемент
            item = LiveControlItem(control_widget, control_id, control_type, control_alias)
            item.setPos(form_pos.x() + x, form_pos.y() + y)
            item.clicked.connect(self.on_control_clicked)

            self.addItem(item)
            self.controls[control_id] = item

    def _create_control_widget(self, control_type, alias, properties):
        """Создаёт виджет контрола по типу"""
        from controls import create_control
        try:
            widget = create_control(control_type, parent=None, db=self.db, alis=alias)
            if hasattr(widget, 'properties'):
                widget.properties = properties
            if hasattr(widget, 'apply_properties'):
                widget.apply_properties()
            return widget
        except Exception as e:
            print(f"Ошибка создания контрола {control_type}: {e}")
            return QLabel(f"[{control_type}]")

    def clear_controls(self):
        """Очищает все контролы"""
        for control_id, item in self.controls.items():
            self.removeItem(item)
        self.controls.clear()

    def on_control_clicked(self, control_item):
        """Обработка клика по контролу"""
        self.control_selected.emit(control_item)

    def clear_selection(self):
        """Снимает выделение со всех контролов"""
        for item in self.controls.values():
            item.set_selected_state(False)
        self.selected_control = None


class LiveFormView(QGraphicsView):
    """Вьюха для живой формы"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(Qt.ScrollHandDrag)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)


class LiveFormDesigner(QWidget):
    """Виджет живой формы для конфигуратора"""

    control_selected = Signal(object)

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()
        self.form_id = form_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = LiveFormScene(self, db=self.db)
        self.scene.control_selected.connect(self._on_control_selected)

        self.view = LiveFormView(self.scene)
        layout.addWidget(self.view)

        self.load_form()

    def set_form_id(self, form_id):
        """Устанавливает ID формы и загружает её"""
        self.form_id = form_id
        self.load_form()

    def load_form(self):
        """Загружает форму из БД"""
        if not self.form_id:
            return

        # Загружаем метаданные формы
        sql = "SELECT cname, calias, mstate_json FROM meta.forms WHERE id = %s"
        row = self.db.execute_query(sql, (self.form_id,))
        if not row:
            return

        form_name = row[0][0] or "Форма"
        mstate_json = row[0][2]

        # Парсим JSON
        form_data = {}
        if mstate_json:
            try:
                if isinstance(mstate_json, str):
                    form_data = json.loads(mstate_json)
                else:
                    form_data = mstate_json
            except:
                pass

        # Получаем геометрию
        width = form_data.get('geometry', {}).get('width', 800)
        height = form_data.get('geometry', {}).get('height', 600)

        # Устанавливаем фон формы
        self.scene.set_form_background(width, height, form_name)

        # Загружаем контролы
        controls_data = self._get_form_controls()
        self.scene.load_controls(controls_data)

    def _get_form_controls(self):
        """Загружает контролы формы из meta.form_elements"""
        if not self.form_id:
            return []

        sql = """
            SELECT id, calias, cclass, cdatasource, mproperties_json, isortorder
            FROM meta.form_elements
            WHERE formid = %s
            ORDER BY isortorder
        """
        rows = self.db.execute_query(sql, (self.form_id,))

        controls = []
        for row in rows:
            eid, calias, cclass, datasource, props_json, order = row

            props = {}
            if props_json:
                try:
                    props = json.loads(props_json)
                except:
                    pass

            controls.append({
                'id': str(eid),
                'calias': calias,
                'cclass': cclass,
                'cdatasource': datasource or '',
                'properties': props,
                'sortorder': order,
                'x': props.get('x', 10),
                'y': props.get('y', 50),
                'width': props.get('width', 150),
                'height': props.get('height', 30)
            })

        return controls

    def _on_control_selected(self, control_item):
        """Обработка выбора контрола"""
        self.control_selected.emit({
            'id': control_item.control_id,
            'alias': control_item.control_alias,
            'type': control_item.control_type,
            'widget': control_item.control_widget
        })

    def get_selected_control(self):
        """Возвращает выбранный контрол"""
        return self.scene.selected_control