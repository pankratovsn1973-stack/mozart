# -*- coding: utf-8 -*-
# core/object_property_collection.py
"""
Коллекция свойств ОДНОГО экземпляра объекта на сцене.
Пишет события в change_log при любом изменении модели.

Правила:
  - Индексация — только по ID (prop.id), не по имени.
  - Новые свойства получают уникальный отрицательный ID
    из CollectionManager.next_negative_id().
  - Уникальность имени в пределах родителя (одной коллекции).
  - Все мутаторы (set_value, set_property_meta, rename_property,
    remove_override, set_property_delete, set_blob, add_property)
    пишут ChangeEvent.
"""
from datetime import datetime
from typing import Dict, List, Optional, Set

from core.change_log import change_log, ChangeEvent
from core.object_property import ObjectProperty
import os

from core.constants import LEGACY_LOG_FILENAME

_legacy_logged: Set[str] = set()


class ObjectPropertyCollection:
    """objpropcol экземпляра объекта сцены."""

    def __init__(self, element_id: int, collection_manager=None):
        self.element_id = element_id
        self._collection_manager = collection_manager
        self._items: Dict[str, ObjectProperty] = {}

    # ------------------------------------------------------------------
    # Наполнение
    # ------------------------------------------------------------------
    def add(self, prop: ObjectProperty):
        existing = self._items.get(prop.cname)
        if existing is None or prop.order < existing.order:
            self._items[prop.cname] = prop

    @classmethod
    def from_raw_rows(cls, element_id: int, rows: List[tuple],
                      collection_manager=None) -> "ObjectPropertyCollection":
        """
        Сборка коллекции свойств из сырых строк f_build_objpropcol (20 колонок).

        v9 FIX (уникальность отрицательных DB-ID):
        SQL больше НЕ нумерует Qt-мосты (-1, -2, -3...). Для них приходит NULL.
        Любой не-положительный / отсутствующий id трактуется как «нет физической
        строки в class_version_properties» и получает уникальный отрицательный
        DB-ID из единого счётчика CollectionManager.next_negative_db_id().
        Это гарантирует отсутствие коллизий DB-ID между разными элементами сцены.

        is_from_qt = True, если свойство пришло из моста
        (defined_in_version_id IS NULL), иначе False.
        """
        col = cls(element_id, collection_manager)

        for r in rows:
            def _get(idx, default=None):
                return r[idx] if len(r) > idx else default

            # --- BLOB: bytes / bytearray / base64-строка -------------------
            raw_blob = _get(16)
            blob_value: Optional[bytes] = None
            if raw_blob is not None:
                if isinstance(raw_blob, (bytes, bytearray)):
                    blob_value = bytes(raw_blob)
                elif isinstance(raw_blob, str):
                    import base64
                    try:
                        blob_value = base64.b64decode(raw_blob)
                    except Exception:
                        blob_value = raw_blob.encode('utf-8')

            # --- DB-ID: только положительный считаем реальным --------------
            raw_id = _get(0)
            try:
                real_id = int(raw_id) if raw_id is not None else None
            except (TypeError, ValueError):
                real_id = None

            if real_id is not None and real_id > 0:
                prop_id = real_id
            else:
                prop_id = (collection_manager.next_negative_db_id()
                           if collection_manager is not None else -1)

            # --- Происхождение: мост Qt или строка ERP --------------------
            defined_in = _get(10)
            is_from_qt = (defined_in is None)

            col.add(ObjectProperty(
                id=prop_id,
                cname=_get(1),
                order=_get(2, 1),
                value=str(_get(3)) if _get(3) is not None else "",
                typevalue=_get(4, 0) if _get(4) is not None else 0,
                sourcevalue=_get(5),
                typesourcevalue=_get(6),
                fuuncselectionvalue=_get(7),
                bridgecalcset=_get(8),
                bridgecalcget=_get(9),
                defined_in_version_id=defined_in,
                ui_label_ru=_get(11),
                editor_type=_get(12),
                qt_target=_get(13),
                translation_strategy=_get(14),
                isdefaultepr=_get(15),
                blob_value=blob_value,
                is_blob=bool(_get(17, False)),
                blob_name=_get(18),
                owner_version_id=_get(19),
                is_from_qt=is_from_qt,
            ))

        return col

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------
    def get(self, cname: str) -> Optional[ObjectProperty]:
        return self._items.get(cname)

    def all_ordered(self) -> List[ObjectProperty]:
        return sorted(self._items.values(), key=lambda p: (p.order, p.cname))

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, cname: str) -> bool:
        return cname in self._items

    # ------------------------------------------------------------------
    # Новое свойство
    # ------------------------------------------------------------------
    def add_property(self, cname: str, source: str = "user_edit",
                     **meta) -> Optional[ObjectProperty]:
        """
        Добавляет НОВОЕ собственное свойство элемента (order=1).
        Уникальность имени — в пределах родителя: если cname занят, вернуть None.

        v9 FIX (идентичность):
        - DB-ID берётся из CollectionManager.next_negative_db_id()
          (метода next_negative_id НЕ существует — был AttributeError при ➕);
        - выдаётся сквозной id_col и объект регистрируется в общем индексе
          менеджера как IDCOL_KIND_PROP. Без этого свойство было невидимо
          для get_property_by_id_col / реактива / Inspector;
        - owner_element_id = self.element_id (DB-ID владельца) — по нему
          менеджер находит графику и применяет SET-бридж.

        v9 FIX (флаги):
        isDirty / is_changed / is_property_changed = True сразу при создании,
        иначе get_changed_properties() пусто и свойство не сохраняется в БД.

        Метаданные фильтруются по полям ObjectProperty и нормализуются
        ('' → None для строк, int для typevalue, bool для isdefaultepr/is_blob),
        чтобы диалог 📝 не ронял конструктор и не писал мусор в БД.

        В ChangeEvent пробрасывается id_col → Inspector обновляет узел точечно.
        """
        from dataclasses import fields as _dc_fields
        from core.constants import IDCOL_KIND_PROP

        cname = (cname or "").strip()
        if not cname:
            return None
        if cname in self._items:
            return None

        mgr = self._collection_manager

        # --- Идентичность: DB-ID + idCol ---------------------------------
        new_db_id = mgr.next_negative_db_id() if mgr is not None else -1

        # --- Значение ----------------------------------------------------
        raw_value = meta.pop('value', '')
        value = str(raw_value) if raw_value is not None else ""

        # --- Фильтрация и нормализация метаданных ------------------------
        allowed_fields = {f.name for f in _dc_fields(ObjectProperty)}
        reserved = {'id', 'cname', 'order', 'value',
                    'id_col', 'owner_element_id'}
        nullable_str = {
            'ui_label_ru', 'editor_type', 'qt_target', 'translation_strategy',
            'bridgecalcset', 'bridgecalcget', 'fuuncselectionvalue',
            'typesourcevalue', 'sourcevalue', 'blob_name',
        }

        clean_meta = {}
        for key, val in meta.items():
            if key not in allowed_fields or key in reserved:
                continue
            if key in nullable_str:
                if isinstance(val, str):
                    val = val.strip() or None
            elif key in ('isdefaultepr', 'is_blob'):
                val = bool(val) if val is not None else None
            elif key == 'typevalue':
                try:
                    val = int(val) if val is not None else 0
                except (TypeError, ValueError):
                    val = 0
            clean_meta[key] = val

        prop = ObjectProperty(
            id=new_db_id,
            cname=cname,
            order=1,                 # всегда собственное, не унаследованное
            value=value,
            **clean_meta
        )

        # --- Флаги жизненного цикла --------------------------------------
        prop.isInherited = False
        prop.isDelete = False
        prop.is_deleted = False
        prop.is_from_qt = False
        prop.defined_in_version_id = None
        prop.isDirty = True
        prop.is_changed = True
        prop.is_property_changed = True

        # --- Регистрация в коллекции и общем индексе idCol ---------------
        self._items[cname] = prop

        if mgr is not None:
            prop.id_col = mgr.next_id_col()
            prop.owner_element_id = self.element_id
            mgr.register_idcol(prop, IDCOL_KIND_PROP)
        else:
            prop.id_col = 0
            prop.owner_element_id = self.element_id

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_add',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value=None,
            new_value=prop.id,
            source=source,
            extra={'value': value, 'meta': clean_meta},
            id_col=prop.id_col,
        ))
        return prop
    # ------------------------------------------------------------------
    # Внесение значения
    # ------------------------------------------------------------------
    def set_value(self, cname: str, new_value: str,
                  source: str = "manual", silent: bool = False) -> bool:
        """
        Меняет значение свойства в МОДЕЛИ и пишет change_log.

        SET-бридж в виджет НЕ вызывается — это ответственность:
          - CollectionManager.update_property_value_by_id_col,
          - либо прямого apply_property_to_widget (фаза 2 загрузки).

        v9 FIX (флаги изменений):
        get_changed_properties() / get_changed_property_meta() отбирают строки
        по isDirty. Раньше set_value его не выставлял → сохранение в БД было
        пустым при визуально «изменённых» свойствах. Теперь любая фиксация
        нового значения выставляет isDirty + is_changed + is_property_changed.

        Исключение — НЕ пользовательские источники ('init', 'silent',
        'auto_sync'): они синхронизируют модель с реальностью, а не выражают
        правку аналитика. Для них dirty НЕ ставится, иначе каждый init
        подстановки myx/myy/mywidth/myheight уезжал бы в БД как изменение.
        Значение и change_log при этом пишутся всегда.

        silent=True ИЛИ manager.is_silent() → effective_source='silent'
        (подавляется только UI-реактивность и SET-бридж, но не факт правки).
        """
        prop = self._items.get(cname)
        if prop is None:
            return False

        new_str = str(new_value) if new_value is not None else ""
        if prop.value == new_str:
            return False

        old_value = prop.value
        prop.value = new_str

        # --- Источник: silent имеет приоритет над переданным ---------------
        effective_source = source
        if silent:
            effective_source = 'silent'
        elif (self._collection_manager is not None
              and self._collection_manager.is_silent()):
            effective_source = 'silent'

        # --- Флаг правки: только от пользователя --------------------------
        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True
            # Правка значения «оживляет» ранее сброшенное свойство
            if getattr(prop, 'isDelete', False):
                prop.isDelete = False
                prop.is_deleted = False

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_value',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value=old_value,
            new_value=new_str,
            source=effective_source,
            id_col=getattr(prop, 'id_col', None),
        ))
        return True

    def set_value_by_idcol(self, id_col: int, new_value,
                           source: str = "user_edit",
                           silent: bool = False) -> bool:
        """
        Атомарный сеттер значения по idCol свойства. Делегирует в set_value.

        v9 FIX (единый контракт с CollectionManager):
        Раньше метод не проверял GEOMETRY_PROPS / ALLOWED_GEOMETRY_SOURCES,
        хотя менеджер это делает. Прямой вызов коллекционного сеттера обходил
        запрет и менял myx/myy/mywidth/myheight из таблицы, минуя сцену.
        Теперь правило одно на оба входа: геометрия — только 'vizivig'/'init'.

        v9 FIX (STRICT IDCOL + O(1)):
        Поиск через manager.get_property_by_id_col (kind == IDCOL_KIND_PROP)
        вместо линейного перебора _items.values(). Дополнительно проверяется
        принадлежность: prop.owner_element_id == self.element_id. Без этого
        метод мог изменить свойство ЧУЖОГО элемента и записать ChangeEvent
        с неверным element_id.
        Без менеджера — локальный fallback по _items (обратная совместимость).

        v9 FIX (флаги):
        Правка значения снимает маркер удаления (isDelete/is_deleted), чтобы
        поведение совпадало с set_value и с кнопкой «×» в таблице. Сам dirty
        выставляет set_value по источнику ('init'/'silent'/'auto_sync' — не ставят).

        silent=True пробрасывается в set_value → effective_source='silent',
        UI-реактивность подавляется, значение и change_log пишутся.

        SET-бридж НЕ вызывается — это ответственность менеджера
        (update_property_value_by_id_col) или фазы 2 загрузки.
        """
        from core.constants import GEOMETRY_PROPS, ALLOWED_GEOMETRY_SOURCES

        if not id_col or id_col <= 0:
            return False

        # --- Поиск объекта: индекс менеджера, иначе локальный fallback ----
        prop = None
        mgr = self._collection_manager
        if mgr is not None:
            prop = mgr.get_property_by_id_col(id_col)
        else:
            for p in self._items.values():
                if getattr(p, 'id_col', None) == id_col:
                    prop = p
                    break

        if prop is None:
            return False

        # --- Принадлежность: свойство должно быть НАШЕГО элемента ---------
        owner_db_id = getattr(prop, 'owner_element_id', None)
        if owner_db_id is not None and owner_db_id != self.element_id:
            print(f"[OPC] Отказ: idCol={id_col} ('{prop.cname}') принадлежит "
                  f"элементу {owner_db_id}, а не {self.element_id}")
            return False

        # --- Запрет геометрии вне сцены ----------------------------------
        if (prop.cname in GEOMETRY_PROPS
                and source not in ALLOWED_GEOMETRY_SOURCES):
            print(f"[OPC] Отказ: '{prop.cname}' нельзя менять "
                  f"source='{source}' — только со сцены (визивиг)")
            return False

        # --- Правка значения «оживляет» сброшенное свойство ---------------
        if getattr(prop, 'isDelete', False):
            prop.isDelete = False
            prop.is_deleted = False

        return self.set_value(prop.cname, new_value,
                              source=source, silent=silent)

    def set_property_delete_by_idcol(self, id_col: int, is_deleted: bool = True,
                                     source: str = "user_edit") -> bool:
        """
        Установка/снятие маркера удаления свойства по idCol. Делегирует в
        set_property_delete — единственную реализацию операции в проекте.

        v9 FIX (делегирование):
        Раньше метод писал isDelete/is_deleted/is_changed/isDirty напрямую
        через setattr и слал ChangeEvent с old_value=None/new_value=None
        и источником 'user_edit_delete', которого нет ни в одном контракте
        источников. Теперь вся логика в set_property_delete:
          • атомарная запись isDelete + is_deleted (без рассинхрона);
          • isDirty → попадание в get_changed_properties() → dt_end в БД;
          • идемпотентность (повторный вызов не плодит событий);
          • extra.physical_row / defined_in_version_id / owner_version_id;
          • extra.restored=True при снятии флага;
          • реальное прежнее значение флага в old_value.

        v9 FIX (STRICT IDCOL + O(1)):
        Поиск через manager.get_property_by_id_col (kind == IDCOL_KIND_PROP)
        вместо перебора _items.values(). Метод/сигнал/элемент сюда не пройдут.
        Дополнительно проверяется принадлежность: prop.owner_element_id ==
        self.element_id — иначе можно было изменить свойство ЧУЖОГО элемента
        и записать ChangeEvent с неверным element_id.
        Без менеджера — локальный fallback по _items (обратная совместимость).

        Значение value НЕ трогается: при is_deleted=False прежняя правка
        восстанавливается как была. Очистка значения — отдельная операция «×».

        SET-бридж не вызывается: это операция модели, а не команда виджету.
        """
        if not id_col or id_col <= 0:
            return False

        # --- Поиск объекта: индекс менеджера, иначе локальный fallback ----
        prop = None
        mgr = self._collection_manager
        if mgr is not None:
            prop = mgr.get_property_by_id_col(id_col)
        else:
            for p in self._items.values():
                if getattr(p, 'id_col', None) == id_col:
                    prop = p
                    break

        if prop is None:
            return False

        # --- Принадлежность: свойство должно быть НАШЕГО элемента ---------
        owner_db_id = getattr(prop, 'owner_element_id', None)
        if owner_db_id is not None and owner_db_id != self.element_id:
            print(f"[OPC] Отказ: idCol={id_col} ('{prop.cname}') принадлежит "
                  f"элементу {owner_db_id}, а не {self.element_id}")
            return False

        return self.set_property_delete(prop.cname, bool(is_deleted),
                                        source=source)


# ------------------------------------------------------------------
    # Переопределения МЕТАДАННЫХ
    # ------------------------------------------------------------------
    def set_property_meta(self, cname: str, source: str = "user_edit",
                          **kwargs) -> bool:
        """
        Устанавливает переопределения МЕТАДАННЫХ свойства. Пишет prop_meta.
        Переименование — только через rename_property.

        v9 FIX (флаги изменений):
        get_changed_property_meta() отбирает строки по isDirty. Раньше флаг
        не выставлялся → переопределения метаданных не сохранялись в БД,
        хотя Inspector показывал новые значения. Теперь любая реальная правка
        метаданных ставит isDirty + is_changed + is_property_changed.

        v9 FIX (STRICT IDCOL):
        В ChangeEvent пробрасывается id_col=prop.id_col. Без него
        _on_model_changed_reactive уходил в fallback по DB-ID, а
        DebugCollectionInspector пропускал событие 'prop_meta' целиком.

        Нормализация: пустая строка / пробелы для строковых метаданных = None
        (в БД и в мостах «не задано» — это NULL). Иначе сравнение '' != None
        давало ложное «изменение» при каждом открытии диалога 📝.

        source='init'/'silent'/'auto_sync' → значение пишется, dirty НЕ ставится.
        Значение свойства (value) здесь НЕ трогается — только метаданные.
        """
        prop = self._items.get(cname)
        if prop is None:
            return False

        allowed = {
            'ui_label_ru', 'editor_type', 'qt_target', 'translation_strategy',
            'bridgecalcset', 'bridgecalcget', 'fuuncselectionvalue',
            'typevalue', 'isdefaultepr', 'is_blob', 'typesourcevalue',
        }
        # Поля, где пустая строка эквивалентна NULL
        nullable_str = {
            'ui_label_ru', 'editor_type', 'qt_target', 'translation_strategy',
            'bridgecalcset', 'bridgecalcget', 'fuuncselectionvalue',
            'typesourcevalue',
        }

        old_meta = {k: getattr(prop, k, None) for k in allowed}
        changed_keys = []

        for key, val in kwargs.items():
            if key not in allowed:
                continue

            # --- Нормализация типов -------------------------------------
            if key in nullable_str:
                if isinstance(val, str):
                    val = val.strip() or None
            elif key in ('isdefaultepr', 'is_blob'):
                val = bool(val) if val is not None else None
            elif key == 'typevalue':
                try:
                    val = int(val) if val is not None else None
                except (TypeError, ValueError):
                    continue

            if getattr(prop, key, None) != val:
                setattr(prop, key, val)
                changed_keys.append(key)

        if not changed_keys:
            return False

        # --- Источник и флаг правки ------------------------------------
        effective_source = source
        if (self._collection_manager is not None
                and self._collection_manager.is_silent()):
            effective_source = 'silent'

        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True
            # Правка метаданных «оживляет» ранее сброшенное переопределение
            if getattr(prop, 'isDelete', False):
                prop.isDelete = False
                prop.is_deleted = False

        new_meta = {k: getattr(prop, k, None) for k in allowed}

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_meta',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value={k: old_meta[k] for k in changed_keys},
            new_value={k: new_meta[k] for k in changed_keys},
            source=effective_source,
            extra={'rename': False, 'changed_keys': changed_keys},
            id_col=getattr(prop, 'id_col', None),
        ))
        return True

    def rename_property(self, old_cname: str, new_cname: str,
                        source: str = "user_edit") -> bool:
        """
        Переименовать собственное свойство. prop.id и prop.id_col НЕ меняются —
        идентичность объекта сохраняется, меняется только ключ в _items.
        Пишет prop_meta с extra.rename=True.

        v9 FIX (флаги изменений):
        get_changed_properties() / get_changed_property_meta() отбирают по
        isDirty. Раньше флаг не ставился → переименование не уезжало в БД:
        в UI новое имя, в class_version_properties прежнее c_name.

        v9 FIX (защита линии крови):
        Унаследованное переименовывать нельзя — это откажет триггер
        fn_protect_prop_name уже на UPDATE, откатив всю транзакцию сохранения.
        Отказываем ДО правки модели по трём признакам:
          • order > 1                     — пришло от ERP-предка;
          • is_from_qt / defined_in IS NULL — пришло из Qt-моста;
          • owner_version_id != element_id  — владелец другая версия.
        Проверка «есть ли потомки» остаётся в PropertyMetaEditDialog
        (has_children) — коллекция о соседних классах не знает.

        v9 FIX (STRICT IDCOL):
        В ChangeEvent пробрасывается id_col=prop.id_col → Inspector обновляет
        узел точечно, реактивный слот не падает в fallback по DB-ID.

        Нормализация: имя обрезается по пробелам; пустое / совпадающее /
        занятое имя → False без побочных эффектов.
        """
        prop = self._items.get(old_cname)
        if prop is None:
            return False

        new_cname = (new_cname or "").strip()
        if not new_cname or new_cname == old_cname:
            return False
        if new_cname in self._items:
            return False

        # --- Защита унаследованного / мостового имени --------------------
        is_inherited = (
            (getattr(prop, 'order', 1) or 1) > 1
            or bool(getattr(prop, 'is_from_qt', False))
            or getattr(prop, 'defined_in_version_id', None) is None
        )
        owner_vid = getattr(prop, 'owner_version_id', None)
        if not is_inherited and owner_vid is not None and self.element_id > 0:
            is_inherited = (owner_vid != self.element_id)

        if is_inherited:
            print(f"[OPC] Отказ: '{old_cname}' унаследовано — "
                  f"переименование запрещено (fn_protect_prop_name). "
                  f"Создайте собственное свойство или переопределите метаданные.")
            return False

        # --- Перекладываем ключ, идентичность сохраняем ------------------
        self._items.pop(old_cname)
        prop.cname = new_cname
        self._items[new_cname] = prop

        # --- Источник и флаг правки --------------------------------------
        effective_source = source
        if (self._collection_manager is not None
                and self._collection_manager.is_silent()):
            effective_source = 'silent'

        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True
            # Переименование «оживляет» ранее сброшенное свойство
            if getattr(prop, 'isDelete', False):
                prop.isDelete = False
                prop.is_deleted = False

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_meta',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=new_cname,
            old_value=old_cname,
            new_value=new_cname,
            source=effective_source,
            extra={'rename': True, 'old_cname': old_cname},
            id_col=getattr(prop, 'id_col', None),
        ))
        return True
    # ------------------------------------------------------------------
    # Удаление (пометка)
    # ------------------------------------------------------------------
    def remove_override(self, cname: str, source: str = "user_edit") -> bool:
        """
        Помечает переопределение свойства на удаление (isDelete=True).
        Узел остаётся в _items — физическое удаление запрещено триггером
        fn_protect_prop_name для унаследованных свойств.

        v9 FIX (флаги изменений):
        get_changed_properties() отбирает по isDirty OR isDelete, но
        _save_properties_for_version проверяет dirty-флаги. Раньше isDirty
        не ставился → dt_end в class_version_properties не проставлялся,
        хотя Inspector показывал «(удалено)». Теперь ставятся
        isDirty + is_changed + is_property_changed + is_deleted.

        v9 FIX (STRICT IDCOL):
        В ChangeEvent пробрасывается id_col=prop.id_col. Без него
        DebugCollectionInspector пропускал 'prop_delete', а реактивный
        слот _on_model_changed_reactive падал в fallback по DB-ID.

        Различаем два случая (extra.physical_row):
          • defined_in_version_id / prop.id > 0 → есть физическая строка
            в class_version_properties → при сохранении закрываем dt_end;
          • свойство из Qt-моста (id < 0, defined_in_version_id IS NULL) →
            закрывать нечего, это лишь подавление значения в модели.

        Значение value НЕ очищается: после отмены удаления (set_value /
        set_property_delete(False)) прежняя правка должна восстановиться.
        Очистка значения — отдельная операция «×» (update_property_value_by_id_col).
        """
        prop = self._items.get(cname)
        if prop is None:
            return False

        if getattr(prop, 'isDelete', False):
            # Уже помечено — идемпотентно, без повторного события
            return True

        old_flag = False
        prop.isDelete = True
        prop.is_deleted = True

        # --- Есть ли физическая строка в БД -----------------------------
        defined_in = getattr(prop, 'defined_in_version_id', None)
        has_physical_row = bool(
            (defined_in is not None and defined_in > 0)
            or (getattr(prop, 'id', 0) or 0) > 0
        )

        # --- Источник и флаг правки --------------------------------------
        effective_source = source
        if (self._collection_manager is not None
                and self._collection_manager.is_silent()):
            effective_source = 'silent'

        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_delete',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value=old_flag,
            new_value=True,
            source=effective_source,
            extra={
                'physical_row': has_physical_row,
                'defined_in_version_id': defined_in,
                'owner_version_id': getattr(prop, 'owner_version_id', None),
            },
            id_col=getattr(prop, 'id_col', None),
        ))
        return True
    def set_property_delete(self, cname: str, flag: bool = True,
                            source: str = "user_edit") -> bool:
        """
        Явная установка маркера удаления переопределения (isDelete).
        Узел остаётся в _items — физическое DELETE запрещён триггером
        fn_protect_prop_name для унаследованных свойств.

        Парный к remove_override: тот всегда ставит True, этот умеет и снимать.

        v9 FIX (синхрон флагов):
        Раньше менялся только isDelete, а legacy is_deleted оставался прежним.
        Inspector и SQL-preview читают (isDelete OR is_deleted) → после отмены
        строка продолжала показываться «(удалено)». Теперь оба флага пишутся
        атомарно, плюс is_changed / is_property_changed.

        v9 FIX (флаги изменений):
        Отмена удаления — тоже правка, которую надо донести до БД
        (вернуть значение / снять dt_end). Ставится isDirty, иначе
        get_changed_properties() её не видит и в БД остаётся закрытая строка.

        v9 FIX (STRICT IDCOL):
        В ChangeEvent пробрасывается id_col=prop.id_col → Inspector красит
        узел точечно, реактивный слот не падает в fallback по DB-ID.

        extra.physical_row: есть ли строка в class_version_properties.
        У свойства из Qt-моста (id < 0, defined_in_version_id IS NULL)
        закрывать/открывать нечего — это подавление значения в модели.

        Значение value НЕ трогается: при flag=False прежняя правка
        восстанавливается как была. Очистка значения — отдельная операция «×».

        source='init'/'silent'/'auto_sync' → флаг пишется, dirty НЕ ставится.
        """
        prop = self._items.get(cname)
        if prop is None:
            return False

        flag = bool(flag)
        old_flag = bool(getattr(prop, 'isDelete', False))
        old_legacy = bool(getattr(prop, 'is_deleted', False))

        # Нет реальной правки: основной флаг уже нужный и legacy не рассинхронен
        if old_flag == flag and old_legacy == flag:
            return False

        # --- Атомарная запись обоих флагов -------------------------------
        prop.isDelete = flag
        prop.is_deleted = flag

        # --- Есть ли физическая строка в БД -----------------------------
        defined_in = getattr(prop, 'defined_in_version_id', None)
        has_physical_row = bool(
            (defined_in is not None and defined_in > 0)
            or (getattr(prop, 'id', 0) or 0) > 0
        )

        # --- Источник и флаг правки --------------------------------------
        effective_source = source
        if (self._collection_manager is not None
                and self._collection_manager.is_silent()):
            effective_source = 'silent'

        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_delete',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value=old_flag,
            new_value=flag,
            source=effective_source,
            extra={
                'physical_row': has_physical_row,
                'defined_in_version_id': defined_in,
                'owner_version_id': getattr(prop, 'owner_version_id', None),
                'restored': (old_flag and not flag),
            },
            id_col=getattr(prop, 'id_col', None),
        ))
        return True
    # ------------------------------------------------------------------
    # BLOB
    # ------------------------------------------------------------------
    def set_blob(self, cname: str, blob_data: Optional[bytes],
                 blob_name: str = "", source: str = "user_edit") -> bool:
        """
        Устанавливает / сбрасывает BLOB свойства. Пишет prop_blob.

        blob_data=None (или пустые байты) → сброс:
            blob_value=None, blob_name=None, is_blob=False.

        v9 FIX (флаги изменений):
        get_changed_properties() отбирает по isDirty. Раньше флаг не ставился
        ни при загрузке картинки, ни при её удалении → blob_value в БД не
        обновлялся вообще. Теперь любая реальная правка блоба ставит
        isDirty + is_changed + is_property_changed.

        v9 FIX (STRICT IDCOL):
        В ChangeEvent пробрасывается id_col=prop.id_col. Без него
        DebugCollectionInspector пропускал событие 'prop_blob' целиком
        (ветка требует event.id_col is not None), а реактивный слот уходил
        в fallback по DB-ID.

        Значение value (c_value) здесь НЕ трогается: для image-свойств оно
        хранит отображаемое имя файла и приходит отдельно из select_image_dialog
        через update_property_value_by_id_col.

        source='init'/'silent'/'auto_sync' → блоб пишется, dirty НЕ ставится.
        """
        prop = self._items.get(cname)
        if prop is None:
            return False

        # --- Нормализация входа ------------------------------------------
        data: Optional[bytes] = None
        if blob_data is not None:
            if isinstance(blob_data, (bytes, bytearray, memoryview)):
                data = bytes(blob_data)
            elif isinstance(blob_data, str):
                data = blob_data.encode('utf-8')
            else:
                try:
                    data = bytes(blob_data)
                except (TypeError, ValueError):
                    return False
            if not data:          # b'' трактуем как сброс
                data = None

        old_info = {
            'is_blob': bool(getattr(prop, 'is_blob', False)),
            'blob_name': getattr(prop, 'blob_name', None),
            'blob_size': len(prop.blob_value) if prop.blob_value else 0,
        }

        # --- Нет реальной правки → выходим -------------------------------
        new_name = (blob_name or "").strip() or None if data is not None else None
        if data is None:
            if not old_info['is_blob'] and prop.blob_value is None:
                return False
        else:
            if (old_info['is_blob']
                    and prop.blob_value == data
                    and (getattr(prop, 'blob_name', None) or None) == new_name):
                return False

        # --- Применение --------------------------------------------------
        if data is None:
            prop.blob_value = None
            prop.blob_name = None
            prop.is_blob = False
        else:
            prop.blob_value = data
            prop.blob_name = new_name or ""
            prop.is_blob = True

        new_info = {
            'is_blob': bool(prop.is_blob),
            'blob_name': prop.blob_name,
            'blob_size': len(prop.blob_value) if prop.blob_value else 0,
        }

        # --- Источник и флаг правки --------------------------------------
        effective_source = source
        if (self._collection_manager is not None
                and self._collection_manager.is_silent()):
            effective_source = 'silent'

        _NON_USER_SOURCES = {'init', 'silent', 'auto_sync'}
        if effective_source not in _NON_USER_SOURCES:
            prop.isDirty = True
            prop.is_changed = True
            prop.is_property_changed = True
            # Загрузка новой картинки «оживляет» сброшенное свойство
            if data is not None and getattr(prop, 'isDelete', False):
                prop.isDelete = False
                prop.is_deleted = False

        change_log.record(ChangeEvent(
            timestamp=datetime.now(),
            kind='prop_blob',
            element_id=self.element_id,
            target_id=prop.id,
            target_name=cname,
            old_value=old_info,
            new_value=new_info,
            source=effective_source,
            extra={'reset': data is None},
            id_col=getattr(prop, 'id_col', None),
        ))
        return True

    # ------------------------------------------------------------------
    # Трансляция в Qt и обратно
    # ------------------------------------------------------------------
    def apply_to_widget(self, widget, bridge_manager,
                        prop_names: Optional[List[str]] = None):
        """Применяет значения к живому Qt-виджету. isDelete — пропускаем."""
        for prop in self.all_ordered():
            if prop_names is not None and prop.cname not in prop_names:
                continue
            if getattr(prop, 'isDelete', False):
                continue
            if not prop.value and not prop.is_blob:
                continue
            bridge_manager.apply_property_to_widget(widget, prop)

    def read_from_widget(self, widget, bridge_manager,
                         prop_names: Optional[List[str]] = None):
        """
        Читает значения из живого Qt-виджета. Пишет через set_value,
        чтобы попасть в change_log.
        """
        for prop in self.all_ordered():
            if prop_names is not None and prop.cname not in prop_names:
                continue
            if not prop.bridgecalcget:
                continue
            new_val = bridge_manager.read_property_from_widget(widget, prop)
            if new_val is not None and new_val != prop.value:
                self.set_value(prop.cname, new_val, source="auto_sync")

    # ------------------------------------------------------------------
    # Для сохранения
    # ------------------------------------------------------------------
    def get_changed_properties(self) -> List[ObjectProperty]:
        return [
            p for p in self.all_ordered()
            if getattr(p, 'isDirty', False) or getattr(p, 'isDelete', False)
        ]

    def get_changed_property_meta(self) -> List[ObjectProperty]:
        return [p for p in self.all_ordered() if getattr(p, 'isDirty', False)]

    def get_deleted_overrides(self) -> List[ObjectProperty]:
        return [p for p in self.all_ordered() if getattr(p, 'isDelete', False)]

    def get_all_with_blob(self) -> List[ObjectProperty]:
        return [p for p in self.all_ordered() if p.is_blob]

    def mark_saved(self):
        """После записи в БД — фиксируем новое initial_value / initial_meta."""
        for prop in self._items.values():
            prop.mark_saved()




