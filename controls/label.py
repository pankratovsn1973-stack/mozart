# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/label.py

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Property, Qt

from .base_control import BaseControl


class MozartLabel(QLabel, BaseControl):
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        BaseControl.__init__(self)
        self._text = "Метка"
        self._text_alignment = "left"
        self._bold = False
        self._font_size = 9
        self._apply_style()
        self.setText(self._text)

    def _apply_style(self):
        if self._text_alignment == "left":
            self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif self._text_alignment == "center":
            self.setAlignment(Qt.AlignCenter)
        elif self._text_alignment == "right":
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = self.font()
        font.setBold(self._bold)
        if self._font_size > 0:
            font.setPointSize(self._font_size)
        self.setFont(font)

    def set_design_mode(self, design_mode):
        pass

    @Property(str)
    def text_alignment(self):
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, value):
        self._text_alignment = value
        self._apply_style()

    @Property(bool)
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value
        self._apply_style()

    @Property(int)
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value if value > 0 else 9
        self._apply_style()

    @property
    def properties(self):
        props = BaseControl.properties.fget(self)
        props.update({
            'label': self._text,
            'text_alignment': self._text_alignment,
            'bold': self._bold,
            'font_size': self._font_size,
        })
        return props

    @properties.setter
    def properties(self, value):
        if not value:
            return
        BaseControl.properties.fset(self, value)
        if 'label' in value:
            self._text = str(value['label'])
            self.setText(self._text)
        if 'text_alignment' in value:
            self._text_alignment = value['text_alignment']
        if 'bold' in value:
            self._bold = value['bold']
        if 'font_size' in value:
            self._font_size = value['font_size']
        self._apply_style()

    def set_value(self, value):
        text_val = str(value) if value is not None else ""
        self.setText(text_val)
        self._text = text_val
        self._original_value = text_val
        self._is_dirty = False

    def get_value(self):
        return self._text

    def reset(self):
        self.setText(self._original_value)
        self._text = self._original_value
        self._is_dirty = False