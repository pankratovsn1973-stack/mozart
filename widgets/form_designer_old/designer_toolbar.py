# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/designer_toolbar.py

from PySide6.QtWidgets import QHBoxLayout, QPushButton
from PySide6.QtCore import Signal


class DesignerToolbar(QHBoxLayout):
    save_clicked = Signal()
    load_clicked = Signal()
    clear_clicked = Signal()
    grid_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.addWidget(self.btn_save)

        self.btn_load = QPushButton("Загрузить")
        self.btn_load.clicked.connect(self.load_clicked.emit)
        self.addWidget(self.btn_load)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_clicked.emit)
        self.addWidget(self.btn_clear)

        self.btn_grid = QPushButton("⊞ Сетка")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.clicked.connect(lambda: self.grid_toggled.emit(self.btn_grid.isChecked()))
        self.addWidget(self.btn_grid)

        self.addStretch()

    def retranslate(self, tr):
        self.btn_save.setText(tr('btn_save') or "Сохранить")
        self.btn_load.setText(tr('btn_load') or "Загрузить")
        self.btn_clear.setText(tr('btn_clear') or "Очистить")

    def is_grid_checked(self):
        return self.btn_grid.isChecked()