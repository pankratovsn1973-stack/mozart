# core/virtual_class_node.py
# -*- coding: utf-8 -*-
"""
Модуль структуры скомпилированного low-code класса в оперативной памяти Конфигуратора.
Реализует объектное представление узла (VMT) и его реляционных подколлекций.

v7.3: добавлено поле system_class_name — имя системного (Qt/Python) класса,
в который упёрлась линия крови. Заполняется в class_registry._load_class_from_db_cascade,
когда f_resolve_next_version возвращает отрицательный id (системный класс).
Используется PropertyBridgeManager для подтягивания мостов по c_base_class
и ClassEditDialog._get_c_base_class для определения целевого Qt-класса.
"""

from typing import Dict, Any, Optional


class VirtualClassNode:
    """
    Объектное представление версии класса и его унаследованных подобъектов
    в оперативной памяти (Virtual Method Table). Единственный источник правды для холста.
    """

    def __init__(self, version_id: int, class_id: int, class_name: str):
        self.version_id = version_id
        self.class_id = class_id
        self.class_name = class_name

        self.c_base_class = None

        # --- Паспорт топологии запуска ---
        self.c_execution_env = "HYBRID"
        self.is_preload = False
        self.status_id = 1

        # --- Генеалогические указатели ---
        # i_base_class_version_id — это id_mozart_class родительского ERP-класса,
        # а НЕ class_version.id. Ссылки в БД — на объект, не на снимок.
        self.i_base_class_version_id: Optional[int] = None
        self.c_base_source: str = "ERP"
        self.txt_properties_raw: str = ""
        self.donor_object_id: Optional[int] = None

        # --- НОВОЕ: имя системного класса (Qt/Python), в который упёрлась линия ---
        # Заполняется в class_registry._load_class_from_db_cascade, когда
        # f_resolve_next_version возвращает отрицательный id (системный класс).
        # Пример: 'QPushButton', 'QWidget', 'QLabel'.
        # Используется PropertyBridgeManager.get_properties_for_class(...)
        # и ClassEditDialog._get_c_base_class(...).
        self.system_class_name: Optional[str] = None

        # --- Реляционные подколлекции в ОЗУ ---
        # { property_name: { 'type': int, 'value': str, 'default_value': str, 'mask': str, 'source': str } }
        self.sub_properties: Dict[str, Dict[str, Any]] = {}

        # { method_name: txt_method_code_string }
        self.sub_methods: Dict[str, str] = {}

        # { method_key: { 'ui_label': str, 'isdefaultepr': bool, 'bridgecalc': str } }
        self.sub_method_bridges: Dict[str, Dict[str, Any]] = {}

        # { signal_name: id_method_to_trigger }
        self.sub_signals: Dict[str, Optional[int]] = {}

        # Кэш сырого результата f_build_objpropcol
        self.objpropcol_raw: Optional[list] = None

    # =====================================================================
    # Резолвинг метода с учётом mydefault (super)
    # =====================================================================
    def resolve_method(self, method_name: str) -> Optional[str]:
        """
        Возвращает исходный код метода (txt_method) или None.

        v9 FIX (корректный резолв предка):
        Раньше self.i_base_class_version_id (id_mozart_class) передавался
        напрямую в get_class_version(), который ожидает class_version.id.
        Для MozartButton (i_base_class=9) это находило version_id=9
        (QLineEdit) вместо QPushButton. Super-вызов был полностью сломан.

        Теперь:
        1. 'mydefault' → резолвим АКТИВНУЮ версию предка через
           f_get_active_version_id(i_base_class, session_date).
           Это гарантирует, что берётся именно живая версия на дату сессии,
           а не случайная строка с совпадающим ID.
        2. Обычный метод → ищем в sub_methods (уже загружены с учётом
           линии крови в _fill_local_node_sub_collections).
        3. Если метода нет ни локально, ни у предка → None.

        Контракт: вызывающий код (BridgeResolver) сам решает, что делать
        при None (fallback на SuperLibre). Этот метод НЕ обращается к
        SuperLibre напрямую.
        """
        if method_name == 'mydefault':
            base_class_id = self.i_base_class_version_id
            if not base_class_id or base_class_id <= 0:
                return None

            from ide_core import goProject

            # Резолвим активную версию предка на дату сессии
            parent_version_id = 0
            try:
                session_date = goProject.system_date.toPython()
                res = goProject.class_registry.db.execute_query(
                    "SELECT class_erp.f_get_active_version_id(%s, %s);",
                    (base_class_id, session_date)
                )
                if res and res[0]:
                    parent_version_id = int(res[0][0])
            except Exception as e:
                print(f"[VCN] Ошибка резолва предка для {self.class_name}: {e}")
                return None

            if parent_version_id <= 0:
                return None

            parent_node = goProject.class_registry.get_class_version(parent_version_id)
            if parent_node is None:
                return None

            # Рекурсивный вызов: предок тоже может иметь mydefault
            return parent_node.resolve_method(method_name)

        # Обычный метод: ищем в уже загруженных sub_methods
        if method_name in self.sub_methods:
            code = self.sub_methods[method_name]
            # Пустой код (NULL в БД) ≠ наличие метода
            return code if code and code.strip() else None

        return None
    # =====================================================================
    # Проверка: есть ли метод (собственный, в мостах или унаследованный)
    # =====================================================================
    def has_method(self, method_name: str) -> bool:
        """True, если метод есть в sub_methods, sub_method_bridges или резолвится через mydefault."""
        if method_name in self.sub_methods:
            return True
        if method_name in self.sub_method_bridges:
            return True
        if method_name == 'mydefault' and self.i_base_class_version_id:
            from ide_core import goProject
            parent_node = goProject.class_registry.get_class_version(
                self.i_base_class_version_id
            )
            if parent_node:
                return parent_node.has_method(method_name)
        return False