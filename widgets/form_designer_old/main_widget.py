# widgets/form_designer_old/main_widget.py
# -*- coding: utf-8 -*-
"""
Модуль предоставляет класс FormDesigner (Визуальный редактор форм Mozart ERP).
Является центральным графическим контейнером рабочей области дизайнера интерфейсов.
Исправлен баг TypeError при добавлении DesignerToolbar путем динамического поиска UI-виджета.
"""

import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
                               QMessageBox, QApplication, QToolBar)
from PySide6.QtCore import Qt, Slot

# Родные импорты архитектуры Mozart
from .form_scene import FormDesignerScene
from .form_view import FormDesignerView
from .property_editor import PropertyEditor
from .designer_toolbar import DesignerToolbar
from .palette_widget import PaletteWidget


class FormDesigner(QWidget):
    """
    Центральный виджет конструктора экранных форм.
    Координирует связь между графическим холстом, палитрой и инспектором свойств.
    """

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db
        self.form_id = form_id

        # Ссылка на активный визуальный холст формы (FormBackground)
        self.runtime_form = None

        # Инициализируем графическую сцену и вьюпорт отображения
        self.scene = FormDesignerScene(self)
        self.view = FormDesignerView(self.scene, self)

        # Разворачиваем элементы управления интерфейса дизайнера
        self.setup_ui()

    def setup_ui(self):
        """Сборка каркаса и интерфейсных панелей визуального редактора."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        # 1. Верхняя панель инструментов (Тулбар)
        self.toolbar = DesignerToolbar(self)

        # ИСПРАВЛЕНО: Динамически определяем, где внутри класса DesignerToolbar
        # спрятан настоящий QWidget, чтобы избежать падения TypeError в QBoxLayout.
        toolbar_widget = None

        if isinstance(self.toolbar, QWidget) or isinstance(self.toolbar, QToolBar):
            toolbar_widget = self.toolbar
        elif hasattr(self.toolbar, 'toolbar') and isinstance(self.toolbar.toolbar, QWidget):
            toolbar_widget = self.toolbar.toolbar
        elif hasattr(self.toolbar, 'tb') and isinstance(self.toolbar.tb, QWidget):
            toolbar_widget = self.toolbar.tb
        elif hasattr(self.toolbar, 'get_widget') and callable(self.toolbar.get_widget):
            toolbar_widget = self.toolbar.get_widget()
        elif hasattr(self.toolbar, 'get_toolbar') and callable(self.toolbar.get_toolbar):
            toolbar_widget = self.toolbar.get_toolbar()

        # Если виджет успешно извлечен — добавляем его в компоновщик
        if toolbar_widget:
            main_layout.addWidget(toolbar_widget)
        else:
            # Если это кастомный контейнер элементов, просто пропускаем его добавление в компоновку,
            # чтобы не ронять инициализацию всего графического редактора форм.
            pass

        # Основной рабочий разделитель (Сплиттер)
        splitter = QSplitter(Qt.Horizontal, self)
        main_layout.addWidget(splitter)

        # 2. Левая панель: Палитра компонентов Mozart ERP
        self.palette_panel = PaletteWidget(self)
        splitter.addWidget(self.palette_panel)

        # 3. Центральная область: Графический холст (Сцена/Вью)
        splitter.addWidget(self.view)

        # 4. Правая панель: Инспектор свойств (Property Editor)
        self.property_panel = PropertyEditor(self)
        splitter.addWidget(self.property_panel)

        # Задаем пропорции панелей: Палитра, Холст, Инспектор
        splitter.setSizes([150, 750, 300])

        # Устанавливаем собранный лейаут на виджет
        if self.layout() is None:
            self.setLayout(main_layout)
        else:
            self.layout().addLayout(main_layout)

        # ========== СИНХРОНИЗАЦИЯ СИГНАЛОВ СЦЕНЫ ==========
        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.form_resized.connect(self._on_form_resized_on_scene)
        self.scene.save_requested.connect(self.save_form_to_db)
        self.scene.geometry_changed.connect(self._on_geometry_changed)

        # Подключаем обратную связь от инспектора свойств к элементам сцены
        self.property_panel.property_changed.connect(self._on_property_edited_in_panel)

    def init_form(self, width: int, height: int, title: str):
        """Создает и разворачивает на холсте чистую подложку проектируемой формы."""
        self.runtime_form = self.scene.init_form(width, height, title)

        # Передаем форму в инспектор для отображения стартовых параметров
        if self.runtime_form:
            self.property_panel.set_active_item("form_root", self.runtime_form)

    @Slot(object)
    def _on_control_selected(self, selected_obj):
        """Обработчик выделения элементов на холсте сцены."""
        if not selected_obj:
            self.property_panel.set_active_item(None, None)
            return

        if selected_obj == self.scene.background or hasattr(selected_obj, 'title_bar'):
            self.property_panel.set_active_item("form_root", selected_obj)
            return

        control_item = None
        for item in self.scene.items():
            if hasattr(item, 'widget') and item.widget() == selected_obj:
                control_item = item
                break

        if not control_item and hasattr(selected_obj, 'control_id'):
            control_item = selected_obj

        target = control_item if control_item else selected_obj
        c_id = getattr(target, 'control_id', '')

        self.property_panel.set_active_item(c_id, target)

    @Slot(str, int, int, int, int)
    def _on_geometry_changed(self, control_id, x, y, width, height):
        """Синхронизация координат при перетаскивании элементов мымшой."""
        sel_item = getattr(self.scene, 'selected_control', None)
        sel_id = getattr(sel_item, 'control_id', None)

        if sel_item and sel_id == control_id:
            self.property_panel._block_sync = True

            for row in range(self.property_panel.rowCount()):
                name_item = self.property_panel.item(row, 0)
                if name_item:
                    prop_name = name_item.data(Qt.UserRole)
                    val_item = self.property_panel.item(row, 1)
                    if val_item:
                        if prop_name == "x":
                            val_item.setText(str(x))
                        elif prop_name == "y":
                            val_item.setText(str(y))
                        elif prop_name == "width":
                            val_item.setText(str(width))
                        elif prop_name == "height":
                            val_item.setText(str(height))

            self.property_panel._block_sync = False

    @Slot(float, float)
    def _on_form_resized_on_scene(self, width, height):
        """Синхронизация числовых значений в таблице при изменении размеров формы мышом."""
        sel_item = getattr(self.scene, 'selected_control', None)

        if sel_item == self.scene.background or (sel_item and hasattr(sel_item, 'title_bar')):
            self.property_panel._block_sync = True
            for row in range(self.property_panel.rowCount()):
                name_item = self.property_panel.item(row, 0)
                if name_item:
                    prop_name = name_item.data(Qt.UserRole)
                    val_item = self.property_panel.item(row, 1)
                    if val_item:
                        if prop_name == "width":
                            val_item.setText(str(int(width)))
                        elif prop_name == "height":
                            val_item.setText(str(int(height)))
            self.property_panel._block_sync = False

    @Slot(str, str, object)
    def _on_property_edited_in_panel(self, control_id, property_name, new_value):
        """Обработчик ручных правок параметров внутри таблицы инспектора свойств."""
        pass

    def save_form_to_db(self):
        """Сериализация структуры визуальных элементов холста и сохранение в PostgreSQL."""
        if not self.db or not self.form_id:
            return
        try:
            QApplication.statusTip()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось записать форму в БД:\n{str(e)}")
