# widgets/form_designer_old/main_widget.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGraphicsView, QSplitter
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

from .form_scene import FormDesignerScene
from .property_editor import PropertyEditor
from .palette_widget import PaletteWidget
from .toolbar_bar import ToolBarBar


class FormDesigner(QWidget):
    """Главный виджет WYSIWYG-дизайнера форм Mozart ERP с верхним тулбаром метаданных."""

    def __init__(self, parent=None, db=None, form_id=None):
        super().__init__(parent)
        self.db = db
        self.form_id = form_id
        self.scene = None
        self.view = None
        self.toolbar_panel = None
        self.palette_panel = None
        self.property_panel = None
        self.runtime_form = None

        self.setup_ui()

    def setup_ui(self):
        # Главный вертикальный макет всего окна конфигуратора
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # РЯД 1 (ВЕРХНИЙ): Размещаем панель инструментов строго НАД сценой и палитрой
        self.toolbar_panel = ToolBarBar(self)
        # Передаем базу данных в тулбар для автоматической вычитки метаданных
        self.toolbar_panel.set_db(self.db)
        main_layout.addWidget(self.toolbar_panel)

        # РЯД 2: Разделитель для трех нижних секций (Палитра -> Холст -> Свойства)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # СЕКЦИЯ 1 (ЛЕВАЯ): Палитра доступных контролов
        self.palette_panel = PaletteWidget(self)
        splitter.addWidget(self.palette_panel)

        # СЕКЦИЯ 2 (ЦЕНТРАЛЬНАЯ): Холст сцены дизайнера
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.scene = FormDesignerScene(self)
        self.scene.set_db(self.db)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Разрешаем холсту принимать Drag-and-Drop элементы из палитры
        self.view.setAcceptDrops(True)
        canvas_layout.addWidget(self.view)

        splitter.addWidget(canvas_container)

        # СЕКЦИЯ 3 (ПРАВАЯ): Инспектор свойств PropertyEditor
        self.property_panel = PropertyEditor(self)
        splitter.addWidget(self.property_panel)

        # Задаем гармоничные пропорции распределения ширины
        splitter.setSizes([180, 750, 250])
        main_layout.addWidget(splitter)

        # Подключаем сигналы сетки и привязки
        self.toolbar_panel.snap_toggled.connect(self.scene.set_snap_enabled)
        self.toolbar_panel.grid_toggled.connect(self.scene.set_grid_visible)
        self.toolbar_panel.grid_size_changed.connect(self.scene.set_grid_size)

        # Коммутируем каскадные сигналы назначения формы к параметрам бланка
        self.toolbar_panel.form_role_changed.connect(self._on_form_role_changed)
        self.toolbar_panel.entity_changed.connect(self._on_form_entity_changed)
        self.toolbar_panel.interface_changed.connect(self._on_form_interface_changed)
        self.toolbar_panel.menu_item_changed.connect(self._on_form_menu_item_changed)

        # Подключаем сигналы ядра сцены к инспектору свойств
        self.scene.control_selected.connect(self._on_control_selected)
        self.scene.geometry_changed.connect(self._on_geometry_changed)

    def init_form(self, width, height, title):
        """Метод-мост для совместимости с FormPropertiesDialog."""
        return self.load_form_template(width, height, title)

    def load_form_template(self, width, height, title, controls_data=None):
        """Инициализирует чистый бланк формы или восстанавливает сохраненную из БД структуру."""
        self.runtime_form = self.scene.init_form(width, height, title)

        if controls_data:
            self.scene.load_controls(controls_data)

        self.property_panel.set_form(self)
        return self.runtime_form

    def _on_form_role_changed(self, role_alias):
        """Записывает выбранную роль (edit/view/custom/main_route) в параметры формы."""
        if self.runtime_form:
            setattr(self.runtime_form, 'form_role', role_alias)
            self.property_panel.set_form(self)

    def _on_form_entity_changed(self, entity_alias):
        """Связывает бланк формы с выбранной бизнес-сущностью Mozart ERP."""
        if self.runtime_form:
            self.runtime_form.entity_alias = entity_alias
            self.property_panel.set_form(self)

    def _on_form_interface_changed(self, interface_id):
        """Связывает форму с конкретным ID интерфейсной роли из auth.roles."""
        if self.runtime_form:
            setattr(self.runtime_form, 'interface_role_id', interface_id)
            self.property_panel.set_form(self)

    def _on_form_menu_item_changed(self, menu_id):
        """Связывает форму с выбранным первичным ключом (id) из meta.menu."""
        if self.runtime_form:
            setattr(self.runtime_form, 'target_menu_id', menu_id)
            self.property_panel.set_form(self)

    def _on_control_selected(self, control_item):
        """Слот фокуса элемента: переключает строки PropertyEditor."""
        self.property_panel.set_control(control_item)

    def _on_geometry_changed(self, control_id, x, y, width, height):
        """Слот онлайн-обновления геометрических ячеек инспектора во время движения мыши."""
        if hasattr(self, 'property_panel') and hasattr(self.property_panel, 'update_geometry_values'):
            self.property_panel.update_geometry_values(x, y, width, height)
