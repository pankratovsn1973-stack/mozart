# /home/sergey/Documents/configurate/widgets/form_designer_old/hierarchy_widget.py
# -*- coding: utf-8 -*-
# Дерево иерархии контролов формы

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from lang.local_translator import LocalTranslator


class HierarchyWidget(QWidget):
    """Дерево иерархии контролов формы"""

    item_selected = Signal(object)  # control_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.control_items = {}  # {control_id: tree_item}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок
        title = QLabel(self.translator.tr('hierarchy_title'))
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)

        # Дерево
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([self.translator.tr('hierarchy_column')])
        self.tree.setIndentation(20)
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.tree.setHeaderLabels([self.translator.tr('hierarchy_column')])

    def load_controls(self, controls_data):
        """Загружает иерархию контролов"""
        self.tree.clear()
        self.control_items = {}

        # Сначала создаём все элементы
        for data in controls_data:
            item = QTreeWidgetItem()
            item.setText(0, f"{data['cclass']}: {data['calias']}")
            item.setData(0, Qt.UserRole, data['id'])
            self.control_items[data['id']] = item

        # Затем строим иерархию
        for data in controls_data:
            item = self.control_items.get(data['id'])
            parent_id = data.get('parent_id')
            if parent_id and parent_id in self.control_items:
                self.control_items[parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def select_item(self, control_id):
        """Выделяет элемент в дереве"""
        if control_id in self.control_items:
            item = self.control_items[control_id]
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

    def on_item_clicked(self, item, column):
        """Обработка клика по элементу дерева"""
        control_id = item.data(0, Qt.UserRole)
        if control_id:
            self.item_selected.emit(control_id)

    def clear(self):
        """Очищает дерево"""
        self.tree.clear()
        self.control_items = {}

    def clear_selection(self):
        """Снимает выделение в дереве"""
        self.tree.setCurrentItem(None)