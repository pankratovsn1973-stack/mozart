# Полный путь: services/class_data_service.py
"""
Сервис для работы с метаданными классов ERP.
Использует единый экземпляр DatabaseService, переданный извне.
Реализует CRUD для классов, версий, методов и сигналов.
Обеспечивает получение иерархического дерева классов для отображения.
Не создает новых подключений к БД.

АРХИТЕКТУРНЫЕ ПРИНЦИПЫ:
1. Бизнес-логика выборки (фильтрация по дате, рекурсия) вынесена в PostgreSQL.
2. Python-сервис отвечает только за передачу параметров и маппинг результатов.
3. Все операции чтения учитывают текущую дату сессии (Machine Time).
4. Порядок загрузки (i_load_order) является характеристикой версии, а не класса.
"""
from typing import List, Dict, Optional, Any
from database import DatabaseService
from ide_core import goProject


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

    # =====================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =====================================================================

    def _get_session_date(self) -> str:
        """
        Получает текущую дату сессии для исторических срезов.
        Используется во всех SQL-запросах для фильтрации активных версий.

        Выход:
            str - дата в формате 'YYYY-MM-DD HH:mm:ss'
        """
        return goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")

    # =====================================================================
    # ДЕРЕВО КЛАССОВ (ДЕЛЕГИРОВАНИЕ В POSTGRESQL)
    # =====================================================================

    def get_classes_tree(self) -> List[Dict]:
        """
        Получение иерархического дерева классов НА АКТУАЛЬНУЮ ДАТУ СЕССИИ.

        ВАЖНО: Вся логика рекурсии, фильтрации по dt_start/dt_end и сортировки
        по i_load_order выполняется внутри хранимой функции f_get_active_classes_tree.
        Это обеспечивает максимальную производительность и целостность данных.

        Вход: Нет
        Выход:
            List[Dict] - список словарей с полями:
                - version_id: int - ID версии класса
                - class_id: int - ID абстрактного класса
                - c_name: str - имя класса
                - i_load_order: int - порядок загрузки (из class_version!)
                - is_visible: bool - видимость
                - c_base_class: str - имя базового Qt-класса
                - c_base_source: str - источник ('PYTHON', 'ERP')
                - i_parent_id: Optional[int] - ID родительской версии
                - level: int - уровень вложенности
                - root_class_id: int - ID корневой версии
                - category_id: int - ID категории
                - category_name: str - имя категории
                - category_alias: str - алиас категории
                - category_parent_id: int - ID родительской категории
                - category_comment: str - комментарий категории
                - class_comment: str - комментарий класса
                - c_execution_env: str - среда выполнения
                - is_preload: bool - флаг предзагрузки
        """
        # Получаем актуальную дату сессии
        session_date = self._get_session_date()

        # Вызываем оптимизированную хранимую функцию PostgreSQL
        # Она возвращает готовое плоское дерево с учетом истории и порядка загрузки
        sql = "SELECT * FROM class_erp.f_get_active_classes_tree(%s);"
        result = self.db.execute_query(sql, (session_date,))

        if not result:
            return []

        # Маппинг кортежей из БД в словари для удобства использования в UI
        columns = [
            'version_id', 'class_id', 'c_name', 'i_load_order', 'is_visible',
            'c_base_class', 'c_base_source', 'i_parent_id', 'level', 'root_class_id',
            'category_id', 'category_name', 'category_alias', 'category_parent_id',
            'category_comment', 'class_comment', 'c_execution_env', 'is_preload'
        ]
        return [dict(zip(columns, row)) for row in result]

    # =====================================================================
    # ЧТЕНИЕ ПОЛНЫХ ДАННЫХ ВЕРСИИ (С УЧЕТОМ ИСТОРИИ)
    # =====================================================================

    def get_class_version(self, version_id: int) -> Optional[Dict]:
        """
        Полные данные версии класса НА ТЕКУЩУЮ ДАТУ СЕССИИ.

        Включает: метаданные версии, свойства, методы и сигналы.
        Все подзапросы фильтруются по дате сессии для поддержки Machine Time.
        Поле i_load_order берется строго из class_version.

        Вход:
            version_id: int - ID запрашиваемой версии класса
        Выход:
            Optional[Dict] - словарь с ключами 'version', 'properties', 'methods', 'signals'
                             или None, если версия не найдена/неактивна
        """
        session_date = self._get_session_date()

        # ---------------------------------------------------------------------
        # 1. Основные метаданные версии
        # ---------------------------------------------------------------------
        sql_version = """
        SELECT mc.id AS class_id, mc.c_name, cv.i_load_order, mc.mcomment,
               cv.id, cv.is_visible, cv.c_base_class, cv.c_base_source,
               cv.i_base_class, cv.i_parent_id, cv.txt_properties,
               cv.dt_start, cv.dt_end, cv.c_execution_env, cv.is_preload,
               cv.status_id, cv.donor_object_id
        FROM class_erp.class_version cv
        JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
        WHERE cv.id = %s 
          AND %s::timestamp BETWEEN COALESCE(cv.dt_start, '-infinity') 
                                AND COALESCE(cv.dt_end, 'infinity')
        ORDER BY cv.i_load_order
        """
        version_rows = self.db.execute_query(sql_version, (version_id, session_date))
        if not version_rows:
            return None

        r = version_rows[0]
        version = {
            'id': r[4],
            'class_id': r[0],
            'c_name': r[1],
            'i_load_order': r[2],  # ✅ ТЕПЕРЬ ИЗ class_version
            'mcomment': r[3],
            'is_visible': r[5],
            'c_base_class': r[6],
            'c_base_source': r[7],
            'i_base_class': r[8],
            'i_parent_id': r[9],
            'txt_properties': r[10],
            'dt_start': r[11],
            'dt_end': r[12],
            'c_execution_env': r[13],
            'is_preload': r[14],
            'status_id': r[15],
            'donor_object_id': r[16],
        }

        # ---------------------------------------------------------------------
        # 2. Свойства версии (с учетом даты сессии!)
        # ---------------------------------------------------------------------
        sql_properties = """
        SELECT id, c_name, type, mask, source, dt_start, dt_end, c_value, c_default_value
        FROM class_erp.class_version_properties
        WHERE id_class_version = %s 
          AND %s::timestamp BETWEEN COALESCE(dt_start, '-infinity') 
                                AND COALESCE(dt_end, 'infinity')
        ORDER BY id
        """
        properties_rows = self.db.execute_query(sql_properties, (version_id, session_date)) or []
        properties_list = []
        for p in properties_rows:
            properties_list.append({
                'id': p[0],
                'c_name': p[1],
                'type': p[2],
                'mask': p[3],
                'source': p[4],
                'dt_start': p[5],
                'dt_end': p[6],
                'c_value': p[7],  # Значение свойства
                'c_default_value': p[8]  # Дефолтное значение
            })

        # ---------------------------------------------------------------------
        # 3. Методы (с учетом даты сессии для связи и версии метода!)
        # ---------------------------------------------------------------------
        sql_methods = """
        SELECT m.id, m.c_name, mv.id AS method_version_id, mv.txt_method,
               mv.c_komment, mv.dt_start, mv.dt_end
        FROM class_erp.method_class_relation mcr
        JOIN class_erp.method m ON mcr.id_method = m.id
        JOIN class_erp.method_version mv ON m.id = mv.id_method
        WHERE mcr.id_class_version = %s
          AND %s::timestamp BETWEEN COALESCE(mcr.dt_start, '-infinity') 
                                AND COALESCE(mcr.dt_end, 'infinity')
          AND %s::timestamp BETWEEN COALESCE(mv.dt_start, '-infinity') 
                                AND COALESCE(mv.dt_end, 'infinity')
        ORDER BY m.c_name
        """
        methods_rows = self.db.execute_query(
            sql_methods, (version_id, session_date, session_date)
        ) or []
        methods_list = []
        for m in methods_rows:
            methods_list.append({
                'id': m[0],
                'c_name': m[1],
                'method_version_id': m[2],
                'txt_method': m[3],
                'c_komment': m[4],
                'dt_start': m[5],
                'dt_end': m[6],
            })

        # ---------------------------------------------------------------------
        # 4. Сигналы (с учетом даты сессии!)
        # ---------------------------------------------------------------------
        sql_signals = """
        SELECT s.id, s.c_signal, m.id AS method_id, m.c_name AS method_name
        FROM class_erp.signal s
        LEFT JOIN class_erp.method m ON s.id_method = m.id
        WHERE s.id_class_version = %s 
          AND %s::timestamp BETWEEN COALESCE(s.dt_start, '-infinity') 
                                AND COALESCE(s.dt_end, 'infinity')
        ORDER BY s.c_signal
        """
        signals_rows = self.db.execute_query(sql_signals, (version_id, session_date)) or []
        signals_list = []
        for s in signals_rows:
            signals_list.append({
                'id': s[0],
                'c_signal': s[1],
                'method_id': s[2],
                'method_name': s[3],
            })

        return {
            'version': version,
            'properties': properties_list,
            'methods': methods_list,
            'signals': signals_list,
        }

    # =====================================================================
    # СОЗДАНИЕ И ОБНОВЛЕНИЕ ВЕРСИЙ
    # =====================================================================

    def create_class_version(self, data: Dict) -> int:
        """
        Создание новой версии класса.

        Вход:
            data: Dict - словарь с полями:
                - c_name: str - имя класса (обязательно)
                - c_base_class: str - имя базового Qt-класса
                - c_base_source: str - источник ('PYTHON' или 'ERP')
                - i_base_class: Optional[int] - ID родительской версии (для наследования)
                - i_parent_id: Optional[int] - ID родительского контейнера
                - is_visible: bool - флаг видимости
                - txt_properties: str - JSON со свойствами
                - i_load_order: int - порядок загрузки (ОБЯЗАТЕЛЬНО)
        Выход:
            int - ID созданной версии класса
        """
        # 1. Создаем запись в таблице абстрактных классов
        sql_class = """
        INSERT INTO class_erp.mozartclasses (c_name)
        VALUES (%s)
        RETURNING id
        """
        class_result = self.db.execute_query(sql_class, (data.get('c_name'),))
        class_id = class_result[0][0] if class_result else None
        if not class_id:
            raise ValueError("Не удалось создать абстрактный класс")

        # 2. Создаем версию класса с порядком загрузки
        sql_version = """
        INSERT INTO class_erp.class_version 
        (id_mozart_class, c_base_class, c_base_source, 
         i_base_class, i_parent_id, is_visible, txt_properties, i_load_order)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        version_result = self.db.execute_query(sql_version, (
            class_id,
            data.get('c_base_class', ''),
            data.get('c_base_source', 'ERP'),
            data.get('i_base_class'),
            data.get('i_parent_id'),
            data.get('is_visible', True),
            data.get('txt_properties', '{}'),
            data.get('i_load_order', 100)  # ✅ Сохраняем порядок загрузки
        ))
        if not version_result:
            raise ValueError("Не удалось создать версию класса")
        return version_result[0][0]

    def update_class_version(self, version_id: int, data: Dict) -> bool:
        """
        Обновление данных существующей активной версии класса.

        Вход:
            version_id: int - ID обновляемой версии
            data: Dict - обновляемые поля
        Выход:
            bool - True при успехе
        """
        sql = """
        UPDATE class_erp.class_version 
        SET c_base_class = %s, 
            c_base_source = %s, 
            i_base_class = %s, 
            i_parent_id = %s, 
            is_visible = %s, 
            txt_properties = %s,
            i_load_order = %s       -- ✅ Обновляем порядок загрузки
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (
            data.get('c_base_class', ''),
            data.get('c_base_source', 'ERP'),
            data.get('i_base_class'),
            data.get('i_parent_id'),
            data.get('is_visible', True),
            data.get('txt_properties', '{}'),
            data.get('i_load_order', 100),
            version_id
        ), fetch=False)
        return True

    def soft_delete_class_version(self, version_id: int) -> bool:
        """
        Мягкое удаление версии класса (установка dt_end = NOW()).
        Версия становится неактивной для текущей и будущих дат сессии.

        Вход:
            version_id: int - ID удаляемой версии
        Выход:
            bool - True при успехе
        """
        sql = """
        UPDATE class_erp.class_version 
        SET dt_end = NOW() 
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (version_id,), fetch=False)
        return True

    # =====================================================================
    # РАБОТА С МЕТОДАМИ
    # =====================================================================

    def get_class_methods(self, version_id: int) -> List[Dict]:
        """
        Получение списка методов, связанных с версией класса НА ДАТУ СЕССИИ.

        Вход:
            version_id: int - ID версии класса
        Выход:
            List[Dict] - список методов
        """
        session_date = self._get_session_date()
        sql = """
        SELECT m.id, m.c_name, mv.id as method_version_id, mv.txt_method, mv.c_komment
        FROM class_erp.method_class_relation mcr
        JOIN class_erp.method m ON mcr.id_method = m.id
        JOIN class_erp.method_version mv ON m.id = mv.id_method
        WHERE mcr.id_class_version = %s 
          AND %s::timestamp BETWEEN COALESCE(mcr.dt_start, '-infinity') 
                                AND COALESCE(mcr.dt_end, 'infinity')
          AND %s::timestamp BETWEEN COALESCE(mv.dt_start, '-infinity') 
                                AND COALESCE(mv.dt_end, 'infinity')
        ORDER BY m.c_name
        """
        result = self.db.execute_query(sql, (version_id, session_date, session_date))
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
        Добавление нового метода к классу.

        Вход:
            version_id: int - ID версии класса
            method_data: Dict - данные метода (c_name, c_komment, txt_method)
        Выход:
            int - ID созданного метода
        """
        # 1. Создаем абстрактный метод
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

        # 3. Связываем метод с версией класса
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
            bool - True при успехе
        """
        sql = """
        UPDATE class_erp.method_class_relation 
        SET dt_end = NOW() 
        WHERE id_method = %s AND id_class_version = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (method_id, version_id), fetch=False)
        return True

    # =====================================================================
    # РАБОТА С СИГНАЛАМИ
    # =====================================================================

    def get_class_signals(self, version_id: int) -> List[Dict]:
        """
        Получение списка сигналов класса НА ДАТУ СЕССИИ.

        Вход:
            version_id: int - ID версии класса
        Выход:
            List[Dict] - список сигналов
        """
        session_date = self._get_session_date()
        sql = """
        SELECT s.id, s.c_signal, m.id AS method_id, m.c_name AS method_name
        FROM class_erp.signal s
        LEFT JOIN class_erp.method m ON s.id_method = m.id
        WHERE s.id_class_version = %s 
          AND %s::timestamp BETWEEN COALESCE(s.dt_start, '-infinity') 
                                AND COALESCE(s.dt_end, 'infinity')
        ORDER BY s.c_signal
        """
        result = self.db.execute_query(sql, (version_id, session_date))
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
        Привязка метода к сигналу (или отвязка, если method_id=None).

        Вход:
            signal_id: int - ID сигнала
            method_id: Optional[int] - ID метода
        Выход:
            bool - True при успехе
        """
        sql = """
        UPDATE class_erp.signal 
        SET id_method = %s 
        WHERE id = %s AND dt_end IS NULL
        """
        self.db.execute_query(sql, (method_id, signal_id), fetch=False)
        return True

    # =====================================================================
    # СПРАВОЧНЫЕ МЕТОДЫ
    # =====================================================================

    def get_all_methods(self) -> List[Dict]:
        """
        Получение списка всех доступных методов (без учета версии класса).

        Выход:
            List[Dict] - список методов (id, c_name)
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
        Только корневые активные версии НА ДАТУ СЕССИИ.

        Выход:
            List[Dict] - список классов
        """
        session_date = self._get_session_date()
        sql = """
        SELECT mc.id as class_id, mc.c_name, cv.id as version_id, cv.c_base_source
        FROM class_erp.mozartclasses mc
        JOIN class_erp.class_version cv ON mc.id = cv.id_mozart_class
        WHERE cv.dt_end IS NULL 
          AND cv.i_parent_id IS NULL
          AND %s::timestamp BETWEEN COALESCE(cv.dt_start, '-infinity') 
                                AND COALESCE(cv.dt_end, 'infinity')
        ORDER BY mc.c_name
        """
        result = self.db.execute_query(sql, (session_date,))
        classes = []
        for row in result:
            classes.append({
                'class_id': row[0],
                'c_name': row[1],
                'version_id': row[2],
                'c_base_source': row[3]
            })
        return classes