# Полный путь: services/class_data_service.py
"""
Сервис для работы с метаданными классов ERP.
Использует единый экземпляр DatabaseService, переданный извне.
Реализует CRUD для классов, версий, методов и сигналов.
Обеспечивает получение иерархического дерева классов для отображения.
Не создает новых подключений к БД.
"""

from typing import List, Dict, Optional, Any
from database import DatabaseService


class ClassDataService:
    """
    Сервис для работы с данными классов в схеме class_erp.

    Свойства:
        - db: DatabaseService - экземпляр сервиса БД (передается в конструкторе)

    Методы:
        - get_classes_tree() -> List[Dict] - получение иерархического дерева классов
        - get_class_version(version_id) -> Optional[Dict] - получение версии класса с полными данными
        - create_class_version(data) -> int - создание новой версии класса
        - update_class_version(version_id, data) -> bool - обновление версии класса
        - soft_delete_class_version(version_id) -> bool - мягкое удаление версии класса
        - get_class_methods(version_id) -> List[Dict] - получение методов класса
        - add_method_to_class(version_id, method_data) -> int - добавление метода к классу
        - remove_method_from_class(version_id, method_id) -> bool - удаление метода из класса
        - get_class_signals(version_id) -> List[Dict] - получение сигналов класса
        - assign_signal_method(signal_id, method_id) -> bool - привязка метода к сигналу
        - get_all_methods() -> List[Dict] - получение всех доступных методов
        - get_available_base_classes() -> List[Dict] - получение классов для выбора в качестве базового
    """

    def __init__(self, db: DatabaseService):
        """
        Конструктор сервиса.

        Вход:
            db: DatabaseService - единый экземпляр сервиса БД из ide_db_work.py

        Выход: None
        """
        self.db = db

    def get_classes_tree(self) -> List[Dict]:
        """
        Получение иерархического дерева классов с активными версиями.

        Вход: Нет

        Выход:
            List[Dict] - список словарей с полями:
                - class_id: int - ID класса из mozartclasses
                - c_name: str - имя класса
                - version_id: int - ID версии
                - is_visible: bool - визуальный/невизуальный
                - c_base_class: str - имя базового класса
                - c_base_source: str - 'PYTHON' или 'ERP'
                - i_parent_id: Optional[int] - ID родительской версии
                - level: int - уровень вложенности
                - root_class_id: int - ID корневого класса
        """
        sql = """
        WITH RECURSIVE class_tree AS (
            SELECT 
                mc.id as class_id,
                mc.c_name,
                cv.id as version_id,
                cv.is_visible,
                cv.c_base_class,
                cv.c_base_source,
                cv.i_parent_id,
                1 as level,
                mc.id as root_class_id
            FROM class_erp.mozartclasses mc
            JOIN class_erp.class_version cv ON mc.id = cv.id_mozart_class
            WHERE cv.dt_end IS NULL AND cv.i_parent_id IS NULL

            UNION ALL

            SELECT 
                mc.id,
                mc.c_name,
                cv.id,
                cv.is_visible,
                cv.c_base_class,
                cv.c_base_source,
                cv.i_parent_id,
                ct.level + 1,
                ct.root_class_id
            FROM class_tree ct
            JOIN class_erp.class_version cv ON cv.i_parent_id = ct.version_id
            JOIN class_erp.mozartclasses mc ON mc.id = cv.id_mozart_class
            WHERE cv.dt_end IS NULL
        )
        SELECT * FROM class_tree ORDER BY root_class_id, level, c_name;
        """
        result = self.db.execute_query(sql)

        # Преобразуем кортежи в словари
        if not result:
            return []

        # Определяем структуру результата
        columns = ['class_id', 'c_name', 'version_id', 'is_visible',
                   'c_base_class', 'c_base_source', 'i_parent_id', 'level', 'root_class_id']

        return [dict(zip(columns, row)) for row in result]

    def get_class_version(self, version_id: int) -> Optional[Dict]:
        """
        Получение полных данных версии класса.

        Вход:
            version_id: int - ID версии класса

        Выход:
            Optional[Dict] - словарь с полями:
                - version: dict - данные версии
                - properties: List[dict] - список свойств
                - methods: List[dict] - список методов
                - signals: List[dict] - список сигналов
            или None, если версия не найдена
        """
        # 1. Загружаем основную версию
        sql_version = """
        SELECT mc.id as class_id, mc.c_name, cv.*
        FROM class_erp.class_version cv
        JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
        WHERE cv.id = %s AND cv.dt_end IS NULL
        """
        version_rows = self.db.execute_query(sql_version, (version_id,))

        if not version_rows:
            return None

        # Преобразуем в словарь
        version = {
            'id': version_rows[0][2],  # cv.id
            'class_id': version_rows[0][0],  # mc.id
            'c_name': version_rows[0][1],  # mc.c_name
            'is_visible': version_rows[0][3],
            'c_base_class': version_rows[0][4],
            'c_base_source': version_rows[0][5],
            'i_base_class': version_rows[0][6],
            'i_parent_id': version_rows[0][7],
            'txt_properties': version_rows[0][8],
            'dt_start': version_rows[0][9],
            'dt_end': version_rows[0][10]
        }

        # 2. Загружаем свойства
        sql_properties = """
        SELECT id, c_name, type, mask, source, dt_start, dt_end
        FROM class_erp.class_version_properties
        WHERE id_class_version = %s AND dt_end IS NULL
        ORDER BY id
        """
        properties = self.db.execute_query(sql_properties, (version_id,))
        properties_list = []
        for row in properties:
            properties_list.append({
                'id': row[0],
                'c_name': row[1],
                'type': row[2],
                'mask': row[3],
                'source': row[4],
                'dt_start': row[5],
                'dt_end': row[6]
            })

        # 3. Загружаем методы
        sql_methods = """
        SELECT m.id, m.c_name, mv.id as method_version_id, mv.txt_method, 
               mv.c_komment, mv.dt_start, mv.dt_end
        FROM class_erp.method_class_relation mcr
        JOIN class_erp.method m ON mcr.id_method = m.id
        JOIN class_erp.method_version mv ON m.id = mv.id_method
        WHERE mcr.id_class_version = %s 
          AND mcr.dt_end IS NULL 
          AND mv.dt_end IS NULL
        ORDER BY m.c_name
        """
        methods = self.db.execute_query(sql_methods, (version_id,))
        methods_list = []
        for row in methods:
            methods_list.append({
                'id': row[0],
                'c_name': row[1],
                'method_version_id': row[2],
                'txt_method': row[3],
                'c_komment': row[4],
                'dt_start': row[5],
                'dt_end': row[6]
            })

        # 4. Загружаем сигналы
        sql_signals = """
        SELECT s.id, s.c_signal, m.id as method_id, m.c_name as method_name
        FROM class_erp.signal s
        LEFT JOIN class_erp.method m ON s.id_method = m.id
        WHERE s.id_class_version = %s AND s.dt_end IS NULL
        ORDER BY s.c_signal
        """
        signals = self.db.execute_query(sql_signals, (version_id,))
        signals_list = []
        for row in signals:
            signals_list.append({
                'id': row[0],
                'c_signal': row[1],
                'method_id': row[2],
                'method_name': row[3]
            })

        return {
            'version': version,
            'properties': properties_list,
            'methods': methods_list,
            'signals': signals_list
        }

    def create_class_version(self, data: Dict) -> int:
        """
        Создание новой версии класса.

        Вход:
            data: Dict - словарь с полями:
                - c_name: str - имя класса (обязательно)
                - c_base_class: str - имя базового класса
                - c_base_source: str - 'PYTHON' или 'ERP'
                - i_base_class: Optional[int] - ID родительской версии
                - i_parent_id: Optional[int] - ID родительского класса (для составных)
                - is_visible: bool - визуальный/невизуальный
                - txt_properties: str - свойства в формате JSON

        Выход:
            int - ID созданной версии класса
        """
        # 1. Создаем запись в mozartclasses
        sql_class = """
        INSERT INTO class_erp.mozartclasses (c_name)
        VALUES (%s)
        RETURNING id
        """
        class_result = self.db.execute_query(sql_class, (data.get('c_name'),))
        class_id = class_result[0][0] if class_result else None

        if not class_id:
            raise ValueError("Не удалось создать класс")

        # 2. Создаем запись в class_version
        sql_version = """
        INSERT INTO class_erp.class_version 
        (id_mozart_class, c_base_class, c_base_source, 
         i_base_class, i_parent_id, is_visible, txt_properties)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        version_result = self.db.execute_query(sql_version, (
            class_id,
            data.get('c_base_class', ''),
            data.get('c_base_source', 'ERP'),
            data.get('i_base_class'),
            data.get('i_parent_id'),
            data.get('is_visible', True),
            data.get('txt_properties', '{}')
        ))

        if not version_result:
            raise ValueError("Не удалось создать версию класса")

        return version_result[0][0]

    def update_class_version(self, version_id: int, data: Dict) -> bool:
        """
        Обновление данных версии класса.

        Вход:
            version_id: int - ID версии класса
            data: Dict - обновляемые данные

        Выход:
            bool - True если обновление выполнено, иначе False
        """
        sql = """
        UPDATE class_erp.class_version 
        SET c_base_class = %s, 
            c_base_source = %s, 
            i_base_class = %s, 
            i_parent_id = %s, 
            is_visible = %s, 
            txt_properties = %s
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (
            data.get('c_base_class', ''),
            data.get('c_base_source', 'ERP'),
            data.get('i_base_class'),
            data.get('i_parent_id'),
            data.get('is_visible', True),
            data.get('txt_properties', '{}'),
            version_id
        ), fetch=False)
        return True

    def soft_delete_class_version(self, version_id: int) -> bool:
        """
        Мягкое удаление версии класса (установка dt_end = NOW()).

        Вход:
            version_id: int - ID версии класса

        Выход:
            bool - True если удаление выполнено, иначе False
        """
        sql = """
        UPDATE class_erp.class_version 
        SET dt_end = NOW() 
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (version_id,), fetch=False)
        return True

    def get_class_methods(self, version_id: int) -> List[Dict]:
        """
        Получение списка методов, связанных с версией класса.

        Вход:
            version_id: int - ID версии класса

        Выход:
            List[Dict] - список методов с полями:
                - id: int - ID метода
                - c_name: str - имя метода
                - method_version_id: int - ID версии метода
                - txt_method: str - код метода
                - c_komment: str - комментарий
        """
        sql = """
        SELECT m.id, m.c_name, mv.id as method_version_id, mv.txt_method, mv.c_komment
        FROM class_erp.method_class_relation mcr
        JOIN class_erp.method m ON mcr.id_method = m.id
        JOIN class_erp.method_version mv ON m.id = mv.id_method
        WHERE mcr.id_class_version = %s 
          AND mcr.dt_end IS NULL 
          AND mv.dt_end IS NULL
        ORDER BY m.c_name
        """
        result = self.db.execute_query(sql, (version_id,))

        methods = []
        for row in result:
            methods.append({
                'id': row[0],
                'c_name': row[1],
                'method_version_id': row[2],
                'txt_method': row[3],
                'c_komment': row[4]
            })

        return methods

    def add_method_to_class(self, version_id: int, method_data: Dict) -> int:
        """
        Добавление метода к классу.

        Вход:
            version_id: int - ID версии класса
            method_data: Dict - данные метода:
                - c_name: str - имя метода
                - c_komment: str - комментарий
                - txt_method: str - код метода

        Выход:
            int - ID созданного метода
        """
        # 1. Создаем метод
        sql_method = """
        INSERT INTO class_erp.method (c_name)
        VALUES (%s)
        RETURNING id
        """
        method_result = self.db.execute_query(sql_method, (method_data.get('c_name'),))
        method_id = method_result[0][0] if method_result else None

        if not method_id:
            raise ValueError("Не удалось создать метод")

        # 2. Создаем версию метода
        sql_version = """
        INSERT INTO class_erp.method_version (id_method, c_komment, txt_method)
        VALUES (%s, %s, %s)
        """
        self.db.execute_query(sql_version, (
            method_id,
            method_data.get('c_komment', ''),
            method_data.get('txt_method', '')
        ), fetch=False)

        # 3. Связываем с классом
        sql_relation = """
        INSERT INTO class_erp.method_class_relation (id_method, id_class_version)
        VALUES (%s, %s)
        """
        self.db.execute_query(sql_relation, (method_id, version_id), fetch=False)

        return method_id

    def remove_method_from_class(self, version_id: int, method_id: int) -> bool:
        """
        Удаление метода из класса (мягкое удаление связи).

        Вход:
            version_id: int - ID версии класса
            method_id: int - ID метода

        Выход:
            bool - True если удаление выполнено, иначе False
        """
        sql = """
        UPDATE class_erp.method_class_relation 
        SET dt_end = NOW() 
        WHERE id_method = %s AND id_class_version = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (method_id, version_id), fetch=False)
        return True

    def get_class_signals(self, version_id: int) -> List[Dict]:
        """
        Получение списка сигналов класса.

        Вход:
            version_id: int - ID версии класса

        Выход:
            List[Dict] - список сигналов с полями:
                - id: int - ID сигнала
                - c_signal: str - имя сигнала
                - method_id: Optional[int] - ID привязанного метода
                - method_name: Optional[str] - имя привязанного метода
        """
        sql = """
        SELECT s.id, s.c_signal, m.id as method_id, m.c_name as method_name
        FROM class_erp.signal s
        LEFT JOIN class_erp.method m ON s.id_method = m.id
        WHERE s.id_class_version = %s AND s.dt_end IS NULL
        ORDER BY s.c_signal
        """
        result = self.db.execute_query(sql, (version_id,))

        signals = []
        for row in result:
            signals.append({
                'id': row[0],
                'c_signal': row[1],
                'method_id': row[2],
                'method_name': row[3]
            })

        return signals

    def assign_signal_method(self, signal_id: int, method_id: Optional[int]) -> bool:
        """
        Привязка метода к сигналу.

        Вход:
            signal_id: int - ID сигнала
            method_id: Optional[int] - ID метода (None для отвязки)

        Выход:
            bool - True если привязка выполнена, иначе False
        """
        sql = """
        UPDATE class_erp.signal 
        SET id_method = %s 
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (method_id, signal_id), fetch=False)
        return True

    def get_all_methods(self) -> List[Dict]:
        """
        Получение списка всех доступных методов.

        Вход: Нет

        Выход:
            List[Dict] - список методов с полями:
                - id: int - ID метода
                - c_name: str - имя метода
        """
        sql = """
        SELECT id, c_name 
        FROM class_erp.method 
        WHERE dt_end IS NULL 
        ORDER BY c_name
        """
        result = self.db.execute_query(sql)

        methods = []
        for row in result:
            methods.append({
                'id': row[0],
                'c_name': row[1]
            })

        return methods

    def get_available_base_classes(self) -> List[Dict]:
        """
        Получение списка классов, доступных для выбора в качестве базовых.

        Вход: Нет

        Выход:
            List[Dict] - список классов с полями:
                - class_id: int - ID класса
                - c_name: str - имя класса
                - version_id: int - ID версии
                - c_base_source: str - 'PYTHON' или 'ERP'
        """
        sql = """
        SELECT mc.id as class_id, mc.c_name, cv.id as version_id, cv.c_base_source
        FROM class_erp.mozartclasses mc
        JOIN class_erp.class_version cv ON mc.id = cv.id_mozart_class
        WHERE cv.dt_end IS NULL AND cv.i_parent_id IS NULL
        ORDER BY mc.c_name
        """
        result = self.db.execute_query(sql)

        classes = []
        for row in result:
            classes.append({
                'class_id': row[0],
                'c_name': row[1],
                'version_id': row[2],
                'c_base_source': row[3]
            })

        return classes