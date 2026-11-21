# Контекст проекта Mozart ERP

- **Корень:** `/home/sergey/Documents/configurate`
- **Сгенерирован:** 2026-10-25 21:29:32
- **Файлов:** 35


## Сводная статистика

| Показатель | Значение |
|------------|----------|
| Файлов | 35 |
| Классов | 41 |
| Методов/свойств | 354 |
| Функций | 31 |
| Строк кода | 8,996 |


## Оглавление

- [`base_manager.py`](#base-manager-py) — —
- [`composition_manager.py`](#composition-manager-py) — —
- [`constest.py`](#constest-py) — —
- [`core/bridge_function_registry.py`](#core-bridge-function-registry-py) — Реестр функций трансляции значений low-code свойств в Qt/Python и обратно.
- [`core/bridge_functions_builtin.py`](#core-bridge-functions-builtin-py) — Встроенные функции трансляции low-code свойств в Qt/Python и обратно.
- [`core/bridge_resolver.py`](#core-bridge-resolver-py) — BridgeResolver — трёхуровневый резолвер функций моста.
- [`core/class_registry.py`](#core-class-registry-py) — Глобальная Машина классов (Class Registry / Class Loader) платформы Mozart ERP.
- [`core/extend_bridges.py`](#core-extend-bridges-py) — Автономный скрипт расширения таблицы class_property_bridge.
- [`core/method_collection.py`](#core-method-collection-py) — Коллекция методов ОДНОГО экземпляра объекта на сцене (или класса).
- [`core/method_item.py`](#core-method-item-py) — Метаданные одного метода экземпляра объекта сцены (или класса).
- [`core/object_property.py`](#core-object-property-py) — Одна строка objpropcol — свойство экземпляра объекта на сцене.
- [`core/object_property_collection.py`](#core-object-property-collection-py) — Коллекция свойств ОДНОГО экземпляра объекта на сцене.
- [`core/property_bridge_manager.py`](#core-property-bridge-manager-py) — Менеджер декларативных мостов свойств (Property Bridge Manager) платформы Mozart ERP.
- [`core/superlibre.py`](#core-superlibre-py) — Библиотека SuperLibre — методы трансляции low-code свойств в Qt/Python и обратно,
- [`core/system_fields.py`](#core-system-fields-py) — Словарь вшитых полей сущностей Mozart ERP.
- [`core/virtual_class_node.py`](#core-virtual-class-node-py) — Модуль структуры скомпилированного low-code класса в оперативной памяти Конфигуратора.
- [`crud_buttons.py`](#crud-buttons-py) — —
- [`database.py`](#database-py) — —
- [`dialogs/__init__.py`](#dialogs---init---py) — Экспорт диалогов и утилит для работы с классами.
- [`dialogs/base_class_selector.py`](#dialogs-base-class-selector-py) — Диалог выбора базового класса при создании нового класса.
- [`dialogs/class_edit_dialog.py`](#dialogs-class-edit-dialog-py) — Главное окно редактирования структуры класса ERP.
- [`dialogs/class_group_edit_dialog.py`](#dialogs-class-group-edit-dialog-py) — —
- [`dialogs/class_group_manager_dialog.py`](#dialogs-class-group-manager-dialog-py) — —
- [`dialogs/collection_manager.py`](#dialogs-collection-manager-py) — Менеджер коллекции элементов сцены редактора классов.
- [`dialogs/methods_dialog.py`](#dialogs-methods-dialog-py) — Диалог управления методами класса (модальный).
- [`dialogs/select_entity_dialog.py`](#dialogs-select-entity-dialog-py) — Независимое модальное окно выбора сущности из meta.entitytypes.
- [`dialogs/select_field_dialog.py`](#dialogs-select-field-dialog-py) — Независимое модальное окно выбора поля.
- [`dialogs/signals_dialog.py`](#dialogs-signals-dialog-py) — Диалог управления сигналами класса.
- [`ide_core.py`](#ide-core-py) — —
- [`ide_db_work.py`](#ide-db-work-py) — —
- [`ide_field_edit.py`](#ide-field-edit-py) — —
- [`ide_main.py`](#ide-main-py) — Главный стартовый модуль интегрированной среды разработки (IDE) Mozart ERP.
- [`ide_ui_panels.py`](#ide-ui-panels-py) — Модуль предоставляет класс-примесь MozartIDEPanelsMixin.
- [`upload_to_gitverse.py`](#upload-to-gitverse-py) — Автономный скрипт для заливки всех .py файлов проекта напрямую на GitVerse через REST API.
- [`описание.py`](#описание-py) — Генератор структурированной документации проекта Mozart ERP.

## Сводная таблица файлов

| Файл | Строк | Классов | Функций | Роль |
|------|-------|---------|---------|------|
| `base_manager.py` | 90 | 1 | 0 | — |
| `composition_manager.py` | 92 | 1 | 0 | — |
| `constest.py` | 28 | 0 | 0 | — |
| `core/bridge_function_registry.py` | 83 | 2 | 0 | Реестр функций трансляции значений low-code свойств в Qt/Python и обратно. |
| `core/bridge_functions_builtin.py` | 290 | 0 | 22 | Встроенные функции трансляции low-code свойств в Qt/Python и обратно. |
| `core/bridge_resolver.py` | 238 | 1 | 0 | BridgeResolver — трёхуровневый резолвер функций моста. |
| `core/class_registry.py` | 205 | 1 | 0 | Глобальная Машина классов (Class Registry / Class Loader) платформы Mozart ERP. |
| `core/extend_bridges.py` | 198 | 0 | 1 | Автономный скрипт расширения таблицы class_property_bridge. |
| `core/method_collection.py` | 118 | 1 | 0 | Коллекция методов ОДНОГО экземпляра объекта на сцене (или класса). |
| `core/method_item.py` | 37 | 1 | 0 | Метаданные одного метода экземпляра объекта сцены (или класса). |
| `core/object_property.py` | 52 | 1 | 0 | Одна строка objpropcol — свойство экземпляра объекта на сцене. |
| `core/object_property_collection.py` | 132 | 1 | 0 | Коллекция свойств ОДНОГО экземпляра объекта на сцене. |
| `core/property_bridge_manager.py` | 278 | 1 | 0 | Менеджер декларативных мостов свойств (Property Bridge Manager) платформы Moz… |
| `core/superlibre.py` | 527 | 1 | 0 | Библиотека SuperLibre — методы трансляции low-code свойств в Qt/Python и обра… |
| `core/system_fields.py` | 198 | 0 | 5 | Словарь вшитых полей сущностей Mozart ERP. |
| `core/virtual_class_node.py` | 99 | 1 | 0 | Модуль структуры скомпилированного low-code класса в оперативной памяти Конфи… |
| `crud_buttons.py` | 46 | 1 | 0 | — |
| `database.py` | 46 | 1 | 0 | — |
| `dialogs/__init__.py` | 15 | 0 | 0 | Экспорт диалогов и утилит для работы с классами. |
| `dialogs/base_class_selector.py` | 177 | 1 | 0 | Диалог выбора базового класса при создании нового класса. |
| `dialogs/class_edit_dialog.py` | 2111 | 5 | 0 | Главное окно редактирования структуры класса ERP. |
| `dialogs/class_group_edit_dialog.py` | 179 | 1 | 0 | — |
| `dialogs/class_group_manager_dialog.py` | 148 | 1 | 0 | — |
| `dialogs/collection_manager.py` | 493 | 1 | 0 | Менеджер коллекции элементов сцены редактора классов. |
| `dialogs/methods_dialog.py` | 511 | 1 | 0 | Диалог управления методами класса (модальный). |
| `dialogs/select_entity_dialog.py` | 133 | 1 | 0 | Независимое модальное окно выбора сущности из meta.entitytypes. |
| `dialogs/select_field_dialog.py` | 191 | 1 | 0 | Независимое модальное окно выбора поля. |
| `dialogs/signals_dialog.py` | 194 | 1 | 0 | Диалог управления сигналами класса. |
| `ide_core.py` | 172 | 1 | 0 | — |
| `ide_db_work.py` | 64 | 1 | 0 | — |
| `ide_field_edit.py` | 241 | 1 | 0 | — |
| `ide_main.py` | 325 | 1 | 0 | Главный стартовый модуль интегрированной среды разработки (IDE) Mozart ERP. |
| `ide_ui_panels.py` | 224 | 1 | 0 | Модуль предоставляет класс-примесь MozartIDEPanelsMixin. |
| `upload_to_gitverse.py` | 104 | 0 | 2 | Автономный скрипт для заливки всех .py файлов проекта напрямую на GitVerse че… |
| `описание.py` | 957 | 8 | 1 | Генератор структурированной документации проекта Mozart ERP. |

---

## Детальные карточки файлов


### <a id="base-manager-py"></a>`base_manager.py`

**Строк:** 90
**Импорты:** from `PySide6.QtWidgets` import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox (+1); from `PySide6.QtCore` import Qt; from `database` import DatabaseService

**Классы:**

- **`class BaseEntityManager`** (QWidget)
  - _Базовый класс для виджетов управления справочниками._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None)`
    - `set_crud_buttons(crud_widget)` — Привязать виджет с кнопками и подключить сигналы.
    - `load_data()` — Загрузить данные из БД и обновить таблицу. Переопределяется в подклассах.
    - `refresh_table()` — Обновить отображение таблицы на основе self.data.
    - `get_selected_id()` — Возвращает id выбранной строки или None.
    - `add_item()` — Добавление нового элемента. Переопределяется.
    - `edit_item()` — Редактирование выбранного элемента. Переопределяется.
    - `delete_item()` — Удаление выбранного элемента. Переопределяется.
    - `on_item_double_clicked(item)` — По двойному клику вызываем редактирование.
  - **Приватные методы:** (1 шт.)
    - `_setup_table()`


### <a id="composition-manager-py"></a>`composition_manager.py`

**Строк:** 92
**Импорты:** from `PySide6.QtWidgets` import QMessageBox; from `database` import DatabaseService

**Классы:**

- **`class CompositionManager`**
  - **Методы:**
    - `__init__(db = None, parent_widget = None)`
    - `ensure_ext_table_and_field(child_entity_id, link_field_name)`
    - `add_composition(parent_entityid, child_entityid, role_id, link_field, sortorder = 10)`
    - `update_composition(comp_id, parent_entityid, child_entityid, role_id, link_field, sortorder = 10)`
    - `delete_composition(comp_id)`
  - **Приватные методы:** (1 шт.)
    - `_get_entity_cname()` — Возвращает системное имя (cname) сущности, приводит к нижнему регистру.


### <a id="constest-py"></a>`constest.py`

**Строк:** 28
**Импорты:** import `sys`; from `PySide6.QtWidgets` import QApplication; from `ide_core` import goProject; from `database` import DatabaseService; from `dialogs.class_edit_dialog` import ClassEditDialog


### <a id="core-bridge-function-registry-py"></a>`core/bridge_function_registry.py`

**Роль:** Реестр функций трансляции значений low-code свойств в Qt/Python и обратно.
**Строк:** 83
**Импорты:** import `inspect`; from `enum` import Enum; from `typing` import Callable, Optional, Tuple
**Импортируется в:** `core/bridge_functions_builtin.py`, `core/bridge_resolver.py`, `ide_core.py`

**Классы:**

- **`class BridgeFunctionKind`** (Enum)
- **`class BridgeFunctionRegistry`**
  - _Имена из БД -> callable. Валидация сигнатур при регистрации._
  - **Методы:**
    - `__init__()`
    - `register(name: str, kind: BridgeFunctionKind, fn: Callable)`
    - `get_to_runtime(name: Optional[str])` -> `Optional[Callable]`
    - `get_from_runtime(name: Optional[str])` -> `Optional[Callable]`
    - `get_select(name: Optional[str])` -> `Optional[Callable]`
    - `known_names()` -> `list[str]`
    - `has_missing(names: list[str])` -> `list[str]` — Возвращает имена, которых нет в реестре (для лога при старте).
  - **Приватные методы:** (2 шт.)
    - `_assert_signature()`
    - `_get_typed()`


### <a id="core-bridge-functions-builtin-py"></a>`core/bridge_functions_builtin.py`

**Роль:** Встроенные функции трансляции low-code свойств в Qt/Python и обратно.
**Строк:** 290
**Импорты:** import `json`; from `typing` import Optional; from `PySide6.QtCore` import QSize; from `PySide6.QtGui` import QFont, QPixmap, QIcon; from `PySide6.QtWidgets` import QWidget, QFileDialog, QFontDialog, QColorDialog; from `core.bridge_function_registry` import BridgeFunctionKind, BridgeFunctionRegistry
**Импортируется в:** `ide_core.py`

**Функции модуля:**

- `direct_to_qt(widget: QWidget, prop_key: str, value: str)`
- `direct_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `font_to_qt(widget: QWidget, prop_key: str, value: str)`
- `font_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `select_font_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]`
- `color_to_css(widget: QWidget, prop_key: str, value: str)`
- `color_from_css(widget: QWidget, prop_key: str)` -> `str`
- `select_color_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]`
- `size_to_qt(widget: QWidget, prop_key: str, value: str)`
- `size_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `select_size_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]`
- `image_to_qt(widget: QWidget, prop_key: str, value: str)`
- `image_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `select_image_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]`
- `items_to_qt(widget: QWidget, prop_key: str, value: str)`
- `items_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `metadata_to_qt(widget: QWidget, prop_key: str, value: str)` — binding_entity, display_field, selector_form — только в коллекции, не в Qt.
- `metadata_from_qt(widget: QWidget, prop_key: str)` -> `str`
- `select_entity_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]` — Выбор сущности из meta.entitytypes. Возвращает str(id) или None.
- `select_field_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]` — Выбор поля сущности (вшитого или расширения).
- `select_form_dialog(parent: QWidget, current_value = None, entity_id = None)` -> `Optional[str]` — TODO: формы отложены до отдельной задачи. Пока no-op.
- `register_builtin_bridges(registry: BridgeFunctionRegistry)` — Регистрирует все встроенные функции в реестре.


### <a id="core-bridge-resolver-py"></a>`core/bridge_resolver.py`

**Роль:** BridgeResolver — трёхуровневый резолвер функций моста.
**Строк:** 238
**Импорты:** from `typing` import Optional, Callable; from `core.bridge_function_registry` import BridgeFunctionKind

**Классы:**

- **`class BridgeResolver`**
  - _Резолвер функций моста: метод класса → SuperLibre._
  - **Методы:**
    - `__init__(go_project)`
    - `resolve_to_runtime(func_name: Optional[str], version_id: int, widget, collection, cname: str, value: str)` -> `bool` — Применяет значение свойства к живому Qt-виджету.
    - `resolve_from_runtime(func_name: Optional[str], version_id: int, widget, collection, cname: str)` -> `Optional[str]` — Читает значение свойства из живого Qt-виджета.
    - `resolve_select(func_name: Optional[str], version_id: int, widget, collection, cname: str, current_value = None)` -> `Optional[str]` — Открывает диалог выбора значения свойства.
    - `invalidate(version_id: Optional[int] = None)` — Сбрасывает кэш скомпилированных методов.
  - **Приватные методы:** (3 шт.)
    - `_resolve_class_method()` — Возвращает скомпилированный callable метода класса или None.
    - `_find_method_in_db()` — Вызывает f_find_class_method(version_id, func_name).
    - `_compile_method()` — Компилирует текст метода (def func_name(self, ...): ...) в callable.


### <a id="core-class-registry-py"></a>`core/class_registry.py`

**Роль:** Глобальная Машина классов (Class Registry / Class Loader) платформы Mozart ERP.
**Строк:** 205
**Импорты:** import `gc`; from `typing` import Dict, Optional; from `core.virtual_class_node` import VirtualClassNode

**Классы:**

- **`class ClassRegistry`**
  - _Глобальный менеджер и загрузчик low-code классов Конфигуратора._
  - **Методы:**
    - `__init__(db_service = None)`
    - `get_class_version(version_id: int)` -> `Optional[VirtualClassNode]` — Возвращает готовую версию класса из памяти.
    - `get_objpropcol_raw(version_id: int)` -> `list` — Ленивый кэш результата f_build_objpropcol для версии класса.
    - `sync_registry_with_session_date()` — Жестко выжигает из ОЗУ все версии классов, которые не попадают
  - **Приватные методы:** (2 шт.)
    - `_load_class_from_db_cascade()`
    - `_fill_local_node_sub_collections()`


### <a id="core-extend-bridges-py"></a>`core/extend_bridges.py`

**Роль:** Автономный скрипт расширения таблицы class_property_bridge.
**Строк:** 198
**Импорты:** import `psycopg2`; import `sys`; import `os`
**Глобальные константы:** `DB_CONFIG` = dict[5], `ALL_QT_CLASSES` = list[17]

**Функции модуля:**

- `extend_property_bridges()`


### <a id="core-method-collection-py"></a>`core/method_collection.py`

**Роль:** Коллекция методов ОДНОГО экземпляра объекта на сцене (или класса).
**Строк:** 118
**Импорты:** from `typing` import Dict, List, Optional; from `core.method_item` import MethodItem
**Импортируется в:** `dialogs/collection_manager.py`

**Классы:**

- **`class MethodCollection`**
  - _Коллекция методов экземпляра объекта сцены._
  - **Методы:**
    - `__init__(element_id: int)`
    - `add(method: MethodItem)` — Добавляет метод с учётом приоритета order.
    - `[class] from_raw_rows(element_id: int, rows: List[tuple])` -> `'MethodCollection'`
    - `get(c_name: str)` -> `Optional[MethodItem]`
    - `all_ordered()` -> `List[MethodItem]`
    - `__len__()` -> `int`
    - `__contains__(c_name: str)` -> `bool`
    - `set_lang(c_name: str, i_lang: int)` -> `bool` — Меняет i_lang метода. Возвращает True, если изменилось.
    - `remove(c_name: str)` -> `bool` — Помечает метод на удаление (is_deleted=True).
    - `add_new(method: MethodItem)` — Добавляет новый метод (id=-1, is_new=True).
    - `get_changed()` -> `List[MethodItem]` — Методы, у которых is_changed=True (включая is_new, is_deleted).
    - `mark_saved()` — После записи в БД — сбрасываем флаги.


### <a id="core-method-item-py"></a>`core/method_item.py`

**Роль:** Метаданные одного метода экземпляра объекта сцены (или класса).
**Строк:** 37
**Импорты:** from `dataclasses` import dataclass, field; from `datetime` import datetime; from `typing` import Optional
**Импортируется в:** `core/method_collection.py`, `dialogs/methods_dialog.py`

**Классы:**

- **`class MethodItem`**
  - _Метаданные метода (без кода)._
  - **Методы:**
    - `is_inherited()` -> `bool` — True, если метод унаследован (order > 1).


### <a id="core-object-property-py"></a>`core/object_property.py`

**Роль:** Одна строка objpropcol — свойство экземпляра объекта на сцене.
**Строк:** 52
**Импорты:** from `dataclasses` import dataclass, field; from `typing` import Optional
**Импортируется в:** `core/object_property_collection.py`, `dialogs/collection_manager.py`

**Классы:**

- **`class ObjectProperty`**
  - _Свойство экземпляра объекта сцены._
  - **Методы:**
    - `__post_init__()`
    - `is_changed()` -> `bool` — True, если аналитик изменил значение относительно исходного.


### <a id="core-object-property-collection-py"></a>`core/object_property_collection.py`

**Роль:** Коллекция свойств ОДНОГО экземпляра объекта на сцене.
**Строк:** 132
**Импорты:** from `typing` import Dict, List, Optional; from `core.object_property` import ObjectProperty
**Импортируется в:** `dialogs/collection_manager.py`

**Классы:**

- **`class ObjectPropertyCollection`**
  - _objpropcol экземпляра объекта сцены._
  - **Методы:**
    - `__init__(element_id: int)`
    - `add(prop: ObjectProperty)` — Добавляет свойство с учётом приоритета order.
    - `[class] from_raw_rows(element_id: int, rows: List[tuple])` -> `'ObjectPropertyCollection'` — Строит коллекцию из результата f_build_objpropcol.
    - `get(cname: str)` -> `Optional[ObjectProperty]`
    - `all_ordered()` -> `List[ObjectProperty]`
    - `__len__()` -> `int`
    - `__contains__(cname: str)` -> `bool`
    - `set_value(cname: str, new_value: str, source: str = 'manual')` -> `bool` — Устанавливает новое значение. Возвращает True, если значение реально изменилось.
    - `apply_to_widget(widget, bridge_manager, prop_names: Optional[List[str]] = None)` — Применяет значения к живому Qt-виджету через bridgecalcset.
    - `read_from_widget(widget, bridge_manager, prop_names: Optional[List[str]] = None)` — Читает значения из Qt-виджета через bridgecalcget.
    - `get_changed_properties()` -> `List[ObjectProperty]` — Свойства, у которых value != initial_value.
    - `mark_saved()` — После записи в БД — фиксируем новое initial_value = value.


### <a id="core-property-bridge-manager-py"></a>`core/property_bridge_manager.py`

**Роль:** Менеджер декларативных мостов свойств (Property Bridge Manager) платформы Mozart ERP.
**Строк:** 278
**Импорты:** import `re`; from `typing` import Dict, Any, List, Optional

**Классы:**

- **`class PropertyBridgeManager`**
  - _Глобальный менеджер правил связи, кэширования и трансляции low-code свойств._
  - **Методы:**
    - `__init__(db_service = None)`
    - `init_and_warm_cache()`
    - `get_properties_for_class(c_base_class: str)` -> `Dict[str, Dict[str, Any]]` — Возвращает плоский словарь спецификаций low-code свойств для конкретного нативного класса.
    - `get_allowed_values(bridge_id: int)` -> `List[Dict[str, str]]` — Возвращает упорядоченный список выбора для комбобоксов ячеек типа choice.
    - `translate_to_runtime(widget, prop_key: str, value: str, base_qt_class: str)` -> `bool` — Реактивная Машина Прямого Хода.
    - `apply_property_to_widget(widget, prop, version_id = None)` — Применяет ОДНО свойство к живому Qt-виджету.
    - `read_property_from_widget(widget, prop, version_id = None, collection = None)` -> `Optional[str]` — Читает ОДНО свойство из живого Qt-виджета.
    - `apply_bridge_translations(widget, collection, version_id = None)` — Полный проход по ObjectPropertyCollection с применением к живому Qt-виджету.


### <a id="core-superlibre-py"></a>`core/superlibre.py`

**Роль:** Библиотека SuperLibre — методы трансляции low-code свойств в Qt/Python и обратно,
**Строк:** 527
**Импорты:** import `json`; import `re`; from `typing` import Optional; from `PySide6.QtCore` import QSize, Qt; from `PySide6.QtGui` import QFont, QColor, QPixmap, QIcon; from `PySide6.QtWidgets` import QWidget, QFontDialog, QColorDialog, QFileDialog, QInputDialog (+2)

**Классы:**

- **`class SuperLibre`** ⚠️ _большой класс_
  - **Методы:**
    - `direct_to_qt(widget, collection, cname, value)`
    - `direct_from_qt(widget, collection, cname)`
    - `geometry_get(collection, cname: str, default: int = 0)` -> `int`
    - `geometry_to_qt(widget, collection, cname, value)`
    - `geometry_from_qt(widget, collection, cname)`
    - `select_geometry_dialog(widget, collection, cname, current_value = None)`
    - `font_to_qt(widget, collection, cname, value)`
    - `font_from_qt(widget, collection, cname)`
    - `select_font_dialog(widget, collection, cname, current_value = None)`
    - `color_to_backcss(widget, collection, cname, value)` — Применяет ТОЛЬКО background-color через атомарную замену.
    - `color_to_textcss(widget, collection, cname, value)` — Аналогично для цвета текста.
    - `color_from_backcss(widget, collection, cname)`
    - `color_from_textcss(widget, collection, cname)`
    - `color_to_bordercss(widget, collection, cname, value)` — Применяет ТОЛЬКО border-color.
    - `color_from_bordercss(widget, collection, cname)`
    - `select_color_dialog(widget, collection, cname, current_value = None)` — Выбор цвета. НЕ принимает db.
    - `size_to_qt(widget, collection, cname, value)`
    - `size_from_qt(widget, collection, cname)`
    - `select_size_dialog(widget, collection, cname, current_value = None)`
    - `image_to_qt(widget, collection, cname, value)`
    - `image_from_qt(widget, collection, cname)`
    - `select_image_dialog(widget, collection, cname, current_value = None)`
    - `items_to_qt(widget, collection, cname, value)`
    - `items_from_qt(widget, collection, cname)`
    - `metadata_to_qt(widget, collection, cname, value)` — Применяет ERP-метаданные к виджету через setProperty.
    - `metadata_from_qt(widget, collection, cname)` — Читает метаданные из виджета.
    - `entity_id_to_name(widget, collection, cname)` — bridgecalcget: Транслирует ID сущности в имя через SQL-запрос к БД.
    - `field_id_to_name(widget, collection, cname)` — bridgecalcget: Транслирует ID поля в имя.
    - `select_entity_dialog(widget, collection, cname, current_value = None, db = None)` — Диалог выбора сущности.
    - `select_field_dialog(widget, collection, cname, current_value = None, db = None)` — Диалог выбора поля.
    - `select_form_dialog(widget, collection, cname, current_value = None, db = None)` — Заглушка для выбора формы.


### <a id="core-system-fields-py"></a>`core/system_fields.py`

**Роль:** Словарь вшитых полей сущностей Mozart ERP.
**Строк:** 198
**Импорты:** from `typing` import Optional
**Импортируется в:** `dialogs/select_field_dialog.py`
**Глобальные константы:** `ENTITY_VERSION_FIELDS` = dict[9], `ENTITY_INSTANCE_FIELDS` = dict[3], `SYSTEM_FIELDS` = dict[0], `_CNAME_TO_ID` = DictComp

**Функции модуля:**

- `get_system_field(field_id: int)` -> `Optional[dict]` — Возвращает описание вшитого поля по отрицательному ID.
- `get_system_field_by_name(cname: str)` -> `Optional[dict]` — Возвращает описание вшитого поля по cname (например, 'cname').
- `is_system_field_id(field_id)` -> `bool` — True, если field_id — отрицательный (вшитое поле).
- `list_fields_for_dialog()` -> `list` — Возвращает список вшитых полей для диалога выбора:
- `get_sql_expression(field_id: int, version_alias: str = 'v')` -> `Optional[str]` — Возвращает SQL-выражение для чтения вшитого поля.


### <a id="core-virtual-class-node-py"></a>`core/virtual_class_node.py`

**Роль:** Модуль структуры скомпилированного low-code класса в оперативной памяти Конфигуратора.
**Строк:** 99
**Импорты:** from `typing` import Dict, Any, Optional
**Импортируется в:** `core/class_registry.py`

**Классы:**

- **`class VirtualClassNode`**
  - _Объектное представление версии класса и его унаследованных подобъектов_
  - **Методы:**
    - `__init__(version_id: int, class_id: int, class_name: str)`
    - `resolve_method(method_name: str)` -> `Optional[str]` — Возвращает исходный код метода (txt_method) или None.
    - `has_method(method_name: str)` -> `bool` — True, если метод есть в sub_methods, sub_method_bridges или резолвится через mydefault.


### <a id="crud-buttons-py"></a>`crud_buttons.py`

**Строк:** 46
**Импорты:** from `PySide6.QtWidgets` import QWidget, QHBoxLayout, QPushButton; from `PySide6.QtCore` import Signal; from `lang.local_translator` import LocalTranslator

**Классы:**

- **`class CrudButtons`** (QWidget)
  - **Сигналы:** `add_clicked`, `edit_clicked`, `delete_clicked`
  - **Методы:**
    - `__init__(parent = None, with_add = True, with_edit = True, with_delete = True)`
    - `retranslate_ui()`


### <a id="database-py"></a>`database.py`

**Строк:** 46
**Импорты:** import `psycopg2`; from `ide_core` import goProject
**Импортируется в:** `base_manager.py`, `composition_manager.py`, `constest.py`, `dialogs/base_class_selector.py`, `dialogs/class_edit_dialog.py`
  _… и ещё 10_

**Классы:**

- **`class DatabaseService`**
  - _Единый класс для взаимодействия с БД, обёртка над goProject._
  - **Методы:**
    - `__init__()`
    - `execute_query(sql, params = None, fetch = True)` — Выполнить SQL-запрос (SELECT или модифицирующий).
    - `execute_procedure(proc_name, params = None)`
    - `get_connection()`
    - `refresh_connection()`


### <a id="dialogs---init---py"></a>`dialogs/__init__.py`

**Роль:** Экспорт диалогов и утилит для работы с классами.
**Строк:** 15
**Импорты:** from `base_class_selector` import BaseClassSelectorDialog; from `methods_dialog` import MethodsDialog; from `signals_dialog` import SignalsDialog; from `collection_manager` import CollectionManager


### <a id="dialogs-base-class-selector-py"></a>`dialogs/base_class_selector.py`

**Роль:** Диалог выбора базового класса при создании нового класса.
**Строк:** 177
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QTreeWidget (+4); from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `services.class_data_service` import ClassDataService; from `lang.local_translator` import LocalTranslator
**Импортируется в:** `dialogs/__init__.py`

**Классы:**

- **`class BaseClassSelectorDialog`** (QDialog)
  - _Диалог выбора базового класса._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None)`
    - `setup_ui()` — Настройка интерфейса диалога.
    - `load_classes(filter_type: str = 'all')` — Загрузка классов в дерево.
    - `get_selected_version_id()` -> `int` — Получение ID выбранной версии класса.
    - `on_filter_changed(index: int)` — Обработка смены фильтра.
    - `on_item_double_clicked(item: QTreeWidgetItem, column: int)` — Обработка двойного клика по элементу.
    - `accept_selection()` — Подтверждение выбора.


### <a id="dialogs-class-edit-dialog-py"></a>`dialogs/class_edit_dialog.py`

**Роль:** Главное окно редактирования структуры класса ERP.
**Строк:** 2111
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar (+22); from `PySide6.QtCore` import Qt, QPoint, QRectF, QPointF, Signal (+2); from `PySide6.QtGui` import QAction, QPen, QColor, QBrush, QKeyEvent (+3); import `json`; from `typing` import Optional, Dict, List, Any; from `database` import DatabaseService; from `services.class_data_service` import ClassDataService; from `dialogs.collection_manager` import CollectionManager; from `controls` import create_control; from `lang.local_translator` import LocalTranslator
  _… и ещё 1_
**Импортируется в:** `constest.py`

**Классы:**

- **`class MoveHandleItem`** (QGraphicsObject)
  - _Плавающий хендл перемещения в виде руки. Позиционируется в ЛЕВОМ нижнем углу._
  - **Методы:**
    - `__init__(target_item: 'ControlGraphicsItem', collection: CollectionManager, dialog = None)`
    - `setRect(x, y, w, h)`
    - `rect()`
    - `boundingRect()`
    - `paint(painter, option, widget = None)`
    - `update_position()`
    - `mousePressEvent(event)`
    - `mouseMoveEvent(event)`
    - `mouseReleaseEvent(event)`
- **`class ResizeHandleItem`** (QGraphicsObject)
  - _Плавающий хендл ресайза со стрелками. horizontal=ширина, vertical=высота._
  - **Методы:**
    - `__init__(target_item: 'ControlGraphicsItem', collection: CollectionManager, axis: str, dialog = None)`
    - `setRect(x, y, w, h)`
    - `rect()`
    - `boundingRect()`
    - `paint(painter, option, widget = None)`
    - `update_position()`
    - `mousePressEvent(event)`
    - `mouseMoveEvent(event)`
    - `mouseReleaseEvent(event)`
- **`class ControlGraphicsItem`** (QGraphicsObject)
  - _Графический элемент контрола._
  - **Сигналы:** `selected_changed`, `geometry_changed`
  - **Методы:**
    - `__init__(element_id: int, control_widget, parent = None, collection = None, is_logical = False)`
    - `refresh_from_widget()`
    - `boundingRect()`
    - `set_rect(x, y, w, h)`
    - `itemChange(change, value)`
    - `rect()`
    - `paint(painter, option, widget = None)`
    - `set_geometry(x: float, y: float, width: float, height: float)`
    - `set_selected(selected: bool)`
    - `sceneEventFilter(watched, event)`
    - `mousePressEvent(event)`
- **`class MozartGraphicsView`** (QGraphicsView)
  - _Кастомный View._
  - **Методы:**
    - `__init__(scene, parent = None)`
    - `mousePressEvent(event)`
    - `mouseMoveEvent(event)`
    - `mouseReleaseEvent(event)`
  - **Приватные методы:** (1 шт.)
    - `_find_cgi()`
- **`class ClassEditDialog`** (QDialog) ⚠️ _большой класс_
  - _Диалог редактирования класса._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, version_id: int = UnaryOp, mode: str = 'add')`
    - `setup_ui()`
    - `apply_geometry_to_selected_widgets()`
    - `load_source_classes()`
    - `load_class_data(version_id: int)`
    - `load_controls_from_db()`
    - `render_scene()`
    - `create_control_item(element_id: int, element_data: Dict, parent_item: Optional[ControlGraphicsItem] = None)` -> `ControlGraphicsItem`
    - `update_properties_panel()` — Рендеринг инспектора свойств.
    - `toggle_grid()`
    - `on_grid_size_changed(size: str)`
    - `show_methods_dialog()`
    - `show_signals_dialog()`
    - `inject_class(item: QTreeWidgetItem, column: int)`
    - `save_class()`
    - `keyPressEvent(event: QKeyEvent)`
  - **Приватные методы:** (27 шт.)
    - `_sync_graphics_item_geometry()`
    - `_create_source_panel()`
    - `_fill_classes_into_tree()`
    - `_create_scene_panel()`
    - `_create_properties_panel()`
    - `_ensure_default_methods_sync()`
    - `_fill_lineage_and_methods()`
    - `_normalize_version()`
    - `_draw_grid()`
    - `_on_item_selected()`
    - `_handle_click_selection()`
    - `_clear_all_selection_visuals()`
    - `_update_selection_visuals()`
    - `_update_active_handles()`
    - `_show_context_menu()`
    - `_on_table_item_changed()` — Обработчик изменения ячейки таблицы свойств.
    - `_apply_bridge_set()` — Вызывает bridgecalcset для применения значения к виджету.
    - `_get_bridge_get()` — Получает отображаемое значение через bridgecalcget.
    - `_open_select_dialog()` — Открывает диалог выбора значения.
    - `_on_property_value_changed()` — Универсальный обработчик изменения свойства.
    - `_on_property_widget_changed()`
    - `_open_font_dialog()`
    - `_open_image_dialog()`
    - `_save_collection_subobjects_immutable()`
    - `_save_sub_collections_relational()`
    - `_save_class_in_place()`
    - `_save_methods_from_collection()`


### <a id="dialogs-class-group-edit-dialog-py"></a>`dialogs/class_group_edit_dialog.py`

**Строк:** 179
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTreeWidget (+6); from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `lang.local_translator` import LocalTranslator
**Импортируется в:** `dialogs/class_group_manager_dialog.py`

**Классы:**

- **`class ClassGroupEditDialog`** (QDialog)
  - _Окно добавления/редактирования одной группы классификатора._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, group_id: int = 0, initial_name: str = '')`
    - `setup_ui()` — Настройка интерфейса диалога с добавлением поля дескрипции группы.
    - `clear_parent_selection()` — Сбрасывает все галочки, делая группу корневой.
    - `on_item_checked(item: QTreeWidgetItem, column: int)` — Гарантирует триггер только ОДНОГО чекбокса в иерархии.
    - `load_parent_tree()` — Строит дерево потенциальных родителей из базы данных.
    - `load_group_data()` — Загрузка полей существующей группы, включая дескрипцию (mcomment).
    - `save_data()` — Запись изменений, включая описание (mcomment), в PostgreSQL.
  - **Приватные методы:** (3 шт.)
    - `_uncheck_recursive()`
    - `_clear_other_checks()`
    - `_set_check_recursive()`


### <a id="dialogs-class-group-manager-dialog-py"></a>`dialogs/class_group_manager_dialog.py`

**Строк:** 148
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget (+3); from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `lang.local_translator` import LocalTranslator; from `class_group_edit_dialog` import ClassGroupEditDialog

**Классы:**

- **`class ClassGroupManagerDialog`** (QDialog)
  - _Менеджер иерархической структуры категорий с фильтром и защитой удаления._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None)`
    - `setup_ui()`
    - `on_item_selected()`
    - `load_groups()` — Загрузка дерева групп с учетом текстового фильтра TXT1.
    - `add_group()` — Инъекция текста из фильтра TXT1 в новое окно, если он заполнен.
    - `edit_group()`
    - `delete_group()` — Каскадная проверка безопасности на чистоту группы перед удалением.


### <a id="dialogs-collection-manager-py"></a>`dialogs/collection_manager.py`

**Роль:** Менеджер коллекции элементов сцены редактора классов.
**Строк:** 493
**Импорты:** from `typing` import Dict, List, Set, Optional, Any (+1); from `PySide6.QtCore` import QRectF; from `PySide6.QtWidgets` import QGraphicsItem; from `core.object_property` import ObjectProperty; from `core.object_property_collection` import ObjectPropertyCollection; from `core.method_collection` import MethodCollection
**Импортируется в:** `dialogs/__init__.py`, `dialogs/class_edit_dialog.py`, `dialogs/methods_dialog.py`

**Классы:**

- **`class CollectionManager`** ⚠️ _большой класс_
  - _Централизованное хранилище состояния сцены с защищённым API._
  - **Свойства (@property):**
    - `selected_ids` -> `frozenset`
    - `elements_count` -> `int`
    - `active_container_id` -> `Optional[int]`
    - `last_selected_id` -> `Optional[int]`
  - **Методы:**
    - `__init__()`
    - `get_element(element_id: int)` -> `Optional[Dict]`
    - `get_graphic_item(element_id: int)` -> `Optional[QGraphicsItem]`
    - `get_selected_elements()` -> `List[Dict]`
    - `get_last_selected()` -> `Optional[Dict]`
    - `add_element_with_metadata(element_data: dict, donor_version_id: int, db_service)` -> `int`
    - `add_element(element_data: Dict, graphic_item: Optional[QGraphicsItem] = None)` -> `int`
    - `link_graphic_item(element_id: int, graphic_item: QGraphicsItem)`
    - `update_element_data(element_id: int, data: Dict, from_graphics: bool = False)`
    - `remove_element(element_id: int)`
    - `add_to_selection(element_id: int)` -> `bool`
    - `remove_from_selection(element_id: int)`
    - `set_selection(element_ids: List[int], container_id: Optional[int])`
    - `clear_selection()`
    - `select_element(element_id: int, additive: bool = False)` -> `bool`
    - `move_selected(dx: float, dy: float)`
    - `resize_selected(dw: float, dh: float)`
    - `delete_selected()`
    - `align_selected(alignment: str)`
    - `equalize_width()`
    - `equalize_height()`
    - `equalize_sizes()`
    - `get_inserts()` -> `List[Dict]`
    - `get_updates()` -> `List[Dict]`
    - `get_deletes()` -> `List[int]`
    - `get_next_id()` -> `int`
    - `init_property_collection(element_id: int, raw_rows: list)` -> `Optional[ObjectPropertyCollection]` — Инициализирует ObjectPropertyCollection для элемента сцены
    - `get_property_collection(element_id: int)` -> `Optional[ObjectPropertyCollection]` — Возвращает коллекцию свойств элемента или None.
    - `set_property_value(element_id: int, cname: str, value: str, source: str = 'manual')` -> `bool` — Устанавливает значение свойства в коллекции элемента.
    - `get_property_value(element_id: int, cname: str)` -> `Optional[str]` — Возвращает текущее значение свойства или None.
    - `apply_property_collection_to_widget(element_id: int, widget, bridge_manager)` -> `bool` — Применяет всю коллекцию элемента к живому Qt-виджету через
    - `get_changed_properties(element_id: int)` -> `list` — Возвращает список ObjectProperty, у которых value != initial_value.
    - `set_lineage(element_id: int, lineage: List[Dict])` — Сохраняет линию крови для элемента сцены.
    - `get_lineage(element_id: int)` -> `List[Dict]` — Возвращает линию крови элемента (или пустой список).
    - `init_method_collection(element_id: int, raw_rows: list)` -> `Optional[MethodCollection]` — Инициализирует MethodCollection для элемента сцены.
    - `get_method_collection(element_id: int)` -> `Optional[MethodCollection]` — Возвращает коллекцию методов элемента или None.
    - `get_changed_methods()` -> `Dict[int, list]` — Возвращает { element_id: [MethodItem, ...] } для всех изменённых методов.
    - `mark_methods_saved()` — После записи в БД — сбрасываем флаги у всех коллекций.


### <a id="dialogs-methods-dialog-py"></a>`dialogs/methods_dialog.py`

**Роль:** Диалог управления методами класса (модальный).
**Строк:** 511
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox (+11); from `PySide6.QtCore` import Qt, QDateTime; from `PySide6.QtGui` import QFont; from `database` import DatabaseService; from `lang.local_translator` import LocalTranslator; from `dialogs.collection_manager` import CollectionManager; from `core.method_item` import MethodItem
**Импортируется в:** `dialogs/__init__.py`

**Классы:**

- **`class MethodsDialog`** (QDialog)
  - _Диалог управления методами класса (модальный)._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, version_id: int = UnaryOp, element_id: int = UnaryOp, class_name: str = '', collection: CollectionManager = None)`
    - `setup_ui()`
    - `load_object_tree()`
    - `on_object_selected(item: QTreeWidgetItem, column: int)`
    - `on_date_changed(_dt)`
    - `load_methods_combo()`
    - `on_method_selected(index: int)`
    - `load_method_code(method_id: int)`
    - `on_lang_changed(_index)`
    - `add_method()`
    - `delete_method()`
    - `save_method()`
  - **Приватные методы:** (1 шт.)
    - `_get_mono_font()`


### <a id="dialogs-select-entity-dialog-py"></a>`dialogs/select_entity_dialog.py`

**Роль:** Независимое модальное окно выбора сущности из meta.entitytypes.
**Строк:** 133
**Импорты:** from `typing` import Optional; from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem (+4); from `PySide6.QtCore` import Qt; from `database` import DatabaseService

**Классы:**

- **`class SelectEntityDialog`** (QDialog)
  - _Выбор сущности из meta.entitytypes._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, current_value: Optional[str] = None)`
    - `get_selected_id()` -> `Optional[str]`
    - `accept()` — Переопределяем accept для проверки выбора.
    - `keyPressEvent(event)` — Обрабатываем Enter и Escape корректно.
  - **Приватные методы:** (1 шт.)
    - `_load()` — Загрузка списка сущностей.


### <a id="dialogs-select-field-dialog-py"></a>`dialogs/select_field_dialog.py`

**Роль:** Независимое модальное окно выбора поля.
**Строк:** 191
**Импорты:** from `typing` import Optional; from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem (+3); from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `core.system_fields` import SYSTEM_FIELDS

**Классы:**

- **`class SelectFieldDialog`** (QDialog)
  - _Выбор поля (вшитого или расширения) с деревом сущностей._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, current_value: Optional[str] = None, entity_id: Optional[int] = None)`
    - `get_selected_id()` -> `Optional[str]` — Возвращает ID выбранного поля как строку.
    - `accept()` — Переопределяем accept для проверки выбора.
    - `keyPressEvent(event)` — Обрабатываем Enter и Escape корректно.
  - **Приватные методы:** (6 шт.)
    - `_load()` — Загрузка дерева полей.
    - `_make_entity_item()` — Создает узел сущности в дереве.
    - `_fill_entity_fields()` — Заполняет узел сущности её полями.
    - `_maybe_mark_target()` — Подсвечивает строку, если ID совпадает с current_value.
    - `_load_one_entity()` — Загружает дерево для одной конкретной сущности.
    - `_load_all_entities()` — Загружает дерево для всех сущностей.


### <a id="dialogs-signals-dialog-py"></a>`dialogs/signals_dialog.py`

**Роль:** Диалог управления сигналами класса.
**Строк:** 194
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox (+5); from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `services.class_data_service` import ClassDataService; from `lang.local_translator` import LocalTranslator
**Импортируется в:** `dialogs/__init__.py`

**Классы:**

- **`class SignalsDialog`** (QDialog)
  - _Диалог управления сигналами класса._
  - **Методы:**
    - `__init__(parent = None, db: DatabaseService = None, version_id: int = UnaryOp, element_id: int = UnaryOp)`
    - `setup_ui()` — Настройка интерфейса диалога.
    - `load_signals()` — Загрузка сигналов класса.
    - `load_methods()` — Загрузка методов в ComboBox.
    - `assign_method(signal_id: int, method_id: int)` — Привязка метода к сигналу.
    - `on_combo_changed(signal_id: int, combo: QComboBox)` — Обработка изменения ComboBox.


### <a id="ide-core-py"></a>`ide_core.py`

**Строк:** 172
**Импорты:** import `psycopg2`; import `json`; import `os`; from `core.bridge_function_registry` import BridgeFunctionRegistry; from `core.bridge_functions_builtin` import register_builtin_bridges
**Импортируется в:** `constest.py`, `database.py`, `dialogs/class_edit_dialog.py`, `ide_field_edit.py`, `ide_main.py`
  _… и ещё 1_

**Классы:**

- **`class GoProject`**
  - _Глобальный синглтон управления параметрами и машинами ядра платформы Mozart ERP._
  - **Методы:**
    - `__init__()`
    - `set_db_service(db_service)` — Передает инициализированный сервис базы данных в Машины ядра и греет кэш мостов.
    - `p_Connect()` — Установка физического соединения с PostgreSQL.
    - `f_Execute(sql, params = None)` — Выполнение SQL-запроса (SELECT).
    - `p_SaveProject(file_path)` — Сохранение манифеста проекта в .mzt файл (JSON)
    - `p_LoadProject(file_path)` — Загрузка параметров проекта из .mzt файла


### <a id="ide-db-work-py"></a>`ide_db_work.py`

**Строк:** 64
**Импорты:** from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QTabWidget, QPushButton; from `PySide6.QtCore` import Qt; from `database` import DatabaseService; from `tabs` import BalanceUnitsTab, UsersRolesTab, EntitiesTab, DocumentsTab, DataViewTab (+5); from `lang.local_translator` import LocalTranslator
**Импортируется в:** `ide_main.py`, `ide_ui_panels.py`

**Классы:**

- **`class DBWorkDialog`** (QDialog)
  - **Методы:**
    - `__init__(parent = None)`
    - `retranslate_ui()`


### <a id="ide-field-edit-py"></a>`ide_field_edit.py`

**Строк:** 241
**Импорты:** import `sys`; import `re`; from `PySide6.QtWidgets` import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox (+6); from `PySide6.QtCore` import Qt; from `ide_core` import goProject; from `widgets` import ReferenceEditor; from `database` import DatabaseService; from `lang.local_translator` import LocalTranslator
**Глобальные константы:** `SYSTEM_FIELDS` = tuple[2]

**Классы:**

- **`class FieldEditDialog`** (QDialog)
  - **Методы:**
    - `__init__(field_data = None, status_id = None, read_only_mode = False, is_system = False, db = None)`
    - `init_ui()`
    - `update_class_info()` — Обновляет информацию о классе сущности для ссылочного поля.
    - `choose_target_entity()` — Открывает диалог выбора целевой сущности для ссылочного поля.
    - `validate_field_name(text)`
    - `on_type_changed()`
    - `get_data()`


### <a id="ide-main-py"></a>`ide_main.py`

**Роль:** Главный стартовый модуль интегрированной среды разработки (IDE) Mozart ERP.
**Строк:** 325
**Импорты:** import `sys`; import `os`; from `PySide6.QtWidgets` import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter (+3); from `PySide6.QtCore` import Qt; from `PySide6.QtGui` import QAction; from `ide_core` import goProject; from `ide_db_work` import DBWorkDialog; from `lang.local_translator` import LocalTranslator; from `database` import DatabaseService; from `ide_ui_panels` import MozartIDEPanelsMixin

**Классы:**

- **`class MozartIDE`** (QMainWindow, MozartIDEPanelsMixin)
  - _Главное окно IDE Mozart ERP._
  - **Методы:**
    - `__init__()`
    - `change_language(lang_code)`
    - `force_reload_translations()` — Ручной вызов обновления кэша переводов из Postgres без перезапуска приложения.
    - `new_project()`
    - `open_project()` — ИСПРАВЛЕНО: Добавлен DontUseNativeDialog для разблокировки мыши в Linux.
    - `save_project()` — ИСПРАВЛЕНО: Добавлен DontUseNativeDialog при сохранении файла.
    - `about()` — Окно информации о конфигураторе.
    - `on_system_date_changed(datetime_val)` — Слот, обновляющий глобальное время сессии и очищающий ОЗУ от устаревших версий.
  - **Приватные методы:** (2 шт.)
    - `_init_menu()`
    - `_run_methods_diagnostics()` — Временная диагностика: проверка sub_method_bridges в ОЗУ.


### <a id="ide-ui-panels-py"></a>`ide_ui_panels.py`

**Роль:** Модуль предоставляет класс-примесь MozartIDEPanelsMixin.
**Строк:** 224
**Импорты:** import `os`; from `PySide6.QtWidgets` import QWidget, QVBoxLayout, QGroupBox, QPushButton, QFrame (+4); from `PySide6.QtCore` import Qt; from `ide_core` import goProject; from `ide_db_work` import DBWorkDialog; from `database` import DatabaseService
**Импортируется в:** `ide_main.py`

**Классы:**

- **`class MozartIDEPanelsMixin`**
  - _Миксин для изоляции UI-компонентов панелей управления и связей с Postgres._
  - **Наследники:** `ide_main.py::MozartIDE`
  - **Методы:**
    - `retranslate_ui()` — Динамическая смена языковых меток во всем приложении.
    - `connect_to_db()` — Установка соединения с СУБД Postgres и синхронизация словарей.
    - `open_db_work()` — Открытие диалога управления сущностями Mozart ERP.
    - `about()` — Окно информации о конфигураторе.
  - **Приватные методы:** (4 шт.)
    - `_create_left_panel()`
    - `_create_right_panel()`
    - `_update_connection_fields()` — Заполнение полей ввода из структуры goProject.
    - `_clear_connection_fields()`


### <a id="upload-to-gitverse-py"></a>`upload_to_gitverse.py`

**Роль:** Автономный скрипт для заливки всех .py файлов проекта напрямую на GitVerse через REST API.
**Строк:** 104
**Импорты:** import `os`; import `sys`; import `json`; import `base64`; from `urllib.request` import Request, urlopen; from `urllib.error` import HTTPError
**Глобальные константы:** `GITVERSE_OWNER` = 's28091973_mail_ru', `GITVERSE_REPO` = 'mozart', `GITVERSE_TOKEN` = 'dfa59609236ee09a35ee703d927c3e3e984a84ff', `SRC_DIR` = '/home/sergey/Documents/configurate', `API_URL` = JoinedStr

**Функции модуля:**

- `upload_file_via_api(relative_path, local_full_path)` — Отправляет одиночный файл на сервер GitVerse через HTTP REST API.
- `main()`


### <a id="описание-py"></a>`описание.py`

**Роль:** Генератор структурированной документации проекта Mozart ERP.
**Строк:** 957
**Импорты:** import `os`; import `re`; import `ast`; import `json`; from `pathlib` import Path; from `dataclasses` import dataclass, field; from `typing` import List, Dict, Optional, Any, Set (+1); from `datetime` import datetime

**Классы:**

- **`class SimpleMarkdownToHTML`**
  - _Простой конвертер Markdown в HTML без внешних зависимостей._
  - **Методы:**
    - `convert(md_text: str)` -> `str` — Конвертирует Markdown в HTML.
  - **Приватные методы:** (1 шт.)
    - `_escape_html()` — Экранирует HTML-спецсимволы.
- **`class Parameter`**
  - _Параметр функции/метода._
  - **Методы:**
    - `to_dict()` -> `dict`
- **`class FunctionDoc`**
  - _Документация функции._
  - **Методы:**
    - `to_dict()` -> `dict`
- **`class ClassDoc`**
  - _Документация класса._
  - **Методы:**
    - `to_dict()` -> `dict`
- **`class ModuleDoc`**
  - _Документация модуля (файла)._
  - **Методы:**
    - `to_dict()` -> `dict`
- **`class PythonParser`**
  - _Парсит Python файлы и извлекает структуру._
  - **Методы:**
    - `__init__(project_root: str = None)`
    - `parse_file(filepath: str)` -> `Optional[ModuleDoc]` — Парсит один Python файл.
    - `parse_project(root_dir: Optional[str] = None)` -> `Dict[str, ModuleDoc]` — Рекурсивно парсит все Python файлы в проекте.
  - **Приватные методы:** (9 шт.)
    - `_parse_imports()` — Извлекает импорты.
    - `_parse_class()` — Парсит класс и его методы.
    - `_parse_function()` — Парсит функцию/метод.
    - `_get_base_name()` — Получает имя базового класса.
    - `_get_type_hint()` — Извлекает строковое представление типа.
    - `_get_expr_value()` — Извлекает строковое представление значения.
    - `_get_decorator_name()` — Извлекает имя декоратора.
    - `_get_attr_name()` — Извлекает имя атрибута.
    - `_extract_dependencies()` — Извлекает зависимости модуля.
- **`class DocumentationGenerator`**
  - _Генерирует структурированную документацию в разных форматах._
  - **Методы:**
    - `__init__(modules: Dict[str, ModuleDoc], project_root: str)`
    - `generate_markdown(output_file: str)` -> `None` — Генерирует единый Markdown-файл с полной документацией.
    - `generate_json(output_file: str)` -> `None` — Генерирует JSON-документацию.
    - `generate_html(output_file: str)` -> `None` — Генерирует HTML-документацию с использованием встроенного конвертера.
  - **Приватные методы:** (4 шт.)
    - `_write_module_markdown()` — Записывает описание одного модуля в Markdown.
    - `_write_class_markdown()` — Записывает описание класса в Markdown.
    - `_write_function_markdown()` — Записывает описание функции/метода в Markdown.
    - `_slug()` — Создаёт URL-безопасный якорь.
- **`class ProjectAnalyzer`**
  - _Анализирует структуру проекта и строит диаграммы._
  - **Методы:**
    - `__init__(modules: Dict[str, ModuleDoc])`
    - `get_statistics()` -> `Dict` — Собирает статистику по проекту.
    - `generate_mermaid()` -> `str` — Генерирует Mermaid-диаграмму зависимостей.

**Функции модуля:**

- `main()` — Главная функция генерации документации.


---

_Конец карты проекта. Для получения деталей по конкретному файлу — запросите его полный исходник._
