# Полный путь: tabs/entity_classes_tab.py
# -*- coding: utf-8 -*-
"""
Вкладка управления классами ERP в конфигураторе.
Содержит дерево классов слева и панель инструментов с кнопками CRUD.
При двойном клике открывает диалог редактирования класса.
Наследуется от BaseTab для единой работы с БД и переводами.
Использует ClassDataService для работы с данными.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

from tabs.base_tab import BaseTab
from services.class_data_service import ClassDataService
from dialogs.base_class_selector import BaseClassSelectorDialog
from dialogs.class_edit_dialog import ClassEditDialog
from crud_buttons import CrudButtons
from lang.local_translator import LocalTranslator


class EntityClassesTab(BaseTab):
    """
    Вкладка управления классами.

    Свойства:
        - class_service: ClassDataService - сервис классов
        - current_version_id: int - ID выбранной версии
        - tree: QTreeWidget - дерево классов
        - crud: CrudButtons - кнопки CRUD

    Методы:
        - setup_ui() - настройка интерфейса
        - load_classes() - загрузка классов
        - add_class() - добавление класса
        - edit_class() - редактирование класса
        - delete_class() - удаление класса
        - on_item_selected() - обработка выбора элемента
        - refresh() - обновление данных
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.class_service = ClassDataService(db)
        self.current_version_id = None

        # Используем существующий layout от BaseTab
        # НЕ СОЗДАЕМ НОВЫЙ layout!
        self.setup_ui()
        self.load_classes()

    def setup_ui(self):
        """Настройка интерфейса вкладки."""
        # Используем layout от BaseTab (self.layout)
        # Очищаем его перед добавлением новых виджетов
        self.clear_layout()

        # CRUD кнопки
        self.crud = CrudButtons(self)
        self.crud.add_clicked.connect(self.add_class)
        self.crud.edit_clicked.connect(self.edit_class)
        self.crud.delete_clicked.connect(self.delete_class)
        self.layout.addWidget(self.crud)

        # Дерево классов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_class_name'),
            self.translator.tr('field_base_class'),
            self.translator.tr('field_type'),
            self.translator.tr('field_visible')
        ])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 150)
        self.tree.setColumnWidth(3, 80)
        self.tree.setColumnWidth(4, 70)
        self.tree.header().setStretchLastSection(False)

        self.tree.itemDoubleClicked.connect(self.edit_class)
        self.tree.itemSelectionChanged.connect(self.on_item_selected)
        self.layout.addWidget(self.tree)

    def clear_layout(self):
        """Очистка layout от всех виджетов."""
        if self.layout:
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def load_classes(self):
        """Загрузка классов в дерево."""
        self.tree.clear()

        if not self.class_service:
            return

        # Получаем данные
        classes = self.class_service.get_classes_tree()

        # Строим дерево
        items = {}
        root_items = []

        for cls in classes:
            class_id = cls.get('class_id')
            version_id = cls.get('version_id')
            c_name = cls.get('c_name', '')
            c_base_class = cls.get('c_base_class', '')
            c_base_source = cls.get('c_base_source', '')
            is_visible = cls.get('is_visible', True)
            parent_id = cls.get('i_parent_id')
            level = cls.get('level', 1)

            # Создаем элемент
            item = QTreeWidgetItem([
                str(version_id),
                c_name,
                c_base_class or '---',
                c_base_source,
                self.translator.tr('yes') if is_visible else self.translator.tr('no')
            ])
            item.setData(0, Qt.UserRole, version_id)
            item.setData(0, Qt.UserRole + 1, class_id)

            # Сохраняем
            items[version_id] = item

            # Определяем родителя
            if parent_id is None or parent_id not in items:
                root_items.append(item)
            else:
                items[parent_id].addChild(item)

        # Добавляем корневые элементы
        for item in root_items:
            self.tree.addTopLevelItem(item)

        # Расширяем все узлы
        self.tree.expandAll()

    def add_class(self):
        """Добавление нового класса."""
        # Открываем диалог выбора базового класса
        selector = BaseClassSelectorDialog(self, db=self.db)
        if selector.exec_() == BaseClassSelectorDialog.Accepted:
            base_version_id = selector.get_selected_version_id()

            # Открываем редактор с mode='add'
            editor = ClassEditDialog(
                self,
                db=self.db,
                version_id=-1,
                mode='add'
            )

            # Передаем информацию о базовом классе
            if base_version_id > 0:
                base_data = self.class_service.get_class_version(base_version_id)
                if base_data:
                    editor.class_name = f"New_{base_data['version']['c_name']}"

            if editor.exec_() == ClassEditDialog.Accepted:
                self.load_classes()

    def edit_class(self):
        """Редактирование выбранного класса."""
        if self.current_version_id is None or self.current_version_id <= 0:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_select_class')
            )
            return

        # Открываем редактор
        editor = ClassEditDialog(
            self,
            db=self.db,
            version_id=self.current_version_id,
            mode='edit'
        )

        if editor.exec_() == ClassEditDialog.Accepted:
            self.load_classes()

    def delete_class(self):
        """Удаление выбранного класса."""
        if self.current_version_id is None or self.current_version_id <= 0:
            QMessageBox.warning(
                self,
                self.translator.tr('warning'),
                self.translator.tr('warning_select_class')
            )
            return

        if QMessageBox.question(
                self,
                self.translator.tr('confirm_delete'),
                self.translator.tr('confirm_delete_class'),
                QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            # Мягкое удаление
            self.class_service.soft_delete_class_version(self.current_version_id)
            self.load_classes()
            self.current_version_id = None

    def on_item_selected(self):
        """Обработка выбора элемента в дереве."""
        current = self.tree.currentItem()
        if current:
            self.current_version_id = current.data(0, Qt.UserRole)
        else:
            self.current_version_id = None

    def refresh(self):
        """Обновление данных."""
        self.load_classes()

    def retranslate_ui(self):
        """Обновление переводов."""
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_class_name'),
            self.translator.tr('field_base_class'),
            self.translator.tr('field_type'),
            self.translator.tr('field_visible')
        ])
        if hasattr(self, 'crud'):
            self.crud.retranslate_ui()