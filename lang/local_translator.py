# lang/local_translator.py
import sqlite3
import threading
import os
import sys

class LocalTranslator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        project_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        lang_dir = os.path.join(project_dir, 'lang_data')
        os.makedirs(lang_dir, exist_ok=True)
        self.db_path = os.path.join(lang_dir, 'lang.db')
        self._init_db()
        self.current_language = 'ru'
        self._initialized = True

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                label_key TEXT NOT NULL,
                language TEXT NOT NULL,
                translation TEXT NOT NULL,
                PRIMARY KEY (label_key, language)
            )
        ''')
        cur.execute("SELECT COUNT(*) FROM translations WHERE language='en'")
        if cur.fetchone()[0] == 0:
            self._load_fallback(conn)
        conn.commit()
        conn.close()

    def _get_fallback(self):
        return {
            'ru': {
                'window_title_main': 'MOZART ERP - Конфигуратор',
                'menu_file': '&Файл',
                'menu_language': '&Язык',
                'menu_help': '&Помощь',
                'action_new_project': 'Новый проект...',
                'action_open_project': 'Открыть проект...',
                'action_save_project': 'Сохранить параметры',
                'action_exit': 'Выход',
                'action_about': 'О программе',
                'group_project_file': 'Файл проекта',
                'group_db_connection': 'Подключение к базе данных',
                'group_db_work': 'Работа с БД',
                'group_server': 'Сервер приложений',
                'group_client': 'Клиент',
                'btn_open_project': 'Открыть проект...',
                'btn_new_project': 'Новый проект...',
                'btn_save_project': 'Сохранить параметры',
                'btn_connect': 'Подключиться',
                'btn_db_work': 'Работа с БД',
                'btn_start_server': 'Запустить сервер',
                'btn_stop_server': 'Остановить сервер',
                'btn_start_client': 'Запустить клиент',
                'btn_close': 'Закрыть',
                'btn_add': 'Добавить',
                'btn_edit': 'Редактировать',
                'btn_delete': 'Удалить',
                'btn_ok': 'ОК',
                'btn_cancel': 'Отмена',
                'status_ready': 'Готов. Откройте или создайте проект.',
                'status_connected': 'Подключение к БД успешно',
                'status_disconnected': 'Не подключено',
                'field_host': 'Хост',
                'field_port': 'Порт',
                'field_db': 'База данных',
                'field_user': 'Пользователь',
                'field_password': 'Пароль',
                'field_name': 'Имя',
                'field_alias': 'Алиас',
                'field_id': 'ID',
                'field_active': 'Активна',
                'error': 'Ошибка',
                'info': 'Информация',
                'warning': 'Предупреждение',
                'error_loading': 'Ошибка загрузки',
                'dialog_open_project': 'Открыть проект',
                'dialog_save_project': 'Сохранить проект',
                'status_new_project': 'Новый проект создан. Заполните параметры БД и подключитесь.',
                'status_project_loaded': 'Проект загружен:',
                'status_project_saved': 'Проект сохранён:',
                'title_edit_balance_unit': 'Редактирование балансовой единицы',
                'label_is_balance_unit': 'Является балансовой единицей',
                'field_parent': 'Родитель',
                'tab_as_parent': 'Как родитель',
                'tab_as_child': 'Как ребёнок',
                'field_detail': 'Деталь',
                'field_master': 'Мастер',
                'field_role': 'Роль',
                'field_link_field': 'Поле связи',
                'field_order': 'Порядок',
                'title_add_visibility': 'Добавить видимость БЕ',
                'field_balance_unit': 'Балансовая единица',
                'field_policy': 'Политика',
                'policy_individual': 'Индивидуальная',
                'policy_all_visible': 'Все видны',
                'policy_all_hidden': 'Все скрыты',
                'error_visibility_exists': 'Такая запись уже существует',
                'warning_select_entity': 'Выберите сущность',
                'warning_select_field': 'Выберите поле',
                'error_prod_field_delete': 'Поля в продуктивном статусе нельзя удалить',
                'confirm_delete_fields': 'Удалить выбранные поля (%d шт.)?',
                'confirm_delete_records': 'Удалить выбранные записи (%d шт.)?',
                'tab_users': 'Пользователи',
                'tab_roles': 'Роли',
                'tab_context': 'Контекст',
                'tab_users_roles': 'Пользователи и роли',
                'title_user_edit': 'Редактирование пользователя',
                'title_role_edit': 'Редактирование роли',
                'title_context_assign': 'Назначение контекста',
                'field_login': 'Логин',
                'field_password_hash': 'Хеш пароля',
                'field_person_instance': 'Экземпляр персоны',
                'label_active': 'Активен',
                'label_interface_role': 'Интерфейсная роль',
                'field_parent_role': 'Родительская роль',
                'field_interface_path': 'Путь к интерфейсу',
                'field_comment': 'Комментарий',
                'field_user': 'Пользователь',
                'field_balance_unit': 'Балансовая единица',
                'warning_select_user': 'Выберите пользователя',
                'warning_select_role': 'Выберите роль',
                'warning_select_context': 'Выберите запись контекста',
                'warning_context_required': 'Необходимо наличие пользователей, ролей и БЕ',
                'confirm_delete': 'Подтверждение удаления',
                'confirm_delete_user': 'Удалить пользователя?',
                'confirm_delete_role': 'Удалить роль?',
                'confirm_delete_context': 'Удалить контекст?',
                'field_interface': 'Интерфейсная',
                'warning_select_record': 'Выберите запись',
                # Новые ключи для entities и вкладок
                'entity_types': 'Типы сущностей',
                'title_entity_type_edit': 'Редактирование типа сущности',
                'field_system_name': 'Системное имя',
                'field_description': 'Описание',
                'field_entity_class': 'Класс сущности',
                'field_baseclass_legacy': 'Базовый класс (устар.)',
                'label_dependent': 'Зависимая',
                'label_hierarchical': 'Иерархическая',
                'label_versioned': 'Версионная',
                'field_security_strategy': 'Стратегия безопасности',
                'field_status': 'Статус',
                'tab_fields': 'Поля',
                'tab_bu_visibility': 'Видимость БЕ',
                'tab_composition': 'Подчинённые таблицы',
                'tab_routes': 'Маршруты',
                'field_type': 'Тип',
                'field_decimals': 'Точность',
                'field_index': 'Индекс',
                'field_ref_type': 'Ссылка на тип',
                'routes_in_development': 'Раздел в разработке: маршруты для документов',
                'warning_select_record': 'Выберите запись',
                'title_add_composition': 'Добавить подчинённую таблицу',
                'title_edit_composition': 'Редактировать связь',
                'info_add_as_child_not_supported': 'Добавление как ребёнка не поддерживается (создаётся в родителе)',
                'error_composition_exists': 'Такая связь уже существует',
                'confirm_rename_title': 'Подтверждение переименования',
                'confirm_rename_message': 'Изменение системного имени с \'{0}\' на \'{1}\' переименует таблицу расширения. Продолжить?',
                'info_table_renamed': 'Таблица ext.{0} успешно переименована в ext.{1}',
                'error_rename_table': 'Не удалось переименовать таблицу: {0}',
                'warning_table_not_found': 'Таблица ext.{0} не найдена, переименование не требуется',
                'error_rename_prod': 'Нельзя изменить системное имя для сущности в продуктивном статусе',
                'error_prod_entity_delete': 'Сущности в продуктивном статусе нельзя удалить: {0}',
                'confirm_delete_entities': 'Удалить выбранные сущности (%d шт.)?',
                'error_save_field': 'Ошибка сохранения поля: '
            },
            'en': {
                'window_title_main': 'MOZART ERP - Configurator',
                'menu_file': '&File',
                'menu_language': '&Language',
                'menu_help': '&Help',
                'action_new_project': 'New Project...',
                'action_open_project': 'Open Project...',
                'action_save_project': 'Save Settings',
                'action_exit': 'Exit',
                'action_about': 'About',
                'group_project_file': 'Project File',
                'group_db_connection': 'Database Connection',
                'group_db_work': 'Database Work',
                'group_server': 'Application Server',
                'group_client': 'Client',
                'btn_open_project': 'Open Project...',
                'btn_new_project': 'New Project...',
                'btn_save_project': 'Save Settings',
                'btn_connect': 'Connect',
                'btn_db_work': 'Database Work',
                'btn_start_server': 'Start Server',
                'btn_stop_server': 'Stop Server',
                'btn_start_client': 'Start Client',
                'btn_close': 'Close',
                'btn_add': 'Add',
                'btn_edit': 'Edit',
                'btn_delete': 'Delete',
                'btn_ok': 'OK',
                'btn_cancel': 'Cancel',
                'status_ready': 'Ready. Open or create a project.',
                'status_connected': 'Database connection successful',
                'status_disconnected': 'Not connected',
                'field_host': 'Host',
                'warning_select_record': 'Select a record',
                'field_port': 'Port',
                'field_db': 'Database',
                'field_user': 'User',
                'field_password': 'Password',
                'field_name': 'Name',
                'field_alias': 'Alias',
                'field_id': 'ID',
                'field_active': 'Active',
                'error': 'Error',
                'info': 'Information',
                'warning': 'Warning',
                'error_loading': 'Loading error',
                'dialog_open_project': 'Open Project',
                'dialog_save_project': 'Save Project',
                'status_new_project': 'New project created. Fill in database parameters and connect.',
                'status_project_loaded': 'Project loaded:',
                'status_project_saved': 'Project saved:',
                'title_edit_balance_unit': 'Edit Balance Unit',
                'label_is_balance_unit': 'Is balance unit',
                'field_parent': 'Parent',
                'tab_users': 'Users',
                'tab_roles': 'Roles',
                'tab_context': 'Context',
                'tab_users_roles': 'Users & Roles',
                'title_user_edit': 'Edit User',
                'title_role_edit': 'Edit Role',
                'title_context_assign': 'Assign Context',
                'field_login': 'Login',
                'field_password_hash': 'Password hash',
                'field_person_instance': 'Person instance',
                'label_active': 'Active',
                'label_interface_role': 'Interface role',
                'field_parent_role': 'Parent role',
                'field_interface_path': 'Interface path',
                'field_comment': 'Comment',
                'field_user': 'User',
                'field_role': 'Role',
                'field_balance_unit': 'Balance unit',
                'warning_select_user': 'Select a user',
                'warning_select_role': 'Select a role',
                'warning_select_context': 'Select a context entry',
                'warning_context_required': 'Users, roles and balance units are required',
                'confirm_delete': 'Confirm deletion',
                'confirm_delete_user': 'Delete user?',
                'confirm_delete_role': 'Delete role?',
                'confirm_delete_context': 'Delete context?',
                'field_interface': 'Interface',
                'tab_as_parent': 'As parent',
                'tab_as_child': 'As child',
                'field_detail': 'Detail',
                'field_master': 'Master',
                'field_role': 'Role',
                'field_link_field': 'Link field',
                'field_order': 'Order',
                'title_add_visibility': 'Add BU visibility',
                'field_policy': 'Policy',
                'policy_individual': 'Individual',
                'policy_all_visible': 'All visible',
                'policy_all_hidden': 'All hidden',
                'error_visibility_exists': 'Record already exists',
                'warning_select_entity': 'Select entity',
                'warning_select_field': 'Select field',
                'error_prod_field_delete': 'Fields in PROD status cannot be deleted',
                'confirm_delete_fields': 'Delete selected fields (%d items)?',
                'confirm_delete_records': 'Delete selected records (%d items)?',
                # New keys for entities and tabs
                'entity_types': 'Entity Types',
                'title_entity_type_edit': 'Edit Entity Type',
                'field_system_name': 'System name',
                'field_description': 'Description',
                'field_entity_class': 'Entity class',
                'field_baseclass_legacy': 'Base class (legacy)',
                'label_dependent': 'Dependent',
                'label_hierarchical': 'Hierarchical',
                'label_versioned': 'Versioned',
                'field_security_strategy': 'Security strategy',
                'field_status': 'Status',
                'tab_fields': 'Fields',
                'tab_bu_visibility': 'BU Visibility',
                'tab_composition': 'Subordinate tables',
                'tab_routes': 'Routes',
                'field_type': 'Type',
                'field_decimals': 'Decimals',
                'field_index': 'Index',
                'field_ref_type': 'Ref type',
                'routes_in_development': 'Section under development: document routes',
                'warning_select_record': 'Select a record',
                'title_add_composition': 'Add subordinate table',
                'title_edit_composition': 'Edit composition',
                'info_add_as_child_not_supported': 'Adding as child is not supported (create in parent)',
                'error_composition_exists': 'Such composition already exists',
                'confirm_rename_title': 'Confirm rename',
                'confirm_rename_message': 'Changing system name from \'{0}\' to \'{1}\' will rename the extension table. Continue?',
                'info_table_renamed': 'Table ext.{0} successfully renamed to ext.{1}',
                'error_rename_table': 'Failed to rename table: {0}',
                'warning_table_not_found': 'Table ext.{0} not found, rename not required',
                'error_rename_prod': 'Cannot change system name for entity in PROD status',
                'error_prod_entity_delete': 'Entities in PROD status cannot be deleted: {0}',
                'confirm_delete_entities': 'Delete selected entities (%d items)?',
                'error_save_field': 'Error saving field: '
            }
        }

    def _load_fallback(self, conn):
        cur = conn.cursor()
        for lang, data in self._get_fallback().items():
            for key, text in data.items():
                cur.execute("INSERT OR IGNORE INTO translations (label_key, language, translation) VALUES (?, ?, ?)",
                            (key, lang, text))
        conn.commit()

    def set_language(self, lang_code):
        self.current_language = lang_code

    def tr(self, key):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT translation FROM translations WHERE label_key=? AND language=?", (key, self.current_language))
        row = cur.fetchone()
        if row:
            conn.close()
            return row[0]
        cur.execute("SELECT translation FROM translations WHERE label_key=? AND language='en'", (key,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else key

    def sync_from_postgres(self, db_service):
        rows = db_service.execute_query("SELECT label_key, language, translation FROM lang.translations")
        if not rows:
            return
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        for key, lang, text in rows:
            cur.execute("INSERT OR REPLACE INTO translations (label_key, language, translation) VALUES (?, ?, ?)",
                        (key, lang, text))
        conn.commit()
        conn.close()