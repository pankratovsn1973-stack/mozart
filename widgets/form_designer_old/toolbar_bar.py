# widgets/form_designer_old/toolbar_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ToolBarBar(QWidget):
    """Верхняя панель инструментов (Тулбар) формы конфигуратора над сценой."""

    save_clicked = Signal()
    cut_clicked = Signal()
    copy_clicked = Signal()
    paste_clicked = Signal()

    # Сигналы изменения назначения и метаданных формы
    form_role_changed = Signal(str)
    entity_changed = Signal(str)
    interface_changed = Signal(int)
    menu_item_changed = Signal(int)

    # Сигналы управления сеткой
    snap_toggled = Signal(bool)
    grid_toggled = Signal(bool)
    grid_size_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.db = getattr(parent, 'db', None)

        # Внутреннее состояние фиксации кнопок сетки
        self._is_snap_checked = False
        self._is_grid_checked = True

        self._setup_ui()

    def _setup_ui(self):
        # Нативный горизонтальный макет панели
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 1. БЛОК БАЗОВЫХ ДЕЙСТВИЙ С ФОРМОЙ
        self.btn_save = QPushButton("Сохранить", self)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        layout.addWidget(self.btn_save)

        self.btn_cut = QPushButton("Вырезать", self)
        self.btn_cut.clicked.connect(self.cut_clicked.emit)
        layout.addWidget(self.btn_cut)

        self.btn_copy = QPushButton("Копировать", self)
        self.btn_copy.clicked.connect(self.copy_clicked.emit)
        layout.addWidget(self.btn_copy)

        self.btn_paste = QPushButton("Вставить", self)
        self.btn_paste.clicked.connect(self.paste_clicked.emit)
        layout.addWidget(self.btn_paste)

        layout.addSpacing(10)

        # 2. КНОПКИ УПРАВЛЕНИЯ СЕТКОЙ И ПРИВЯЗКОЙ (СОЧНЫЕ ЦВЕТА И ТЕКСТ)
        self.btn_bind = QPushButton("Отвязано", self)
        self.btn_bind.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.btn_bind.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 3px; padding: 3px 10px;")
        self.btn_bind.clicked.connect(self._on_bind_clicked)
        layout.addWidget(self.btn_bind)

        self.btn_grid = QPushButton("Сетка: ВКЛ", self)
        self.btn_grid.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.btn_grid.setStyleSheet("background-color: #3498db; color: white; border-radius: 3px; padding: 3px 10px;")
        self.btn_grid.clicked.connect(self._on_grid_clicked)
        layout.addWidget(self.btn_grid)

        # Комбобокс выбора размера ячеек сетки
        self.grid_combo = QComboBox(self)
        self.grid_combo.addItems(["2", "5", "10", "15", "20", "25", "30"])
        self.grid_combo.setCurrentText("10")
        self.grid_combo.setFixedWidth(55)
        self.grid_combo.currentTextChanged.connect(self._on_grid_size_changed)
        layout.addWidget(self.grid_combo)

        layout.addSpacing(15)

        # 3. БЛОК ВЫБОРА НАЗНАЧЕНИЯ И РОЛИ ФОРМЫ
        layout.addWidget(QLabel("Назначение:"))
        self.role_combo = QComboBox(self)
        self.role_combo.addItem("Простая форма", "custom")
        self.role_combo.addItem("Главная для интерфейса", "main_route")
        self.role_combo.addItem("Таблица элементов сущности", "view")
        self.role_combo.addItem("Редактирование экземпляра сущности", "edit")
        self.role_combo.setFixedWidth(240)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        layout.addWidget(self.role_combo)

        # ДИНАМИЧЕСКИЙ БЛОК: Выбор бизнес-сущности (для view и edit)
        self.lbl_entity = QLabel("Сущность:")
        self.entity_combo = QComboBox(self)
        self.entity_combo.setFixedWidth(180)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        layout.addWidget(self.lbl_entity)
        layout.addWidget(self.entity_combo)

        # ДИНАМИЧЕСКИЙ БЛОК: Выбор интерфейсной роли (для main_route)
        self.lbl_interface = QLabel("Интерфейс:")
        self.interface_combo = QComboBox(self)
        self.interface_combo.setFixedWidth(140)
        self.interface_combo.currentIndexChanged.connect(self._on_interface_changed)
        layout.addWidget(self.lbl_interface)
        layout.addWidget(self.interface_combo)

        # КАСКАДНЫЙ ДИНАМИЧЕСКИЙ БЛОК: Выбор корневого меню интерфейса (для main_route)
        self.lbl_menu = QLabel("Пункт меню:")
        self.menu_combo = QComboBox(self)
        self.menu_combo.setFixedWidth(160)
        self.menu_combo.currentIndexChanged.connect(self._on_menu_item_changed)
        layout.addWidget(self.lbl_menu)
        layout.addWidget(self.menu_combo)

        # По умолчанию скрываем зависимые блоки метаданных (так как выбрана Простая форма)
        self._toggle_meta_visibility(entity=False, interface=False, menu=False)

        layout.addStretch()
    def set_db(self, db):
        """Принимает DatabaseService и запускает фоновое чтение метаданных Mozart."""
        self.db = db
        self._load_meta_from_db()

    def _toggle_meta_visibility(self, entity=False, interface=False, menu=False):
        """Управляет отображением зависимых блоков на панели инструментов."""
        self.lbl_entity.setVisible(entity)
        self.entity_combo.setVisible(entity)
        self.lbl_interface.setVisible(interface)
        self.interface_combo.setVisible(interface)
        self.lbl_menu.setVisible(menu)
        self.menu_combo.setVisible(menu)

    def _load_meta_from_db(self):
        if not self.db:
            return

        # 1. Читаем список бизнес-сущностей из meta.entitytypes
        try:
            self.entity_combo.clear()
            rows = self.db.execute_query("SELECT calias, cname FROM meta.entitytypes ORDER BY cname;")
            if rows:
                for row in rows:
                    self.entity_combo.addItem(str(row[1]), str(row[0]))
        except Exception as e:
            print(f"[ToolBarBar] Ошибка чтения meta.entitytypes: {e}")

        # 2. Читаем список интерфейсных ролей из auth.roles (где тип роли 'INTERFACE')
        try:
            self.interface_combo.clear()
            sql = """
                SELECT r.id, r.cname 
                FROM auth.roles r
                JOIN auth.role_types t ON r.role_type_id = t.id
                WHERE t.calias = 'INTERFACE'
                ORDER BY r.cname;
            """
            rows = self.db.execute_query(sql)
            if rows:
                for row in rows:
                    self.interface_combo.addItem(str(row[1]), int(row[0]))
        except Exception as e:
            print(f"[ToolBarBar] Ошибка чтения интерфейсных ролей: {e}")

    def _load_root_menus(self, role_id):
        """Вычисляет корневые пункты (parentid IS NULL) таблицы meta.menu для выбранной роли."""
        if not self.db or role_id is None:
            self.menu_combo.clear()
            return

        try:
            self.menu_combo.clear()
            sql = """
                SELECT id, cname 
                FROM meta.menu 
                WHERE roleid = %s AND parentid IS NULL AND lisactive = true
                ORDER BY isortorder, cname;
            """
            rows = self.db.execute_query(sql, (int(role_id),))
            if rows:
                for row in rows:
                    self.menu_combo.addItem(str(row[1]), int(row[0]))
            else:
                self.menu_combo.addItem("Нет корневых меню", None)
        except Exception as e:
            print(f"[ToolBarBar] Ошибка загрузки meta.menu: {e}")

    def _on_role_changed(self, index):
        """Слот смены Назначения: динамически перестраивает тулбар конфигуратора."""
        role_alias = self.role_combo.currentData()
        self.form_role_changed.emit(role_alias)

        if role_alias == "main_route":
            # Активируем Интерфейс и его Пункт меню, прячем блок сущностей
            self._toggle_meta_visibility(entity=False, interface=True, menu=True)
            self._on_interface_changed(self.interface_combo.currentIndex())
        elif role_alias in ("view", "edit"):
            # Активируем блок бизнес-сущностей, прячем остальное
            self._toggle_meta_visibility(entity=True, interface=False, menu=False)
        else:
            # Простая форма — все скрыто
            self._toggle_meta_visibility(entity=False, interface=False, menu=False)

    def _on_interface_changed(self, index):
        role_id = self.interface_combo.currentData()
        if role_id is not None:
            self.interface_changed.emit(int(role_id))
            # Каскадно подгружаем корневые меню meta.menu под выбранную роль
            self._load_root_menus(role_id)

    def _on_menu_item_changed(self, index):
        menu_id = self.menu_combo.currentData()
        if menu_id is not None:
            self.menu_item_changed.emit(int(menu_id))

    def _on_entity_changed(self, index):
        entity_alias = self.entity_combo.currentData()
        if entity_alias:
            self.entity_changed.emit(entity_alias)

    def _on_bind_clicked(self):
        """Инвертирует режим магнитной привязки и перекрашивает кнопку."""
        self._is_snap_checked = not self._is_snap_checked
        if self._is_snap_checked:
            self.btn_bind.setText("Привязано")
            self.btn_bind.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 3px; padding: 3px 10px;")
        else:
            self.btn_bind.setText("Отвязано")
            self.btn_bind.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 3px; padding: 3px 10px;")
        self.snap_toggled.emit(self._is_snap_checked)

    def _on_grid_clicked(self):
        """Инвертирует видимость сетки и перекрашивает кнопку."""
        self._is_grid_checked = not self._is_grid_checked
        if self._is_grid_checked:
            self.btn_grid.setText("Сетка: ВКЛ")
            self.btn_grid.setStyleSheet("background-color: #3498db; color: white; border-radius: 3px; padding: 3px 10px;")
        else:
            self.btn_grid.setText("Сетка: ВЫКЛ")
            self.btn_grid.setStyleSheet("background-color: #bdc3c7; color: white; border-radius: 3px; padding: 3px 10px;")
        self.grid_toggled.emit(self._is_grid_checked)

    def _on_grid_size_changed(self, text):
        if text.isdigit():
            self.grid_size_changed.emit(int(text))
