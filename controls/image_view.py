# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/image_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout
from PySide6.QtCore import Property, Qt
from PySide6.QtGui import QPixmap

from .base_control import BaseControl


class MozartImageView(QWidget, BaseControl):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        BaseControl.__init__(self)
        self._label = ""
        self._value = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(150)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        layout.addWidget(self.image_label)
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Выбрать файл...")
        self.btn_select.clicked.connect(self.select_file)
        btn_layout.addWidget(self.btn_select)
        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_image)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

    def select_file(self):
        if self._is_readonly:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                   "Images (*.png *.jpg *.jpeg *.svg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.set_image(pixmap)
                self._value = file_path
                self._is_dirty = True

    def clear_image(self):
        if self._is_readonly:
            return
        self.image_label.clear()
        self._value = None
        self._is_dirty = True

    def set_image(self, pixmap):
        scaled = pixmap.scaled(
            self.image_label.width() - 10,
            self.image_label.height() - 10,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def set_design_mode(self, design_mode):
        self.btn_select.setEnabled(not design_mode)
        self.btn_clear.setEnabled(not design_mode)

    @Property(str)
    def binding_field(self):
        return self._binding_field

    @binding_field.setter
    def binding_field(self, value):
        self._binding_field = value

    @Property(str)
    def entity_alias(self):
        return self._entity_alias

    @entity_alias.setter
    def entity_alias(self, value):
        self._entity_alias = value

    @Property(bool)
    def is_required(self):
        return self._is_required

    @is_required.setter
    def is_required(self, value):
        self._is_required = value

    @Property(bool)
    def is_readonly(self):
        return self._is_readonly

    @is_readonly.setter
    def is_readonly(self, value):
        self._is_readonly = value
        self.btn_select.setEnabled(not value)
        self.btn_clear.setEnabled(not value)

    @property
    def alis(self):
        return self.objectName()

    @alis.setter
    def alis(self, value):
        self.setObjectName(value)

    @property
    def properties(self):
        props = BaseControl.properties.fget(self)
        props.update({'label': self._label})
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'label' in value:
            self._label = value['label']

    def set_value(self, value):
        self._original_value = value
        self._value = value
        self._is_dirty = False
        if value and isinstance(value, str):
            pixmap = QPixmap(value)
            if not pixmap.isNull():
                self.set_image(pixmap)
                return
        self.image_label.clear()

    def get_value(self):
        return self._value

    def is_dirty(self):
        return self._is_dirty

    def reset(self):
        self.set_value(self._original_value)