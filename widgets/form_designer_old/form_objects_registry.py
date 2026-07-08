# /home/sergey/Documents/configurate/widgets/form_designer_old/form_objects_registry.py
"""
Модуль: Глобальный реестр визуальных объектов дизайнера форм.

Роль в архитектуре Mozart ERP:
    - Централизованное хранилище метаданных всех объектов на холсте дизайнера.
    - Обеспечивает поиск объектов по control_id (из БД), calias и parentid.
    - Реализует паттерн Unit of Work для отслеживания изменений перед сохранением.
    - Предоставляет WeakRef-ссылки на виджеты для предотвращения утечек памяти.
    - Служит единым источником истины для всех графических элементов формы.
    - Содержит системный предохранитель для гарантии единственности объекта формы.

Ключевые зависимости:
    - Используется всеми компонентами дизайнера (scene, control_item, loader, etc.)
    - Взаимодействует с DesignerDataModel для хранения свойств объектов.
"""

import weakref


class FormObjectsRegistry:
    """
    Синглтон-реестр для управления состоянием объектов на сцене.

    Свойства:
        - _registry: dict[str, dict] - Основной словарь. Ключ = control_id (из БД).
          Значение содержит: control_id, parentid, calias, cclass, widget_ref, full_path.
        - _wid_to_cid_map: dict[int, str] - Технический словарь для обратного поиска ID по адресу виджета.
        - _index_by_path: dict[(str, str), str] - Индекс для быстрого поиска по кортежу (parentid, calias).

    Основные методы:
        - register_object: Регистрация нового или обновление существующего элемента.
        - get_meta_by_parent_and_calias: Поиск метаданных по пути в иерархии.
        - get_id_by_widget: Обратный поиск ID по экземпляру виджета через маппинг.
        - clear: Полная очистка всех структур реестра при загрузке новой формы.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FormObjectsRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._registry = {}  # ПУНКТ 2.1.1.1: Ключ = control_id
            cls._instance._wid_to_cid_map = {}  # Технический индекс wid -> control_id
            cls._instance._index_by_path = {}  # ПУНКТ 2.1.1.3: Ключ = (parentid, calias)
        return cls._instance

    # ==================== ПУНКТ 2.1.1.2 + REGISTRY GUARD ====================
    def register_object(self, control_id, widget_obj, parentid=None,
                        full_path="", calias="", cclass=""):
        """
        Регистрация объекта в реестре по control_id из БД.

        Args:
            control_id: str - Числовой идентификатор из meta.form_elements
                              (или отрицательный для новых) - ОБЯЗАТЕЛЬНЫЙ параметр
            widget_obj: QWidget - Виджет для регистрации
            parentid: str - ID родительского контрола (из БД)
            full_path: str - Полный путь в иерархии (для отладки)
            calias: str - Бизнес-алиас контрола
            cclass: str - Класс контрола (textbox, reference, button, form, etc.)

        Returns:
            str - Зарегистрированный control_id или None
        """
        if not widget_obj or not control_id:
            return None

        # ✅ СИСТЕМНЫЙ ПРЕДОХРАНИТЕЛЬ: Уничтожаем все старые формы при регистрации новой
        new_cclass = str(cclass).lower().strip()
        if new_cclass == 'form':
            keys_to_delete = []
            for cid, meta in self._registry.items():
                if str(meta.get('cclass', '')).lower().strip() == 'form':
                    keys_to_delete.append(cid)

            for key in keys_to_delete:
                old_meta = self._registry[key]
                old_wid = id(old_meta['widget_ref']()) if old_meta.get('widget_ref') else None

                # Чистим технический маппинг
                if old_wid and old_wid in self._wid_to_cid_map:
                    del self._wid_to_cid_map[old_wid]

                # Чистим индекс путей
                path_key = (str(old_meta.get('parentid')), str(old_meta.get('calias')))
                if path_key in self._index_by_path:
                    del self._index_by_path[path_key]

                del self._registry[key]

            if keys_to_delete:
                print(f"[REGISTRY_GUARD] Удалено {len(keys_to_delete)} старых записей форм: {keys_to_delete}")

        control_id = str(control_id)
        wid = id(widget_obj)

        # Присваиваем бизнес-атрибуты виджету
        if calias:
            widget_obj.calias = calias
        if cclass:
            widget_obj.cclass = cclass

        # Уникализация objectName для Qt (только если объект поддерживает это свойство)
        if hasattr(widget_obj, 'objectName') and hasattr(widget_obj, 'setObjectName'):
            unique_qt_name = f"{calias}_{control_id}" if calias else f"control_{control_id}"
            if widget_obj.objectName() != unique_qt_name:
                widget_obj.setObjectName(unique_qt_name)

        # ==================== ПУНКТ 4.1.2.1 ====================
        # Создаем запись в реестре с обязательным полем cclass
        meta = {
            "control_id": control_id,
            "parentid": str(parentid) if parentid else None,
            "cclass": str(cclass) if cclass else "",
            "widget_ref": weakref.ref(widget_obj),
            "full_path": str(full_path) if full_path else "",
            "calias": str(calias) if calias else ""
        }

        # Сохраняем в _registry, используя control_id как ЕДИНСТВЕННЫЙ ключ
        self._registry[control_id] = meta

        # Обновляем технический маппинг wid -> control_id
        self._wid_to_cid_map[wid] = control_id

        # Индексация по пути для быстрого поиска дочерних элементов
        if parentid and calias:
            path_key = (str(parentid), str(calias))
            self._index_by_path[path_key] = control_id

        return control_id

    def get_meta_by_widget(self, widget_obj):
        """
        Поиск метаданных через технический маппинг wid -> control_id.
        Поддерживает как прямые виджеты, так и прокси-виджеты.
        """
        if not widget_obj:
            return None

        wid = id(widget_obj)

        # 1. Прямой поиск по техническому индексу
        control_id = self._wid_to_cid_map.get(wid)
        if control_id:
            return self._registry.get(control_id)

        # 2. Поиск через прокси-виджет (QGraphicsProxyWidget)
        for cid, meta in self._registry.items():
            ref = meta.get("widget_ref")
            actual_ref = ref() if isinstance(ref, weakref.ref) else ref
            if actual_ref:
                # Проверяем, является ли actual_ref прокси для widget_obj
                if hasattr(actual_ref, 'widget') and callable(actual_ref.widget):
                    if actual_ref.widget() == widget_obj:
                        return meta
                # Проверяем, является ли widget_obj прокси для actual_ref
                if hasattr(widget_obj, 'widget') and callable(widget_obj.widget):
                    if widget_obj.widget() == actual_ref:
                        return meta

        # 3. Поиск по calias (fallback)
        widget_calias = getattr(widget_obj, 'calias', None)
        if widget_calias:
            for cid, meta in self._registry.items():
                if meta.get("calias") == widget_calias:
                    ref = meta.get("widget_ref")
                    actual_ref = ref() if isinstance(ref, weakref.ref) else ref
                    if actual_ref is widget_obj or actual_ref is None:
                        return meta

        return None

    # ==================== ПУНКТ 6.1.1.2 ====================
    def get_meta_by_parent_and_calias(self, parentid, calias):
        """
        Поиск метаданных по родителю и алиасу (для каскадного клика).

        Args:
            parentid: str - ID родительского контрола
            calias: str - Бизнес-алиас дочернего элемента

        Returns:
            dict or None - Метаданные найденного объекта или None
        """
        if not parentid or not calias:
            return None

        path_key = (str(parentid), str(calias))
        control_id = self._index_by_path.get(path_key)

        if control_id:
            return self._registry.get(str(control_id))
        return None

    def get_id_by_widget(self, widget_obj):
        """
        Получение control_id по виджету.

        Args:
            widget_obj: QWidget - Виджет для поиска

        Returns:
            str - control_id или "unknown"
        """
        meta = self.get_meta_by_widget(widget_obj)
        return meta["control_id"] if meta else "unknown"

    def get_widget_by_id(self, control_id):
        """
        Получение виджета по его control_id.

        Args:
            control_id: str - ID контрола

        Returns:
            QWidget or None - Виджет или None
        """
        cid_str = str(control_id).strip()

        # Особый случай: форма
        if cid_str in ("0", "form_root"):
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.allWidgets():
                if widget.__class__.__name__ == "FormDesigner" and hasattr(widget, 'runtime_form'):
                    return widget.runtime_form
            return None

        meta = self._registry.get(cid_str)
        if meta:
            ref = meta.get("widget_ref")
            return ref() if isinstance(ref, weakref.ref) else ref
        return None

    def get_meta_by_id(self, control_id):
        """
        Получение метаданных по control_id.

        Args:
            control_id: str - ID контрола

        Returns:
            dict or None - Метаданные или None
        """
        return self._registry.get(str(control_id))

    def get_all_ids(self):
        """
        Возвращает список всех зарегистрированных control_id.

        Returns:
            list[str] - Список всех control_id
        """
        return list(self._registry.keys())

    def clear(self):
        """Полная очистка всех структур реестра."""
        self._registry.clear()
        self._wid_to_cid_map.clear()
        self._index_by_path.clear()
        print("[FormObjectsRegistry] Реестр полностью очищен.")

    def clear_registry(self):
        """Алиас для clear()."""
        self.clear()