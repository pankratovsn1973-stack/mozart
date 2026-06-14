# /home/sergey/Documents/configurate/widgets/form_designer_old/main_widget.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget, QHBoxLayout, QPushButton, QComboBox, QLabel, \
    QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize

from .form_scene import FormDesignerScene
from .form_view import FormDesignerView
from .palette_widget import PaletteWidget
from .property_editor import PropertyEditor
from .methods_panel import MethodsPanel
from .events_panel import EventsPanel
from .code_editor import CodeEditorDialog

# Подключаем абстрактный класс формы через общий пакет
from controls import MozartForm as Form


class FormDesigner(QWidget):
    """Главный виджет визуального дизайнера форм платформы Mozart"""

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db
        self.form_id = form_id
        self.calc_code = ""

        self.runtime_form = Form(parent=None)
        if hasattr(self.runtime_form, 'set_data_bridge') and self.db:
            self.runtime_form.set_data_bridge(self.db)

        self.setup_ui()
        self.init_form()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель с кнопками управления сеткой
        toolbar_layout = QHBoxLayout()

        self.btn_grid = QPushButton("⊞ Сетка")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.clicked.connect(self.toggle_grid)
        toolbar_layout.addWidget(self.btn_grid)

        self.btn_snap = QPushButton("⚡ Привязка")
        self.btn_snap.setCheckable(True)
        self.btn_snap.setChecked(True)
        self.btn_snap.clicked.connect(self.toggle_snap)
        toolbar_layout.addWidget(self.btn_snap)

        toolbar_layout.addWidget(QLabel("Размер сетки:"))
        self.combo_grid_size = QComboBox()
        self.combo_grid_size.addItems(["5 px", "10 px", "15 px", "20 px", "25 px", "50 px"])
        self.combo_grid_size.setCurrentText("10 px")
        self.combo_grid_size.currentTextChanged.connect(self.change_grid_size)
        toolbar_layout.addWidget(self.combo_grid_size)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        self.splitter = QSplitter(Qt.Horizontal, self)

        self.palette = PaletteWidget(self)
        self.splitter.addWidget(self.palette)

        self.scene = FormDesignerScene(self)
        self.view = FormDesignerView(self.scene)
        self.splitter.addWidget(self.view)

        right_tabs = QTabWidget()

        # --- СНЯТИЕ БЛОКИРОВКИ СПЛИТТЕРА В СТАРОЙ ВЕРСИИ ---
        right_tabs.setMinimumWidth(10)
        right_tabs.minimumSizeHint = lambda: QSize(10, 10)
        right_tabs.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        # ----------------------------------------------------

        self.property_panel = PropertyEditor(self)
        self.property_panel.property_changed.connect(self._on_property_edited_in_panel)
        right_tabs.addTab(self.property_panel, "Свойства")

        self.methods_panel = MethodsPanel(self)
        self.methods_panel.edit_method_requested.connect(self._edit_method)
        self.methods_panel.add_method_requested.connect(self._add_method)
        right_tabs.addTab(self.methods_panel, "Методы")

        self.events_panel = EventsPanel(self)
        right_tabs.addTab(self.events_panel, "События")

        self.splitter.addWidget(right_tabs)

        # Разрешаем сжимать все панели, включая правые табы
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, True)
        self.splitter.setCollapsible(2, True)



        layout.addWidget(self.splitter)

        # Начальные пропорции макета
        self.splitter.setSizes([150, 600, 250])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)  # сцена забирает всё свободное пространство
        self.splitter.setStretchFactor(2, 0)

        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.form_resized.connect(self._on_form_resized_on_scene)
        self.scene.save_requested.connect(self.save_form_to_db)
        self.scene.geometry_changed.connect(self._on_geometry_changed)

        self.setFocusPolicy(Qt.StrongFocus)
    def toggle_grid(self):
        self.scene.set_grid_visible(self.btn_grid.isChecked())

    def toggle_snap(self):
        self.scene.set_snap_enabled(self.btn_snap.isChecked())

    def change_grid_size(self, text):
        size = int(text.split()[0])
        self.scene.set_grid_size(size)

    def init_form(self, width=800, height=600, title="Форма"):
        """Порождает бланк формы и линкует его с бизнес-объектом Form"""
        bg = self.scene.init_form(width, height, title)

        self.runtime_form.title = title
        self.runtime_form.form_id = self.form_id
        self.runtime_form.form_type = 'edit'  # Default
        self.runtime_form.interface_role = ''

        self.runtime_form._design_background = bg
        bg._runtime_form = self.runtime_form

        self.property_panel.set_form(self.runtime_form)
        self.methods_panel.set_control(self.runtime_form, self.calc_code)
        self.methods_panel.setEnabled(True)

        title_bar_height = bg.title_bar.get_height() if hasattr(bg, 'title_bar') and bg.title_bar else 32
        self.view.centerOn(0, title_bar_height / 2)
        self.view.reset_zoom()

        self.splitter.updateGeometry()
        self.view.updateGeometry()
        self.palette.updateGeometry()

        # Асинхронно форсируем применение размеров сплиттера после рендеринга таблиц
        QTimer.singleShot(50, lambda: self.splitter.setSizes([150, 600, 250]))

    def _on_control_selected(self, control_item):
        """Срабатывает при клике на контрол и пробрасывает все свойства в правую панель"""
        if control_item:
            self.property_panel.set_control(control_item)
            self.methods_panel.set_control(control_item, self.calc_code)
            self.events_panel.set_control(control_item)
        else:
            self.property_panel.set_form(self.runtime_form)
            self.methods_panel.set_control(self.runtime_form, self.calc_code)
            self.methods_panel.setEnabled(True)
            self.events_panel.setEnabled(False)

    def _on_form_resized_on_scene(self, width, height):
        if getattr(self.property_panel, 'current_object_type', None) == 'form':
            if hasattr(self.property_panel, 'load_properties'):
                self.property_panel.load_properties()

    def _on_geometry_changed(self, control_id, x, y, width, height):
        """Обновляет панель свойств при изменении геометрии мышкой"""
        if self.scene.selected_control and self.scene.selected_control.control_id == control_id:
            if hasattr(self.property_panel, 'update_geometry_values'):
                self.property_panel.update_geometry_values(x, y, width, height)

    def _on_property_edited_in_panel(self, prop_name, value):
        """Применяет изменения из таблицы инспектора свойств к реальному контролу или бизнес-форме"""
        selected_item = self.scene.selected_control

        if not selected_item:
            if hasattr(self.runtime_form, prop_name):
                setattr(self.runtime_form, prop_name, value)

            if hasattr(self.runtime_form, 'properties') and isinstance(self.runtime_form.properties, dict):
                self.runtime_form.properties[prop_name] = value

            bg = getattr(self.runtime_form, '_design_background', None)
            if bg:
                if prop_name == "title" and hasattr(bg, 'set_title'):
                    bg.set_title(str(value))
                elif prop_name == "width" and hasattr(bg, 'set_size'):
                    bg.set_size(int(value), bg.height)
                elif prop_name == "height" and hasattr(bg, 'set_size'):
                    bg.set_size(bg.width, int(value))
                elif prop_name == "form_type":
                    bg.form_type = value
                    bg.update_layout()
                elif prop_name == "interface_role":
                    bg.interface_role = value
                    bg.update_layout()

                if hasattr(self.scene, 'update_resize_handles_position'):
                    self.scene.update_resize_handles_position()
                self.scene.update()
            return

        control_widget = selected_item.control_widget

        if prop_name in ("objectName", "calias", "alis"):
            control_widget.setObjectName(str(value))
        elif prop_name == "width":
            control_widget.resize(int(value), control_widget.height())
            selected_item.setGeometry(0, 0, int(value), control_widget.height())
        elif prop_name == "height":
            control_widget.resize(control_widget.width(), int(value))
            selected_item.setGeometry(0, 0, control_widget.width(), int(value))
        elif prop_name == "x":
            selected_item.setPos(int(value), selected_item.pos().y())
        elif prop_name == "y":
            selected_item.setPos(selected_item.pos().x(), int(value))
        else:
            if hasattr(control_widget, prop_name):
                setattr(control_widget, prop_name, value)
            if hasattr(control_widget, 'properties') and isinstance(control_widget.properties, dict):
                control_widget.properties[prop_name] = value

        if hasattr(selected_item, '_emit_geometry'):
            selected_item._emit_geometry()
        self.scene.update()

    def get_form_data(self):
        """
        Возвращает сериализованные метаданные самой формы и её контролов.
        Используется внешними диалогами (например, form_properties_dialog.py) для сохранения.
        """
        # Безопасно считываем текущие размеры с бланка формы на сцене
        bg = getattr(self.runtime_form, '_design_background', None)
        width = bg.width if bg else 800
        height = bg.height if bg else 600

        form_state = {
            "width": width,
            "height": height,
            "title": getattr(self.runtime_form, 'title', 'Форма'),
            "background_color": getattr(self.runtime_form, 'background_color', '#f0f0f0'),
            "resizable": getattr(self.runtime_form, 'resizable', True),
            "form_type": getattr(self.runtime_form, 'form_type', 'edit'),
            "interface_role": getattr(self.runtime_form, 'interface_role', '')
        }

        # Получаем данные обо всех элементах управления на сцене
        controls_list = []
        if hasattr(self.scene, 'get_controls_data'):
            controls_list = self.scene.get_controls_data() or []

        return {
            "form": form_state,
            "controls": controls_list,
            "form_id": self.form_id
        }

    def _edit_method(self, method_name, code):
        dialog = CodeEditorDialog(self, title=f"Редактирование метода {method_name}", code=code)
        if dialog.exec():
            new_code = dialog.get_code()
            self.calc_code = new_code
            if hasattr(self.methods_panel, 'update_method_code'):
                self.methods_panel.update_method_code(method_name, new_code)

    def _add_method(self):
        pass

    def save_form_to_db(self):
        pass
