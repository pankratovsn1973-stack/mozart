# -*- coding: utf-8 -*-
# tabs/users_roles_tab.py

from PySide6.QtWidgets import QWidget, QTabWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt

from database import DatabaseService
from lang.local_translator import LocalTranslator
from .user_roles.users_tab import UsersTab
from .user_roles.roles_tab import RolesTab
from .user_roles.context_tab import ContextTab
from .user_roles.menu_manager import MenuManager


class UsersRolesTab(QWidget):
    """
    Вкладка "Пользователи и роли"
    Содержит три подвкладки: Пользователи, Роли, Контекст
    На подвкладке "Роли" правая панель с меню для выбранной роли
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.translator = LocalTranslator()

        # Основной TabWidget
        self.tabs = QTabWidget()

        # Вкладка 1: Пользователи
        self.users_tab = UsersTab(self, db=self.db)
        self.tabs.addTab(self.users_tab, self.translator.tr('tab_users'))

        # Вкладка 2: Роли (с разделённой панелью)
        self.roles_splitter = QSplitter(Qt.Horizontal)

        # Левая панель: дерево ролей
        self.roles_tab = RolesTab(self, db=self.db)
        self.roles_splitter.addWidget(self.roles_tab)

        # Правая панель: меню для выбранной роли
        self.menu_manager = MenuManager(self, db=self.db)
        self.roles_splitter.addWidget(self.menu_manager)

        # Устанавливаем соотношение размеров (левая панель уже, правая шире)
        self.roles_splitter.setSizes([300, 600])

        # Оборачиваем сплиттер в виджет для QTabWidget
        roles_container = QWidget()
        roles_layout = QVBoxLayout(roles_container)
        roles_layout.setContentsMargins(0, 0, 0, 0)
        roles_layout.addWidget(self.roles_splitter)

        self.tabs.addTab(roles_container, self.translator.tr('tab_roles'))

        # Подключаем сигнал выбора роли к загрузке меню
        self.roles_tab.role_selected.connect(self.menu_manager.set_role)

        # Вкладка 3: Контекст
        self.context_tab = ContextTab(self, db=self.db)
        self.tabs.addTab(self.context_tab, self.translator.tr('tab_context'))

        # Основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновляет заголовки вкладок при смене языка"""
        self.tabs.setTabText(0, self.translator.tr('tab_users'))
        self.tabs.setTabText(1, self.translator.tr('tab_roles'))
        self.tabs.setTabText(2, self.translator.tr('tab_context'))

        # Обновляем заголовки внутри вкладок
        if hasattr(self, 'users_tab'):
            self.users_tab.retranslate_ui()
        if hasattr(self, 'roles_tab'):
            self.roles_tab.retranslate_ui()
        if hasattr(self, 'context_tab'):
            self.context_tab.retranslate_ui()
        if hasattr(self, 'menu_manager'):
            self.menu_manager.retranslate_ui()