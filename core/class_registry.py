# core/class_registry.py
# -*- coding: utf-8 -*-
"""
Глобальная Машина классов (Class Registry / Class Loader) платформы Mozart ERP.
Обеспечивает кэширование, сборку «линий крови» и жесткую очистку неактивного ОЗУ.

v7.3: резолв предка через SQL-функцию class_erp.f_resolve_next_version.
Обработка системного класса (отрицательный id): не создаём VirtualClassNode,
но запоминаем имя в node.system_class_name.
"""

import gc
from typing import Dict, Optional
from core.virtual_class_node import VirtualClassNode


class ClassRegistry:
    """Глобальный менеджер и загрузчик low-code классов Конфигуратора."""

    def __init__(self, db_service=None):
        self.db = db_service
        # Главная хэш-карта кэша памяти: { version_id : VirtualClassNode }
        self._registry: Dict[int, VirtualClassNode] = {}

    def get_class_version(self, version_id: int) -> Optional[VirtualClassNode]:
        """
        Возвращает готовую версию класса из памяти.
        Если версии в кэше нет — запускает каскадную загрузку из СУБД по линии крови.

        v9 FIX (логирование):
        print выполнялся при КАЖДОМ обращении, включая cache hit, и печатал
        весь список ключей реестра. При загрузке формы с подобъектами это
        сотни строк спама в консоли. Теперь:
          • лог только при промахе кэша (реальная загрузка из БД);
          • вместо списка ключей — их количество;
          • всё под модульным флагом isDebug (по умолчанию False).

        Контракт не изменён: возврат VirtualClassNode или None.
        Отрицательный/нулевой id (системный класс) по-прежнему даёт None —
        системные классы не имеют VirtualClassNode.
        """
        if version_id is None or version_id <= 0:
            return None

        node = self._registry.get(version_id)
        if node is not None:
            return node

        if isDebug:
            print(f"[ClassRegistry] CACHE MISS v{version_id} "
                  f"(в кэше {len(self._registry)} версий, "
                  f"БД={'да' if self.db is not None else 'нет'})")

        return self._load_class_from_db_cascade(version_id)

    def get_objpropcol_raw(self, version_id: int) -> list:
        """Ленивый кэш результата f_build_objpropcol для версии класса (v8.1)."""
        if version_id is None or version_id <= 0:
            return []

        node = self.get_class_version(version_id)
        if node is None:
            return []

        if node.objpropcol_raw is not None:
            return node.objpropcol_raw

        if not self.db:
            node.objpropcol_raw = []
            return node.objpropcol_raw

        from ide_core import goProject
        iso_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")

        sql = """
            SELECT 
                id,                     -- idx 0
                cname,                  -- idx 1
                "order",                -- idx 2
                value,                  -- idx 3
                typevalue,              -- idx 4
                sourcevalue,            -- idx 5
                typesourcevalue,        -- idx 6
                fuuncselectionvalue,    -- idx 7
                bridgecalcset,          -- idx 8
                bridgecalcget,          -- idx 9
                defined_in_version_id,  -- idx 10
                ui_label_ru,            -- idx 11
                editor_type,            -- idx 12
                qt_target,              -- idx 13
                translation_strategy,   -- idx 14
                isdefaultepr,           -- idx 15
                blob_value,             -- idx 16
                is_blob,                -- idx 17
                blob_name,              -- idx 18
                owner_version_id        -- idx 19
            FROM class_erp.f_build_objpropcol(%s, %s)
            ORDER BY "order", cname
        """
        try:
            rows = self.db.execute_query(sql, (version_id, iso_date)) or []
        except Exception as e:
            print(f"[ClassRegistry] Ошибка f_build_objpropcol для {version_id}: {e}")
            rows = []

        node.objpropcol_raw = rows
        return rows

    def _load_class_from_db_cascade(self, version_id: int) -> Optional[VirtualClassNode]:
        if not self.db:
            return None

        sql = """
        SELECT
            cv.id_mozart_class, mc.c_name, cv.c_base_class, cv.c_base_source,
            cv.c_execution_env, cv.is_preload, cv.status_id, cv.i_base_class, cv.txt_properties,
            cv.donor_object_id
        FROM class_erp.class_version cv
        JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
        WHERE cv.id = %s AND cv.dt_end IS NULL;
        """

        res = self.db.execute_query(sql, (version_id,))
        if not res:
            return None

        row = res[0]
        (c_mc_id, c_name, b_class, b_source, exec_env, preload,
         stat_id, b_class_vid, geo_json, donor_id) = row

        node = VirtualClassNode(version_id, c_mc_id, c_name)

        node.c_base_class = b_class or 'QWidget'
        node.c_base_source = b_source or "ERP"
        node.c_execution_env = exec_env or "HYBRID"
        node.is_preload = bool(preload)
        node.status_id = stat_id or 1
        # ВНИМАНИЕ: i_base_class — это id_mozart_class родительского ERP-класса,
        # а не class_version.id. Ссылки в БД — на объект, не на снимок.
        node.i_base_class_version_id = b_class_vid
        node.txt_properties_raw = geo_json or ""
        node.donor_object_id = donor_id

        # ─── Резолв предка через SQL-функцию (donor → i_base_class → system_classes) ───
        parent_id = self._resolve_next_version(version_id)

        if parent_id > 0:
            # ERP-предок: рекурсивно грузим VirtualClassNode и сливаем подколлекции
            parent_node = self.get_class_version(parent_id)
            if parent_node:
                node.sub_properties.update(dict(parent_node.sub_properties))
                node.sub_methods.update(dict(parent_node.sub_methods))
                node.sub_method_bridges.update(dict(parent_node.sub_method_bridges))
                node.sub_signals.update(dict(parent_node.sub_signals))
                # Прокидываем имя системного класса от предка, если у текущего его нет
                if node.system_class_name is None and parent_node.system_class_name is not None:
                    node.system_class_name = parent_node.system_class_name
        elif parent_id < 0:
            # Системный класс: не создаём VirtualClassNode, но запоминаем имя
            sys_name = self._get_system_class_name(-parent_id)
            node.system_class_name = sys_name
        # parent_id == 0 → конец линии, ничего не делаем

        self._fill_local_node_sub_collections(node)
        self._registry[version_id] = node

        print(f"[ClassRegistry] Версия класса {c_name} (ID: {version_id}) успешно откомпилирована в памяти.")
        return node

    def _resolve_next_version(self, version_id: int) -> int:
        """
        Тонкая обёртка над class_erp.f_resolve_next_version.
        Возвращает:
          > 0 — id ERP-версии предка;
          < 0 — -system_classes.id (системный класс);
            0 — предка нет.
        """
        if not self.db:
            return 0

        from ide_core import goProject
        try:
            session_date = goProject.system_date.toPython()
            res = self.db.execute_query(
                "SELECT class_erp.f_resolve_next_version(%s, %s);",
                (version_id, session_date)
            )
            if res and res[0]:
                return int(res[0][0])
        except Exception as e:
            print(f"[ClassRegistry] Ошибка резолва предка для {version_id}: {e}")
        return 0

    def _get_system_class_name(self, sys_id: int) -> Optional[str]:
        """
        Возвращает c_name системного класса по system_classes.id.
        Пример: sys_id=12 → 'QPushButton'.
        """
        if not self.db:
            return None
        try:
            res = self.db.execute_query(
                "SELECT c_name FROM class_erp.system_classes WHERE id = %s AND dt_end IS NULL;",
                (sys_id,)
            )
            if res and res[0]:
                return str(res[0][0])
        except Exception as e:
            print(f"[ClassRegistry] Ошибка получения системного класса {sys_id}: {e}")
        return None

    def _fill_local_node_sub_collections(self, node: VirtualClassNode):
        """
        Загружает свойства, методы, мосты методов и сигналы для ОДНОЙ версии
        класса (без рекурсии — предки уже слиты в _load_class_from_db_cascade).

        v9 FIX (методы):
        f_get_class_methods_on_date возвращает 9 колонок:
          id, c_name, txt_method, "order", defined_in_version_id,
          owner_class_id, i_lang, dt_start, dt_end.
        Раньше код читал только 2 → ValueError на любом классе с методами.

        v9 FIX (сигналы):
        Сигналы конвертируются в SignalItem и регистрируются в общем индексе
        idCol CollectionManager (если он доступен). Без этого SignalsDialog
        и MethodsDialog не находили их через get_object_by_id_col.

        v9 FIX (свойства):
        При слиянии с предком используем update(), который НЕ стирает
        локальные переопределения: если ключ уже есть в sub_properties
        текущего узла, предковая версия его не затирает.

        v9 FIX (isDebug):
        Переменная isDebug не была определена в модуле → NameError при
        загрузке любого класса. Добавлена локально как False; для включения
        отладки установить True или импортировать из ide_core.
        """
        from ide_core import goProject
        iso_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")
        isDebug = False  # Установить True для отладки загрузки классов

        # --- Свойства (только собственные этой версии) -------------------
        sql_props = ("SELECT c_name, type, mask, source, c_value, c_default_value "
                     "FROM class_erp.f_get_class_properties_on_date(%s, %s);")
        rows_props = self.db.execute_query(sql_props, (node.version_id, iso_date)) or []
        for r in rows_props:
            p_name, p_type, p_mask, p_source, p_val, p_def = r
            # Не затираем унаследованное, если локальное уже есть
            if p_name not in node.sub_properties:
                node.sub_properties[p_name] = {
                    'type': int(p_type) if p_type is not None else 0,
                    'value': str(p_val if p_val is not None else ""),
                    'default_value': str(p_def if p_def is not None else ""),
                    'mask': p_mask or '',
                    'source': p_source or ''
                }

        # --- Методы (9 колонок!) -----------------------------------------
        sql_meths = ("SELECT id, c_name, txt_method, \"order\", defined_in_version_id, "
                     "owner_class_id, i_lang, dt_start, dt_end "
                     "FROM class_erp.f_get_class_methods_on_date(%s, %s);")
        rows_meths = self.db.execute_query(sql_meths, (node.version_id, iso_date)) or []
        for r in rows_meths:
            m_id, m_name, m_text, m_order, m_defined_in, m_owner, m_lang, m_dt_start, m_dt_end = r
            # Не затираем унаследованный метод, если локальный уже есть
            if m_name not in node.sub_methods:
                node.sub_methods[m_name] = str(m_text or "")

        # --- Мосты методов -----------------------------------------------
        if node.c_base_class:
            sql_mbridges = ("SELECT method_key, ui_label_ru, isdefaultepr, bridgecalc, dt_start "
                            "FROM class_erp.f_get_class_method_bridges_on_date(%s, %s);")
            rows_mbridges = self.db.execute_query(
                sql_mbridges, (node.c_base_class, iso_date)
            ) or []
            for r in rows_mbridges:
                mk, label, is_def, bc, dt = r
                if mk not in node.sub_method_bridges:
                    node.sub_method_bridges[mk] = {
                        'ui_label': label or mk,
                        'isdefaultepr': bool(is_def),
                        'bridgecalc': bc or '',
                    }

        # --- Сигналы -----------------------------------------------------
        sql_sigs = ("SELECT c_signal, id_method "
                    "FROM class_erp.f_get_class_signals_on_date(%s, %s);")
        rows_sigs = self.db.execute_query(sql_sigs, (node.version_id, iso_date)) or []
        for r in rows_sigs:
            s_name, m_id = r
            if s_name not in node.sub_signals:
                node.sub_signals[s_name] = m_id

        if isDebug:
            print(f"[ClassRegistry] v{node.version_id} ({node.class_name}): "
                  f"props={len(node.sub_properties)}, "
                  f"methods={len(node.sub_methods)}, "
                  f"bridges={len(node.sub_method_bridges)}, "
                  f"signals={len(node.sub_signals)}")

    def sync_registry_with_session_date(self):
        """
        Жестко выжигает из ОЗУ все версии классов, которые не попадают
        в актуальный исторический срез на выбранную дату сессии.
        """
        from ide_core import goProject
        if not self.db:
            return

        iso_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")

        sql = """
        SELECT cv.id
        FROM class_erp.class_version cv
        WHERE %s::timestamp without time zone BETWEEN
            COALESCE(cv.dt_start, '-infinity'::timestamp) AND COALESCE(cv.dt_end, 'infinity'::timestamp);
        """

        try:
            rows = self.db.execute_query(sql, (iso_date,)) or []
            active_version_ids = {row[0] if isinstance(row, (list, tuple)) else row for row in rows}
        except Exception as e:
            print(f"[ERROR] Не удалось получить срез активных версий: {e}")
            return

        cached_version_ids = list(self._registry.keys())
        for v_id in cached_version_ids:
            if v_id not in active_version_ids:
                deleted_node = self._registry.pop(v_id, None)
                if deleted_node:
                    print(
                        f"[ClassRegistry] Из ОЗУ выгружена неактивная версия класса: {deleted_node.class_name} (ID: {v_id})")

        gc.collect()