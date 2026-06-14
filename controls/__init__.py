# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/__init__.py

from PySide6.QtWidgets import QWidget

from .base_control import BaseControl
from .textbox import MozartTextBox
from .numberbox import MozartNumberBox
from .datebox import MozartDateBox
from .checkbox import MozartCheckBox
from .memo import MozartMemo
from .combobox import MozartComboBox
from .listbox import MozartListBox
from .optiongroup import MozartOptionGroup
from .image_view import MozartImageView
from .reference import MozartReference
from .grid import MozartGrid
from .container import MozartContainer
from .tab_container import MozartTabContainer
from .mozart_form import MozartForm
from .label import MozartLabel
from .button import MozartButton

# Алиасы
TextBox = MozartTextBox
NumberBox = MozartNumberBox
DateBox = MozartDateBox
CheckBox = MozartCheckBox
Memo = MozartMemo
ComboBox = MozartComboBox
ListBox = MozartListBox
OptionGroup = MozartOptionGroup
ImageView = MozartImageView
Reference = MozartReference
Grid = MozartGrid
Container = MozartContainer
TabContainer = MozartTabContainer
Form = MozartForm
Label = MozartLabel
Button = MozartButton


def create_control(control_type, parent=None, db=None, alis=None):
    """Фабрика создания контролов по строковому имени"""
    control_type = control_type.lower().strip()

    default_sizes = {
        'textbox': (150, 30),
        'numberbox': (150, 30),
        'datebox': (150, 30),
        'checkbox': (120, 30),
        'memo': (200, 80),
        'combobox': (150, 30),
        'listbox': (150, 100),
        'optiongroup': (150, 100),
        'imageview': (200, 150),
        'reference': (200, 30),
        'grid': (300, 150),
        'container': (200, 150),
        'group': (200, 150),
        'tabcontainer': (300, 200),
        'label': (150, 30),
        'button': (100, 30),
    }

    default_w, default_h = default_sizes.get(control_type, (150, 30))

    if control_type == 'textbox':
        widget = MozartTextBox(parent)
    elif control_type == 'numberbox':
        widget = MozartNumberBox(parent)
    elif control_type == 'datebox':
        widget = MozartDateBox(parent)
    elif control_type == 'checkbox':
        widget = MozartCheckBox(parent)
    elif control_type == 'memo':
        widget = MozartMemo(parent)
    elif control_type == 'combobox':
        widget = MozartComboBox(parent)
    elif control_type == 'listbox':
        widget = MozartListBox(parent)
    elif control_type == 'optiongroup':
        widget = MozartOptionGroup(parent)
    elif control_type == 'imageview':
        widget = MozartImageView(parent)
    elif control_type == 'reference':
        widget = MozartReference(parent)
        if db and hasattr(widget, 'set_db'):
            widget.set_db(db)
    elif control_type == 'grid':
        widget = MozartGrid(parent)
    elif control_type in ('container', 'group'):
        widget = MozartContainer(parent)
    elif control_type == 'tabcontainer':
        widget = MozartTabContainer(parent)
    elif control_type == 'label':
        widget = MozartLabel(parent)
    elif control_type == 'button':
        widget = MozartButton(parent)
    else:
        print(f"[Factory Warning] Запрошен неизвестный тип контрола: '{control_type}'. Создан базовый QWidget.")
        widget = QWidget(parent)

    widget.resize(default_w, default_h)

    # Передаём db контролам, которые поддерживают источники данных
    if db and hasattr(widget, 'set_db'):
        widget.set_db(db)

    if alis:
        widget.setObjectName(alis)
        if hasattr(widget, 'alis'):
            widget.alis = alis

    return widget


__all__ = [
    'BaseControl',
    'MozartTextBox', 'TextBox',
    'MozartNumberBox', 'NumberBox',
    'MozartDateBox', 'DateBox',
    'MozartCheckBox', 'CheckBox',
    'MozartMemo', 'Memo',
    'MozartComboBox', 'ComboBox',
    'MozartListBox', 'ListBox',
    'MozartOptionGroup', 'OptionGroup',
    'MozartImageView', 'ImageView',
    'MozartReference', 'Reference',
    'MozartGrid', 'Grid',
    'MozartContainer', 'Container',
    'MozartTabContainer', 'TabContainer',
    'MozartForm', 'Form',
    'MozartLabel', 'Label',
    'MozartButton', 'Button',
    'create_control'
]