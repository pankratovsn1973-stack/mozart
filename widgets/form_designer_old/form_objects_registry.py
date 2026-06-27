# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_objects_registry.py

import uuid
import weakref


class FormObjectsRegistry:
    """Глобальный реестр визуальных объектов на холсте дизайнера.
    Реализует Unit of Work метаданные (full_path, calias) + защитные барьеры."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FormObjectsRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._registry = {}
            cls._instance._index_by_path = {}  # Key: (parent_id, calias), Value: id(widget)
        return cls._instance

    def register_object(self, widget_obj, parent_container_id=None, explicit_id=None,
                        full_path="", calias=""):
        """Регистрирует объект в памяти. Ключ поиска - уникальный calias."""
        if not widget_obj:
            return "form_root"

        # ✅ ЖЕСТКИЙ СИСТЕМНЫЙ БАРЬЕР: Запрещаем регистрировать фон и заголовки
        class_name = widget_obj.__class__.__name__
        if class_name in ("FormBackground", "QLabel"):
            obj_name = getattr(widget_obj, "objectName", lambda: "")()
            # Разрешаем только внутренние элементы референсов
            if obj_name not in ("lbl_of_ref", "txt_of_ref") and \
                    (class_name == "FormBackground" or
                     (hasattr(widget_obj, 'parent') and widget_obj.parent() and
                      widget_obj.parent().__class__.__name__ == "FormBackground")):
                return "form_root"

        wid = id(widget_obj)
        # ✅ ДИАГНОСТИКА
        print(
            f"[REG_DIAG] register_object: wid={wid}, calias='{calias}', parent_container_id={parent_container_id}, explicit_id={explicit_id}, full_path='{full_path}'")

        # Если ID не передан явно, генерируем временный отрицательный или UUID
        if explicit_id is None or str(explicit_id).strip() == '':
            explicit_id = str(uuid.uuid4())[:8]

        control_id = str(explicit_id)

        # Уникализация objectName для Qt (чтобы не было коллизий имен внутри формы)
        unique_qt_name = f"{calias}_{control_id}" if calias else f"control_{control_id}"
        if widget_obj.objectName() != unique_qt_name:
            widget_obj.setObjectName(unique_qt_name)

        # Присваиваем calias как бизнес-атрибут виджету
        if calias:
            widget_obj.calias = calias

        # Обновляем или создаем запись в основном словаре
        if wid in self._registry:
            meta = self._registry[wid]
            meta["control_id"] = control_id
            if full_path: meta["full_path"] = full_path
            if calias: meta["calias"] = calias
            if parent_container_id: meta["parent_id"] = str(parent_container_id)
        else:
            meta = {
                "control_id": control_id,
                "parent_id": str(parent_container_id) if parent_container_id else None,
                "object_name": calias,
                "widget_ref": weakref.ref(widget_obj),
                "full_path": full_path,
                "calias": calias
            }
            self._registry[wid] = meta

        # ✅ ИНДЕКСАЦИЯ ПО ПУТИ (ParentID + Calias) для надежного поиска при клике
        if parent_container_id and calias:
            path_key = (str(parent_container_id), str(calias))
            self._index_by_path[path_key] = wid

        print(
            f"[REGISTER_DIAG] register_object: calias={calias}, parent_container_id={parent_container_id}, explicit_id={explicit_id}")

        # Индексация по пути
        if parent_container_id and calias:
            path_key = (str(parent_container_id), str(calias))
            self._index_by_path[path_key] = wid
            print(f"[REGISTER_DIAG] Индекс добавлен: {path_key} -> {wid}")
        else:
            print(f"[REGISTER_DIAG] Индекс НЕ добавлен: parent_container_id={parent_container_id}, calias={calias}")

        return control_id

    def get_meta_by_widget(self, widget_obj):
        """Поиск метаданных через уникальное свойство .calias виджета."""
        if not widget_obj:
            return None

        # 1. Прямой поиск по id(widget)
        wid = id(widget_obj)
        meta = self._registry.get(wid)

        if meta:
            ref = meta.get("widget_ref")
            actual_ref = ref() if isinstance(ref, weakref.ref) else ref
            if actual_ref is widget_obj:
                return meta

        # 2. Поиск по calias (FALLBACK при изменении id или пересоздании)
        widget_calias = getattr(widget_obj, 'calias', None)

        if widget_calias:
            for existing_wid, m in self._registry.items():
                if m.get("calias") == widget_calias:
                    ref = m.get("widget_ref")
                    actual_ref = ref() if isinstance(ref, weakref.ref) else ref
                    if actual_ref is widget_obj or actual_ref is None:
                        return m

        # 3. Поиск через прокси (QGraphicsProxyWidget <-> QWidget)
        for obj_ptr, m in self._registry.items():
            ref = m.get("widget_ref")
            actual_ref = ref() if isinstance(ref, weakref.ref) else ref

            if actual_ref is None:
                continue

            if hasattr(actual_ref, 'widget') and callable(actual_ref.widget) and actual_ref.widget() == widget_obj:
                return m
            if hasattr(widget_obj, 'widget') and callable(widget_obj.widget) and widget_obj.widget() == actual_ref:
                return m

        return None

    def get_meta_by_parent_and_calias(self, parent_id, calias):
        """КЛЮЧЕВОЙ МЕТОД: Поиск метаданных по ParentID и Calias.
        Используется при каскадном клике, когда id(widget) может не совпадать."""
        path_key = (str(parent_id), str(calias))
        print(f"[GET_META] Поиск по ключу: {path_key}")

        wid = self._index_by_path.get(path_key)
        print(f"[GET_META] Найден wid: {wid}")

        if wid:
            meta = self._registry.get(wid)
            if meta:
                print(f"[GET_META] Найдена meta: {meta}")
                ref = meta.get("widget_ref")
                print(f"[GET_META] widget_ref: {ref}")
                actual_ref = ref() if isinstance(ref, weakref.ref) else ref
                print(f"[GET_META] actual_ref: {actual_ref}")
                if actual_ref:
                    print(f"[GET_META] УСПЕХ! Возвращаем meta")
                    return meta
                else:
                    print(f"[GET_META] ПРОВАЛ: actual_ref is None (объект удален), но возвращаем meta")
                    # ✅ ВОЗВРАЩАЕМ meta ДАЖЕ ЕСЛИ actual_ref is None
                    return meta
            else:
                print(f"[GET_META] meta не найдена для wid={wid}")
        else:
            print(f"[GET_META] wid не найден в _index_by_path")
        return None

    def get_id_by_widget(self, widget_obj):
        """Интеллектуальный поиск ID с распознаванием пар прокси-виджет."""
        meta = self.get_meta_by_widget(widget_obj)
        return meta["control_id"] if meta else "unknown"

    def get_widget_by_id(self, control_id):
        """Возвращает инстанс объекта по его строковому ID."""
        cid_str = str(control_id).strip()
        if cid_str in ("0", "form_root"):
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.allWidgets():
                if widget.__class__.__name__ == "FormDesigner" and hasattr(widget, 'runtime_form'):
                    return widget.runtime_form

        for obj_ptr, meta in self._registry.items():
            if meta["control_id"] == cid_str:
                ref = meta.get("widget_ref")
                actual_ref = ref() if isinstance(ref, weakref.ref) else ref
                if actual_ref:
                    return actual_ref
        return None

    def clear(self):
        """Полная зачистка реестра."""
        self._registry.clear()
        self._index_by_path.clear()

    def clear_registry(self):
        self.clear()