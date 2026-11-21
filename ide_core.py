# Полный путь: ide_core.py
# -*- coding: utf-8 -*-

import psycopg2
import json
import os
from core.bridge_function_registry import BridgeFunctionRegistry
from core.bridge_functions_builtin import register_builtin_bridges

class GoProject:
    """Глобальный синглтон управления параметрами и машинами ядра платформы Mozart ERP."""

    def __init__(self):
        # Базовые параметры подключения (Layer 1)
        self.db_host = "localhost"
        self.db_port = "5432"
        self.db_name = "mozart_erp"
        self.db_user = "postgres"
        self.db_pass = ""
        self.db_conn = None  # Сюда записывается строго физическое соединение psycopg2.connection
        self.current_user_id = None

        # Системное время "Машины времени"
        from PySide6.QtCore import QDateTime
        self.system_date = QDateTime.currentDateTime()

        # Инициализация Машины Классов при старте
        from core.class_registry import ClassRegistry
        self.class_registry = ClassRegistry()

        # Инициализация Менеджера Мостов Свойств (Запускается один раз при старте)
        from core.property_bridge_manager import PropertyBridgeManager
        self.property_bridge_manager = PropertyBridgeManager()

        # Библиотека простых ERP-методов трансляции
        from core.superlibre import SuperLibre
        from core.bridge_resolver import BridgeResolver
        self.superlibre = SuperLibre()
        self.bridge_resolver = BridgeResolver(self)

        # Реестр функций трансляции low-code свойств
        self.bridge_functions = BridgeFunctionRegistry()
        register_builtin_bridges(self.bridge_functions)

        # Средний слой (Layer 2)
        self.l2_path = os.getcwd() + "/layer2_server"
        self.l2_port = 8000
        self.l2_process = None

        # 🚀 ДИАГНОСТИКА: печатаем системную дату сессии при старте
        print(f"[GO_PROJECT] Session Date: {self.system_date.toString('yyyy-MM-dd HH:mm:ss')}")

    def set_db_service(self, db_service):
        """Передает инициализированный сервис базы данных в Машины ядра и греет кэш мостов."""
        self.class_registry.db = db_service

        self.property_bridge_manager.db = db_service
        self.property_bridge_manager.init_and_warm_cache()

    def p_Connect(self):
        """
        Установка физического соединения с PostgreSQL.
        Проверяет, что пользователь имеет роль конфигуратора.
        """
        try:
            if self.db_conn:
                try:
                    self.db_conn.close()
                except:
                    pass

            self.db_conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass,
                connect_timeout=5
            )
            self.db_conn.autocommit = True

            with self.db_conn.cursor() as cur:
                cur.execute("SELECT id FROM auth.users WHERE clogin = %s", (self.db_user,))
                row = cur.fetchone()
                if not row:
                    self.db_conn.close()
                    self.db_conn = None
                    return False, f"Пользователь {self.db_user} не найден в системе."

                user_id = row[0]

                cur.execute("""
                    SELECT u.id 
                    FROM auth.users u
                    JOIN auth.userrolecontext urc ON u.id = urc.userid
                    JOIN auth.roles r ON urc.roleid = r.id
                    JOIN auth.role_types rt ON r.role_type_id = rt.id
                    WHERE u.id = %s AND rt.calias = 'CONFIG'
                """, (user_id,))
                if not cur.fetchone():
                    self.db_conn.close()
                    self.db_conn = None
                    return False, "У вас нет прав конфигуратора. Доступ запрещён."

            self.current_user_id = user_id
            return True, "Соединение со Слоном установлено успешно. Добро пожаловать, конфигуратор!"
        except Exception as e:
            self.db_conn = None
            return False, f"Ошибка подключения: {str(e)}"

    def f_Execute(self, sql, params=None):
        """Выполнение SQL-запроса (SELECT). Возвращает коллекцию строк."""
        if not self.db_conn:
            return []

        try:
            with self.db_conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return cur.fetchall()
                return []
        except Exception as e:
            print(f"SQL Error: {e}")
            return []

    def p_SaveProject(self, file_path):
        """ Сохранение манифеста проекта в .mzt файл (JSON) """
        data = {
            "db": {
                "host": self.db_host, "port": self.db_port,
                "name": self.db_name, "user": self.db_user, "pass": self.db_pass
            },
            "l2": {"path": self.l2_path, "port": self.l2_port}
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def p_LoadProject(self, file_path):
        """ Загрузка параметров проекта из .mzt файла """
        if not os.path.exists(file_path):
            return False, "Файл проекта не найден."

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.db_host = data['db'].get('host', 'localhost')
            self.db_port = data['db'].get('port', '5432')
            self.db_name = data['db'].get('name', '')
            self.db_user = data['db'].get('user', 'postgres')
            self.db_pass = data['db'].get('pass', '')

            self.l2_path = data['l2'].get('path', '')
            self.l2_port = data['l2'].get('port', 8000)

            return True, "Проект загружен."
        except Exception as e:
            return False, f"Ошибка чтения файла: {str(e)}"


# Создаем единственный экземпляр объекта управления проектом
goProject = GoProject()