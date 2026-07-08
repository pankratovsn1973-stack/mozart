# /home/sergey/Documents/configurate/widgets/form_designer_old/property_editor_base.py
# -*- coding: utf-8 -*-

"""
Модуль: Базовый UI-компонент инспектора свойств.

Роль в архитектуре Mozart ERP:
    - Отображение свойств контролов и формы в табличном виде.
    - Интеграция с DesignerDataModel для чтения свойств.
    - Поддержка различных типов данных (строка, число, булево).
    - Базовая логика загрузки свойств из модели.

Ключевые зависимости:
    - PropertyTableWidget - базовый табличный виджет.
    - DesignerDataModel - in-memory хранилище свойств.
    - FormObjectsRegistry - реестр объектов.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem
from .property_table import PropertyTableWidget
from .designer_data_model import DesignerDataModel
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry


class PropertyEditorBase(PropertyTableWidget):
    """
    Базовый UI-компонент инспектора, отвечающий только за чистую отрисовку ячеек таблицы.

    Назначение:
        - Отображение свойств в таблице.
        - Загрузка свойств из DesignerDataModel.
        - Поддержка разных типов данных.

    Ключевые свойства:
        - current_item: ControlItem - Текущий выбранный контрол.
        - current_control_id: str - ID текущего контрола.
        - _designer_ref: FormDesigner - Ссылка на дизайнер.
        - block_sync: bool - Блокировка синхронизации.

    Основные методы:
        - _reload_properties_from_model() - Загрузка свойств из модели.
        - add_property_row() - Добавление строки свойства.
    """

    def __init__(self, parent=None):
        """
        Инициализация инспектора свойств.

        Args:
            parent: QWidget - Родительский виджет
        """
        super().__init__(parent)
        self.current_item = None
        self.current_control_id = None
        self._designer_ref = None

    def _reload_properties_from_model(self):
        """
        Вычитка строк инспектора из СУБД памяти с жестким обособлением пространства формы form_root.
        """
        self.block_sync = True
        self.clearContents()
        self.setRowCount(0)

        model = DesignerDataModel()
        cid = str(self.current_control_id).strip() if self.current_control_id else "form_root"
        registry = FormObjectsRegistry()

        # Определяем, форма это или контрол
        is_form_focused = (cid in ("0", "form_root"))
        focused_widget = registry.get_widget_by_id(cid)
        if focused_widget and focused_widget.__class__.__name__ == "FormBackground":
            is_form_focused = True

        # ==================== ИСПРАВЛЕНИЕ ====================
        # Список свойств для формы
        if is_form_focused:
            props_to_load = ["form_alias", "title", "x", "y", "width", "height"]
            cid = "form_root"
        else:
            # Список свойств для контрола
            # parent_alias - вычисляется отдельно
            props_to_load = ["control_id", "control_type", "form_alias", "x", "y", "width", "height",
                             "label", "binding_field", "entity_alias", "display_field",
                             "selector_form", "is_required", "is_readonly"]

        for prop_name in props_to_load:
            meta = model.get_metadata(prop_name)
            display_label = meta["label"]

            # parent_alias - специальный случай
            if prop_name == "form_alias" and is_form_focused:
                display_label = "Алиас формы"
            elif prop_name == "parent_alias":
                display_label = "Владелец контрола"

            # Определяем read-only свойства
            readonly = False
            if prop_name in ("control_id", "control_type"):
                readonly = True
            if is_form_focused and prop_name in ("x", "y", "width", "height"):
                readonly = False  # Геометрию формы можно менять

            # Получаем значение свойства
            if prop_name == "control_id":
                raw_val = cid
            elif prop_name == "control_type":
                raw_val = model.get_value(cid, "control_type")
                if not raw_val:
                    if self.current_item and getattr(self.current_item, 'objectName', lambda: '')() == 'txt_of_ref':
                        raw_val = "textbox"
                    elif self.current_item and hasattr(self.current_item, 'control_type'):
                        raw_val = str(self.current_item.control_type)
                    elif self.current_item:
                        raw_val = str(self.current_item.__class__.__name__).lower()
                        if raw_val == "qlabel":
                            raw_val = "textbox"
                    else:
                        raw_val = "textbox"
            elif prop_name == "parent_alias":
                # ==================== ИСПРАВЛЕНИЕ ====================
                # Автоматически вычисляем алиас родительского контейнера
                raw_val = "form_root"
                # Ищем метаданные текущего контрола
                meta_reg = registry.get_meta_by_id(cid)
                if meta_reg:
                    pid = meta_reg.get("parentid")  # ИСПРАВЛЕНО: parentid вместо parent_id
                    if pid and pid != "form_root":
                        # Пытаемся найти алиас родителя
                        parent_meta = registry.get_meta_by_id(str(pid))
                        if parent_meta:
                            raw_val = parent_meta.get("calias", f"control_{pid}")
                        else:
                            # Если родитель не найден в реестре, пробуем через модель
                            raw_val = model.get_value(str(pid), "form_alias") or f"control_{pid}"
                else:
                    # Если метаданные не найдены, пробуем через модель
                    raw_val = model.get_value(cid, "parent_alias") or "form_root"
            else:
                raw_val = model.get_value(cid, prop_name)

            # Fallback для геометрии формы
            if not raw_val and is_form_focused:
                if self._designer_ref and getattr(self._designer_ref, 'runtime_form', None):
                    form_obj = self._designer_ref.runtime_form
                    if prop_name == "x":
                        raw_val = "0"
                    elif prop_name == "y":
                        raw_val = "0"
                    elif prop_name == "width":
                        raw_val = str(int(form_obj.width))
                    elif prop_name == "height":
                        raw_val = str(int(form_obj.height))
                    elif prop_name == "title":
                        raw_val = getattr(form_obj, 'title', "СтандСправочник")
                    elif prop_name == "form_alias":
                        raw_val = getattr(form_obj, 'form_alias', "OrdinaryDictionary")

            # Если значение все еще пустое, ставим заглушку
            if not raw_val:
                if prop_name == "form_alias":
                    raw_val = "OrdinaryDictionary"
                elif prop_name == "title":
                    raw_val = "СтандСправочник"
                elif prop_name in ("x", "y"):
                    raw_val = "0"
                elif prop_name in ("width", "height"):
                    raw_val = "100" if prop_name == "width" else "30"
                elif prop_name == "control_type":
                    raw_val = "textbox"
                else:
                    raw_val = ""

            # Добавляем строку в таблицу
            row_idx = self.rowCount()
            self.insertRow(row_idx)

            label_item = QTableWidgetItem(str(display_label))
            label_item.setData(Qt.ItemDataRole.UserRole, prop_name)
            if readonly:
                label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.setItem(row_idx, 0, label_item)

            val_item = QTableWidgetItem(str(raw_val))
            if readonly:
                val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                val_item.setBackground(Qt.GlobalColor.lightGray)
            self.setItem(row_idx, 1, val_item)

        self.block_sync = False

    def set_control(self, control_item):
        """
        Установка контрола для инспектирования.

        Args:
            control_item: ControlItem - Контрол для инспектирования
        """
        self.current_item = control_item
        if control_item:
            registry = FormObjectsRegistry()
            self.current_control_id = registry.get_id_by_widget(control_item)
            if self.current_control_id == "unknown":
                self.current_control_id = getattr(control_item, 'control_id', None)
        else:
            self.current_control_id = "form_root"
        self._reload_properties_from_model()

    def set_form(self, parent_designer):
        """
        Установка формы для инспектирования.

        Args:
            parent_designer: FormDesigner - Экземпляр дизайнера
        """
        self._designer_ref = parent_designer
        self.current_control_id = "form_root"
        self.current_item = None
        self._reload_properties_from_model()