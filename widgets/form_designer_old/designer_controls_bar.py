# widgets/form_designer_old/designer_controls_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel
from PySide6.QtCore import Qt


class DesignerControlsBar(QWidget):
    """Верхняя панель инструментов дизайнера (Сетка, Привязка, Шаг сетки)."""

    def __init__(self, parent_designer, parent=None):
        super().__init__(parent)
        self.designer = parent_designer
        self.scene = parent_designer.scene
        self.view = parent_designer.view
        self.setup_ui()

    def setup_ui(self):
        # Основной лейаут панели инструментов
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)  # Внутренний шаг между кнопками одной группы

        # --- Группа 1: Управление сеткой и привязкой ---
        self.btn_grid = QPushButton("⊞ Сетка", self)
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.setFixedHeight(30)
        self.btn_grid.setMinimumWidth(80)
        self.btn_grid.clicked.connect(self._toggle_grid)

        self.btn_snap = QPushButton("🔗 Привязка", self)
        self.btn_snap.setCheckable(True)
        self.btn_snap.setChecked(True)
        self.btn_snap.setFixedHeight(30)
        self.btn_snap.setMinimumWidth(90)
        self.btn_snap.clicked.connect(self._toggle_snap)

        layout.addWidget(self.btn_grid)
        layout.addWidget(self.btn_snap)

        # --- Логическое разделение ---
        # 1. Отступ перед разделителем (24px)
        layout.addSpacing(24)

        # 2. Вертикальный разделитель (Line Separator)
        sep = QWidget(self)
        sep.setFixedWidth(1)      # 1px выглядит изящнее и современнее в ERP
        sep.setFixedHeight(24)    # Чуть меньше высоты кнопок для аккуратности
        sep.setStyleSheet("background-color: #dcdcdc; border: none;")
        layout.addWidget(sep)

        # 3. Отступ после разделителя (24px)
        layout.addSpacing(24)

        # --- Группа 2: Настройка шага сетки ---
        # Создаем компактный суб-лейаут для метки и комбобокса,
        # чтобы они были ближе друг к другу
        step_layout = QHBoxLayout()
        step_layout.setContentsMargins(0, 0, 0, 0)
        step_layout.setSpacing(6)  # Минимальный отступ между текстом и полем ввода

        self.lbl_grid_size = QLabel("Шаг сетки:", self)
        self.lbl_grid_size.setFixedHeight(30)

        self.cmb_grid_size = QComboBox(self)
        self.cmb_grid_size.addItems(["5", "10", "15", "20", "25", "30"])
        self.cmb_grid_size.setCurrentText("10")
        self.cmb_grid_size.setFixedWidth(80)
        self.cmb_grid_size.setFixedHeight(30)
        self.cmb_grid_size.currentTextChanged.connect(self._change_grid_size)

        step_layout.addWidget(self.lbl_grid_size)
        step_layout.addWidget(self.cmb_grid_size)

        # Добавляем подгруппу в главный лейаут
        layout.addLayout(step_layout)

        # Пружина, выталкивающая все элементы влево
        layout.addStretch()

        # Применяем настройки при старте
        self._apply_settings()

    def _toggle_grid(self, checked):
        """Включает/выключает сетку."""
        print(f"[Grid] Сетка: {checked}")
        if hasattr(self.scene, 'set_grid_visible'):
            self.scene.set_grid_visible(checked)

    def _toggle_snap(self, checked):
        """Включает/выключает привязку."""
        print(f"[Grid] Привязка: {checked}")
        if hasattr(self.scene, 'set_snap_enabled'):
            self.scene.set_snap_enabled(checked)

    def _change_grid_size(self, text):
        """Меняет размер клетки."""
        if text.isdigit():
            size = int(text)
            print(f"[Grid] Размер: {size}")
            if hasattr(self.scene, 'set_grid_size'):
                self.scene.set_grid_size(size)

    def _apply_settings(self):
        """Применяет настройки при инициализации."""
        size = int(self.cmb_grid_size.currentText())
        visible = self.btn_grid.isChecked()
        snap = self.btn_snap.isChecked()

        if hasattr(self.scene, 'set_grid_visible'):
            self.scene.set_grid_visible(visible)
        if hasattr(self.scene, 'set_grid_size'):
            self.scene.set_grid_size(size)
        if hasattr(self.scene, 'set_snap_enabled'):
            self.scene.set_snap_enabled(snap)