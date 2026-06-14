# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/README_controls.py
"""
===============================================================================
БИБЛИОТЕКА БАЗОВЫХ КОНТРОЛОВ MOZART
===============================================================================

Данный файл содержит документацию по всем контролам библиотеки Mozart.
Каждый контрол наследуется от QWidget (или его наследника) и миксина BaseControl,
который предоставляет единый интерфейс для привязки к данным.

ОСНОВНЫЕ ПРИНЦИПЫ:
- Все контролы умеют работать в двух режимах: ДИЗАЙН и РАНТАЙМ
- В режиме дизайна контролы неактивны, не загружают данные, не реагируют на действия пользователя
- В режиме рантайма контролы полноценно работают с данными через DatabaseService
- Привязка к данным осуществляется через свойства binding_field и entity_alias
- Все контролы можно сериализовать в JSON (свойство properties) и восстановить из него

===============================================================================
МИКСИНЫ И БАЗОВЫЕ КЛАССЫ
===============================================================================

1. BaseControl (base_control.py)
   - Базовый миксин для всех контролов
   - Свойства: binding_field, entity_alias, is_required, is_readonly, alis
   - Методы: set_value(), get_value(), is_dirty(), reset()
   - Атрибуты: _original_value, _is_dirty

2. DataSourceMixin (data_source_mixin.py)
   - Миксин для контролов, работающих со списками
   - source_type: "static" (из JSON), "entity" (из БД), "query" (произвольный SQL)
   - Для source_type="entity": entity_alias, display_field, value_field, filter_expression, order_by
   - Для source_type="static": items_json
   - Методы: load_items(), get_items(), find_value_by_text(), find_text_by_value()

===============================================================================
СПИСОК КОНТРОЛОВ
===============================================================================
"""

# -----------------------------------------------------------------------------
# 1. MozartTextBox (textbox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QLineEdit + BaseControl
Назначение: Однострочное текстовое поле
Особенности:
- Сигнал value_changed(str) при изменении текста
- Поддержка placeholderText через свойство 'label'
- В режиме дизайна: setReadOnly(True), setEnabled(False)

Свойства для сериализации:
    - binding_field: str
    - entity_alias: str
    - is_required: bool
    - is_readonly: bool
    - label: str (placeholder)

Пример JSON:
{
    "class": "MozartTextBox",
    "name": "surname",
    "properties": {
        "binding_field": "cLastName",
        "label": "Фамилия",
        "x": 10, "y": 50, "width": 200, "height": 30
    }
}
"""

# -----------------------------------------------------------------------------
# 2. MozartNumberBox (numberbox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QLineEdit + BaseControl
Назначение: Числовое поле с валидацией
Особенности:
- Валидатор QDoubleValidator
- Свойства: min_value, max_value, decimal_places
- Автоматическое форматирование числа

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str (placeholder)
    - min_value: float
    - max_value: float
    - decimal_places: int
"""

# -----------------------------------------------------------------------------
# 3. MozartDateBox (datebox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QDateEdit + BaseControl
Назначение: Выбор даты с календарём
Особенности:
- Формат по умолчанию: "dd.MM.yyyy"
- Свойство date_format для изменения формата
- setCalendarPopup(True)

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - date_format: str
"""

# -----------------------------------------------------------------------------
# 4. MozartCheckBox (checkbox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QCheckBox + BaseControl
Назначение: Флажок (двоичное состояние)
Особенности:
- get_value() возвращает bool
- set_value() принимает bool, str ("true"/"false"), int

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str (текст рядом с чекбоксом)
"""

# -----------------------------------------------------------------------------
# 5. MozartMemo (memo.py)
# -----------------------------------------------------------------------------
"""
Наследник: QPlainTextEdit + BaseControl
Назначение: Многострочное текстовое поле
Особенности:
- Поддержка переноса строк
- Сигнал value_changed(str)

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str
"""

# -----------------------------------------------------------------------------
# 6. MozartComboBox (combobox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QComboBox + BaseControl + DataSourceMixin
Назначение: Выпадающий список
Особенности:
- Поддерживает два источника данных: статический список (items_json) или сущность БД
- Для сущности: автоматически загружает данные через DatabaseService

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - source_type: "static" | "entity" | "query"
    - items_json: str (для source_type="static")
    - display_field: str (для source_type="entity")
    - value_field: str (для source_type="entity")
    - filter_expression: str (для source_type="entity")
    - order_by: str (для source_type="entity")
    - query: str (для source_type="query")
"""

# -----------------------------------------------------------------------------
# 7. MozartListBox (listbox.py)
# -----------------------------------------------------------------------------
"""
Наследник: QListWidget + BaseControl + DataSourceMixin
Назначение: Список (одиночный выбор)
Особенности:
- Аналогичен ComboBox по источникам данных
- currentItemChanged сигнал

Свойства для сериализации:
    - те же, что у MozartComboBox
"""

# -----------------------------------------------------------------------------
# 8. MozartOptionGroup (optiongroup.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget + BaseControl + DataSourceMixin
Назначение: Группа радиокнопок
Особенности:
- Динамическое создание радиокнопок из источника данных
- Свойство orientation: "vertical" | "horizontal"
- В режиме дизайна кнопки блокируются (WA_TransparentForMouseEvents)

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - source_type, items_json, display_field, value_field
    - orientation: str
"""

# -----------------------------------------------------------------------------
# 9. MozartReference (reference.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget + BaseControl
Назначение: Поле выбора ссылки на другую сущность
Особенности:
- Состоит из: QLineEdit (отображение), кнопка выбора, кнопка очистки
- Хранит instance_id целевой сущности
- Отображает значение из display_field

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - display_field: str (какое поле показывать)
    - selector_form: str (алиас формы выбора)

Пример использования:
    reference.set_value(123, "Москва")  # ID и отображаемое имя
"""

# -----------------------------------------------------------------------------
# 10. MozartButton (button.py)
# -----------------------------------------------------------------------------
"""
Наследник: QPushButton + BaseControl
Назначение: Кнопка
Особенности:
- Не хранит значение (get_value() возвращает None)
- Сигнал value_changed(True) при клике
- Используется для выполнения действий

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str (текст на кнопке)
"""

# -----------------------------------------------------------------------------
# 11. MozartLabel (label.py)
# -----------------------------------------------------------------------------
"""
Наследник: QLabel + BaseControl
Назначение: Статическая метка
Особенности:
- Не хранит значение, но может отображать данные (через set_value)
- Свойства: text_alignment ("left", "center", "right"), bold, font_size

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str
    - text_alignment: str
    - bold: bool
    - font_size: int
"""

# -----------------------------------------------------------------------------
# 12. MozartGrid (grid.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget + BaseControl
Назначение: Таблица (грид)
Особенности:
- Поддержка фильтрации (по всем колонкам)
- Поддержка сортировки
- columns_json описывает колонки: [{"field": "cname", "header": "Имя", "width": 150}]
- get_selected() возвращает выбранную строку (словарь)

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - columns_json: str
    - allow_filter: bool
    - allow_sort: bool
"""

# -----------------------------------------------------------------------------
# 13. MozartContainer (container.py)
# -----------------------------------------------------------------------------
"""
Наследник: QGroupBox + BaseControl
Назначение: Контейнер для группировки других контролов
Особенности:
- Имеет заголовок (setTitle)
- Содержит вертикальный layout
- Не хранит значение

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
"""

# -----------------------------------------------------------------------------
# 14. MozartTabContainer (tab_container.py)
# -----------------------------------------------------------------------------
"""
Наследник: QTabWidget + BaseControl
Назначение: Контейнер с вкладками
Особенности:
- tabs_json описывает вкладки: [{"label": "Основное"}, {"label": "Дополнительно"}]
- get_tab_layout(index) возвращает layout для добавления контролов

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - tabs_json: str
"""

# -----------------------------------------------------------------------------
# 15. MozartImageView (image_view.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget + BaseControl
Назначение: Отображение и выбор изображения
Особенности:
- Кнопки выбора файла и очистки
- Хранит путь к файлу (или None)
- Показывает превью изображения

Свойства для сериализации:
    - binding_field, entity_alias, is_required, is_readonly
    - label: str
"""

# -----------------------------------------------------------------------------
# 16. Form (form.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget
Назначение: Контейнер верхнего уровня для формы
Особенности:
- Управляет группой контролов через словарь _controls
- Отслеживает изменения (dirty) через сигнал form_modified
- Методы: load_data(data), get_data(), save(), rollback()
- Автоматически подключает сигналы контролов

Свойства:
    - form_id, form_alias, entity_alias, instance_id, readonly, title
    - is_modified, is_new
"""

# -----------------------------------------------------------------------------
# 17. FormContainer (form_container.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget
Назначение: MDI-контейнер для управления несколькими формами
Особенности:
- Два режима: 'mdi' (QMdiArea) или 'tabs' (QTabWidget)
- Сигналы: form_opened, form_closed, form_activated
- Методы: add_form(), remove_form(), get_active_form()

Режимы:
    - mdi: плавающие окна внутри главного
    - tabs: вкладки
"""

# -----------------------------------------------------------------------------
# 18. MozartForm (mozart_form.py)
# -----------------------------------------------------------------------------
"""
Наследник: QWidget
Назначение: Базовая форма для L3-клиента (рантайм)
Особенности:
- Используется в клиентском приложении для динамического создания форм
- Содержит контекстные свойства: entity_alias, instance_id, caller_form
- Поддерживает мостовое соединение с L2 (DataBridge)
- Методы: load_data(), save()

Отличие от Form:
    - Form — для дизайнера и конфигуратора
    - MozartForm — для рантайма (клиент)
"""

# -----------------------------------------------------------------------------
# ФАБРИКА СОЗДАНИЯ КОНТРОЛОВ
# -----------------------------------------------------------------------------
"""
create_control(control_type, parent=None, db=None, alis=None)

Параметры:
    - control_type: str (текстовое имя контрола: "textbox", "combobox", "grid" и т.д.)
    - parent: QWidget (родительский виджет)
    - db: DatabaseService (для загрузки данных в рантайме)
    - alis: str (алиас контрола, устанавливается через setObjectName)

Возвращает: экземпляр соответствующего контрола

Поддерживаемые типы:
    textbox, numberbox, datebox, checkbox, memo, combobox, listbox,
    optiongroup, imageview, reference, grid, container, group, tabcontainer,
    label, button
"""

# -----------------------------------------------------------------------------
# РЕЖИМЫ РАБОТЫ КОНТРОЛОВ
# -----------------------------------------------------------------------------
"""
Все контролы (и форма) имеют метод set_design_mode(design_mode: bool)

design_mode = True  -> режим дизайна (редактирование формы)
    - Контрол неактивен (disabled или readonly)
    - Не загружает данные из БД
    - Не реагирует на действия пользователя
    - Используется в дизайнере форм

design_mode = False -> режим рантайма (выполнение)
    - Контрол активен
    - Загружает данные через DatabaseService (если есть DataSourceMixin)
    - Реагирует на ввод пользователя
    - Используется в клиентском приложении
"""

# -----------------------------------------------------------------------------
# ПРИМЕР ИСПОЛЬЗОВАНИЯ В ДИЗАЙНЕРЕ
# -----------------------------------------------------------------------------
"""
# Создание контрола через фабрику
from controls import create_control
combo = create_control("combobox", parent=None, db=db, alis="city")
combo.set_design_mode(True)  # в дизайнере не загружаем данные

# Установка свойств (через инспектор)
combo.properties = {
    "source_type": "entity",
    "entity_alias": "city",
    "display_field": "cname",
    "x": 10, "y": 50, "width": 200, "height": 30
}

# В рантайме
combo.set_design_mode(False)
combo.load_items()  # загрузит города из БД
combo.set_value(123)  # выберет город с ID=123
"""

# -----------------------------------------------------------------------------
# ПРИМЕР JSON ДЛЯ СОХРАНЕНИЯ ФОРМЫ
# -----------------------------------------------------------------------------
"""
{
    "class": "MozartForm",
    "objectName": "PersonEdit",
    "windowTitle": "Редактирование персоны",
    "geometry": {"x": 0, "y": 0, "width": 600, "height": 400},
    "widgets": [
        {
            "class": "MozartTextBox",
            "name": "lastname",
            "properties": {
                "binding_field": "cLastName",
                "label": "Фамилия",
                "x": 10, "y": 50, "width": 200, "height": 30
            }
        },
        {
            "class": "MozartComboBox",
            "name": "city",
            "properties": {
                "source_type": "entity",
                "entity_alias": "city",
                "display_field": "cname",
                "binding_field": "city_id",
                "x": 10, "y": 90, "width": 200, "height": 30
            }
        },
        {
            "class": "MozartButton",
            "name": "btn_save",
            "properties": {
                "label": "Сохранить",
                "x": 500, "y": 350, "width": 80, "height": 30
            }
        }
    ]
}
"""

# -----------------------------------------------------------------------------
# СИСТЕМНЫЕ КЛАССЫ (не контролы, но используются вместе)
# -----------------------------------------------------------------------------
"""
BaseControl (base_control.py)
    - Миксин, добавляющий свойства binding_field, entity_alias, is_required, is_readonly
    - Методы set_value/get_value/is_dirty/reset

DataSourceMixin (data_source_mixin.py)
    - Миксин для контролов со списками (ComboBox, ListBox, OptionGroup)
    - Управление источниками данных (статический JSON, сущность БД, произвольный SQL)
"""