# widgets/form_designer_old/designer_bottom_bar.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt


class DesignerBottomBar(QWidget):
    """Нижняя панель действий с формой (Сохранить, Загрузить, Очистить)."""

    def __init__(self, parent_designer, parent=None):
        super().__init__(parent)
        self.designer = parent_designer
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Кнопка "Сохранить"
        self.btn_save = QPushButton("💾 Сохранить", self)
        self.btn_save.setFixedHeight(30)
        self.btn_save.setMinimumWidth(100)
        self.btn_save.clicked.connect(self.designer.save_form_to_db)
        layout.addWidget(self.btn_save)

        # Кнопка "Загрузить"
        self.btn_load = QPushButton("📂 Загрузить", self)
        self.btn_load.setFixedHeight(30)
        self.btn_load.setMinimumWidth(100)
        self.btn_load.clicked.connect(self.designer.load_form)
        layout.addWidget(self.btn_load)

        # Кнопка "Очистить"
        self.btn_clear = QPushButton("🗑 Очистить", self)
        self.btn_clear.setFixedHeight(30)
        self.btn_clear.setMinimumWidth(100)
        self.btn_clear.clicked.connect(self.designer.clear_form)
        layout.addWidget(self.btn_clear)

        layout.addStretch()

        # Кнопка "Закрыть" (опционально)
        self.btn_close = QPushButton("✖ Закрыть", self)
        self.btn_close.setFixedHeight(30)
        self.btn_close.setMinimumWidth(80)
        self.btn_close.clicked.connect(self.designer.close)
        layout.addWidget(self.btn_close)