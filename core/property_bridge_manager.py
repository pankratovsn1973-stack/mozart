# -*- coding: utf-8 -*-
# core/property_bridge_manager.py
"""
Менеджер декларативных мостов свойств (Property Bridge Manager) платформы Mozart ERP.
Обеспечивает ОЗУ-кэширование правил трансляции метаданных и прямой рантайм-трансляции.

Архитектура v8.1:
  - Ядро не знает специфики. Всё делегируется резолверу или прямому setProperty.
  - Объединённые метаданные (Bridge + Override) кэшируются по (version_id, cname).
  - Поддержка BLOB: если prop.is_blob — значение передаётся как bytes.
"""
import re
from typing import Dict, Any, List, Optional, Tuple


class PropertyBridgeManager:
    """Глобальный менеджер правил связи, кэширования и трансляции low-code свойств."""

    def __init__(self, db_service=None):
        self.db = db_service

        # { c_base_class: { property_key: { 'id', 'ui_label', 'editor_type', ... } } }
        self._property_rules: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # { bridge_id: [ (c_value, display_ru), ... ] }
        self._allowed_values: Dict[int, List[Dict[str, str]]] = {}

        # { (version_id, cname): merged_meta_dict }
        self._meta_cache: Dict[Tuple[int, str], Dict[str, Any]] = {}

        # { version_id: { property_key: merged_meta_dict } }
        self._version_meta_cache: Dict[int, Dict[str, Dict[str, Any]]] = {}

    # =====================================================================
    # Прогрев кэша
    # =====================================================================
    def init_and_warm_cache(self):
        print("[DEBUG PBM] Старт прогрева кэша...")
        if not self.db:
            print("[DEBUG PBM] ОШИБКА: db_service не передан!")
            return

        self._property_rules.clear()
        self._allowed_values.clear()
        self._meta_cache.clear()
        self._version_meta_cache.clear()

        # 1. Правила из class_property_bridge
        sql_bridge = """
            SELECT id, c_base_class, property_key, ui_label_ru, editor_type,
                   qt_target, translation_strategy
            FROM class_erp.class_property_bridge
            WHERE dt_start IS NOT NULL;
        """
        try:
            rows_bridge = self.db.execute_query(sql_bridge) or []
            for r in rows_bridge:
                b_id, b_class, p_key, label, e_type, q_target, strategy = r
                if b_class not in self._property_rules:
                    self._property_rules[b_class] = {}
                self._property_rules[b_class][p_key] = {
                    'id': b_id,
                    'ui_label': label,
                    'editor_type': e_type,
                    'qt_target': q_target or p_key,
                    'strategy': strategy or 'DIRECT',
                }
        except Exception as e:
            print(f"❌ [PROPERTY BRIDGE] ОШИБКА чтения мостов: {e}")
            return

        # 2. Списки выбора (choice)
        sql_vals = """
            SELECT bridge_id, c_value, display_ru
            FROM class_erp.class_property_allowed_values
            ORDER BY bridge_id, i_sortorder, id;
        """
        try:
            rows_vals = self.db.execute_query(sql_vals) or []
            for r in rows_vals:
                bridge_id, c_val, disp = r
                if bridge_id not in self._allowed_values:
                    self._allowed_values[bridge_id] = []
                self._allowed_values[bridge_id].append({'value': c_val, 'display': disp})
        except Exception as e:
            print(f"❌ [PROPERTY BRIDGE] ОШИБКА загрузки списков выбора: {e}")

        print(f"✅ [PROPERTY BRIDGE] КЭШ ПРОГРЕТ. Классов: {len(self._property_rules)}")

    # =====================================================================
    # Доступ к базовым правилам (обратная совместимость)
    # =====================================================================
    def get_properties_for_class(self, c_base_class: str) -> Dict[str, Dict[str, Any]]:
        """Плоский словарь спецификаций low-code свойств для нативного класса."""
        return self._property_rules.get(c_base_class, {})

    def get_allowed_values(self, bridge_id: int) -> List[Dict[str, str]]:
        """Упорядоченный список выбора для комбобоксов."""
        return self._allowed_values.get(bridge_id, [])

    # =====================================================================
    # Объединённые метаданные (Bridge + Override)
    # =====================================================================
    def get_meta_for_property(self, version_id: int, cname: str) -> Dict[str, Any]:
        """
        Возвращает объединённые метаданные (Bridge + Override) для свойства.
        Кэш по (version_id, cname).
        """
        if version_id is None or version_id <= 0 or not cname:
            return {}

        cache_key = (version_id, cname)
        if cache_key in self._meta_cache:
            return self._meta_cache[cache_key]

        # Загружаем все правила для версии (кэш по version_id)
        all_meta = self._get_version_meta(version_id)
        meta = all_meta.get(cname, {})

        self._meta_cache[cache_key] = meta
        return meta

    def get_properties_for_version(self, version_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает ВСЕ объединённые правила для версии (кэш по version_id).
        """
        if version_id is None or version_id <= 0:
            return {}
        return self._get_version_meta(version_id)

    def _get_version_meta(self, version_id: int) -> Dict[str, Dict[str, Any]]:
        """Внутренний загрузчик метаданных для версии из f_get_property_bridges_for_version."""
        if version_id in self._version_meta_cache:
            return self._version_meta_cache[version_id]

        if not self.db:
            self._version_meta_cache[version_id] = {}
            return {}

        from ide_core import goProject
        iso_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")

        sql = """
            SELECT c_base_class, property_key, ui_label_ru, editor_type,
                   qt_target, translation_strategy, bridgecalcset, bridgecalcget,
                   fuuncselectionvalue, typesourcevalue, isdefaultepr,
                   defined_in_version_id, blob_name, owner_version_id
            FROM class_erp.f_get_property_bridges_for_version(%s, %s)
        """
        try:
            rows = self.db.execute_query(sql, (version_id, iso_date)) or []
        except Exception as e:
            print(f"[PropertyBridgeManager] Ошибка f_get_property_bridges_for_version({version_id}): {e}")
            rows = []

        result: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            (c_base_class, property_key, ui_label_ru, editor_type,
             qt_target, translation_strategy, bridgecalcset, bridgecalcget,
             fuuncselectionvalue, typesourcevalue, isdefaultepr,
             defined_in_version_id, blob_name, owner_version_id) = r
            result[property_key] = {
                'c_base_class': c_base_class,
                'property_key': property_key,
                'ui_label_ru': ui_label_ru,
                'editor_type': editor_type,
                'qt_target': qt_target,
                'translation_strategy': translation_strategy,
                'bridgecalcset': bridgecalcset,
                'bridgecalcget': bridgecalcget,
                'fuuncselectionvalue': fuuncselectionvalue,
                'typesourcevalue': typesourcevalue,
                'isdefaultepr': isdefaultepr,
                'defined_in_version_id': defined_in_version_id,
                'blob_name': blob_name,
                'owner_version_id': owner_version_id,
            }

        self._version_meta_cache[version_id] = result
        return result

    def invalidate_version_cache(self, version_id: Optional[int] = None):
        """Сбрасывает кэш метаданных (для одной версии или весь)."""
        if version_id is None:
            self._meta_cache.clear()
            self._version_meta_cache.clear()
        else:
            for key in list(self._meta_cache.keys()):
                if key[0] == version_id:
                    del self._meta_cache[key]
            self._version_meta_cache.pop(version_id, None)

    # =====================================================================
    # Прямое присвоение (fallback)
    # =====================================================================

    # =====================================================================
    # Применение к виджету
    # =====================================================================
    def apply_property_to_widget(self, widget, prop, version_id=None):
        """
        Применяет ОДНО свойство к виджету.
        ТОЛЬКО через bridgecalcset (SuperLibre / метод класса).
        Если bridgecalcset нет — свойство НЕ применяется к Qt.
        Оно остаётся в коллекции и уходит в БД при сохранении.
        """
        from ide_core import goProject

        if not widget or prop is None:
            return

        # ✅ Без моста — не применяем к Qt (свойство «скромно лежит» в коллекции)
        if not prop.bridgecalcset:
            return

        collection = getattr(self, 'current_collection', None)
        if collection is not None:
            goProject.current_collection = collection
        if version_id:
            goProject.current_element_id = version_id

        if prop.is_blob:
            value_for_bridge = prop.blob_value if prop.blob_value is not None else prop.value
        else:
            value_for_bridge = prop.value

        prop_id_col = getattr(prop, 'id_col', None)
        element_id_col = None
        mgr = getattr(collection, '_collection_manager', None) if collection else None
        if mgr is not None:
            element_id_col = mgr.get_id_col_by_element_reference(
                getattr(prop, 'owner_element_id', version_id)
            )

        # Единственный путь — резолвер → SuperLibre / метод класса
        goProject.bridge_resolver.resolve_to_runtime(
            prop.bridgecalcset,
            version_id or 0,
            widget,
            collection,
            prop.cname,
            value_for_bridge,
            prop_id_col=prop_id_col,
            element_id_col=element_id_col,
        )

# =====================================================================
    # Чтение из виджета
    # =====================================================================
    def read_property_from_widget(self, widget, prop, version_id=None, collection=None) -> Optional[str]:
        """Читает ОДНО свойство из живого Qt-виджета через BridgeResolver."""
        from ide_core import goProject

        if not widget or prop is None:
            return None

        if collection is None:
            collection = getattr(self, 'current_collection', None)

        prop_id_col = getattr(prop, 'id_col', None)
        element_id_col = None
        mgr = getattr(collection, '_collection_manager', None) if collection else None
        if mgr is not None:
            element_id_col = mgr.get_id_col_by_element_reference(
                getattr(prop, 'owner_element_id', version_id)
            )

        return goProject.bridge_resolver.resolve_from_runtime(
            prop.bridgecalcget,
            version_id or 0,
            widget,
            collection,
            prop.cname,
            prop_id_col=prop_id_col,
            element_id_col=element_id_col,
        )



    # =====================================================================
    # Полный проход по коллекции
    # =====================================================================
    def apply_bridge_translations(self, widget, collection, version_id=None):
        """
        v7.6: ТОЛЬКО SET при инициализации. GET отсутствует.
        Пробегаемся по ВСЕМ пропертям (включая пустые).
        Пустоту обрабатывает сам bridgecalcset.
        """
        from ide_core import goProject

        if not widget or collection is None:
            return

        goProject.current_collection = collection
        if version_id:
            goProject.current_element_id = version_id

        for prop in collection.all_ordered():
            self.apply_property_to_widget(widget, prop, version_id=version_id)