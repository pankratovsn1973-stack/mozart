# /home/sergey/Documents/configurate/widgets/form_designer_old/property_editor_sync.py
# -*- coding: utf-8 -*-

"""
Модуль: Компонент синхронизации геометрии и фокуса инспектора свойств.

Роль в архитектуре Mozart ERP:
    - Обеспечивает синхронизацию между инспектором свойств и сценой.
    - Управляет фокусом и выделением контролов.
    - Интегрируется с реестром для поиска объектов.

Ключевые зависимости:
    - PropertyEditorBase - базовый UI инспектора.
    - DesignerDataModel - in-memory хранилище.
    - FormObjectsRegistry - реестр объектов.
"""

from PySide6.QtCore import Qt
from .property_editor_base import PropertyEditorBase
from .designer_data_model import DesignerDataModel
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry


class PropertyEditorSync(PropertyEditorBase):
    """
    Компонент синхронизации геометрии, управляющий защитными барьерами фокуса.

    Назначение:
        - Синхронизация инспектора с выбранным контролом.
        - Обновление геометрии при изменении размеров.
        - Управление фокусом.

    Ключевые свойства:
        - current_control_id: str - ID текущего контрола.
        - current_item: ControlItem - Текущий выбранный контрол.
        - _designer_ref: FormDesigner - Ссылка на дизайнер.
        - block_sync: bool - Блокировка синхронизации.

    Основные методы:
        - set_control() - Установка контрола для инспектирования.
        - set_form() - Установка формы для инспектирования.
        - update_geometry_values() - Обновление геометрии.
    """

    def set_control(self, control_item):
        """
        Слот переключения фокуса инспектора на выбранный элемент холста.

        Args:
            control_item: ControlItem - Выбранный контрол
        """
        registry = FormObjectsRegistry()

        if not control_item:
            self.current_control_id = "form_root"
            self.current_item = None
            self._reload_properties_from_model()
            return

        if isinstance(control_item, list):
            control_item = control_item[0] if control_item else None
            if not control_item:
                self.set_control(None)
                return

        self.current_item = control_item
        self.current_control_id = registry.get_id_by_widget(control_item)

        if self.current_control_id == "unknown":
            # Если контрол не найден в реестре, пробуем зарегистрировать
            explicit_id = getattr(control_item, 'control_id', None)
            if explicit_id:
                self.current_control_id = registry.register_object(
                    control_id=explicit_id,
                    widget_obj=control_item,
                    parentid=None,
                    full_path="",
                    calias=control_item.objectName(),
                    cclass=control_item.control_type
                )

        self._reload_properties_from_model()

    def set_form(self, parent_designer):
        """
        Принудительная жесткая установка фокуса инспектора на бланк формы.

        Args:
            parent_designer: FormDesigner - Экземпляр дизайнера
        """
        self._designer_ref = parent_designer
        registry = FormObjectsRegistry()

        self.current_control_id = "form_root"
        self.current_item = None

        if parent_designer and getattr(parent_designer, 'runtime_form', None):
            # ==================== ИСПРАВЛЕНИЕ ====================
            # Регистрация формы в реестре с новой сигнатурой
            registry.register_object(
                control_id="form_root",
                widget_obj=parent_designer.runtime_form,
                parentid=None,
                full_path="",
                calias="OrdinaryDictionary",
                cclass="form"
            )

        self._reload_properties_from_model()

    def update_geometry_values(self, x, y, width, height, sender_id: str = None):
        """
        Обновление геометрических свойств в инспекторе.

        Args:
            x: int - Координата X
            y: int - Координата Y
            width: int - Ширина
            height: int - Высота
            sender_id: str - ID отправителя (для проверки контекста)
        """
        if self.block_sync or not self.current_control_id:
            return

        registry = FormObjectsRegistry()

        is_form_focused = (str(self.current_control_id) in ("0", "form_root"))
        focused_widget = registry.get_widget_by_id(str(self.current_control_id))
        if focused_widget and focused_widget.__class__.__name__ == "FormBackground":
            is_form_focused = True

        is_sender_form = (str(sender_id) in ("0", "form_root"))
        sender_widget = registry.get_widget_by_id(str(sender_id))
        if sender_widget and sender_widget.__class__.__name__ == "FormBackground":
            is_sender_form = True

        if is_form_focused and sender_id and not is_sender_form:
            return

        if not is_form_focused and sender_id and str(sender_id) != str(self.current_control_id):
            return

        self.block_sync = True
        geo_map = {"x": str(int(x)), "y": str(int(y)), "width": str(int(width)), "height": str(int(height))}
        model = DesignerDataModel()

        model.set_value(self.current_control_id, "x", geo_map["x"])
        model.set_value(self.current_control_id, "y", geo_map["y"])
        model.set_value(self.current_control_id, "width", geo_map["width"])
        model.set_value(self.current_control_id, "height", geo_map["height"])

        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            if name_item:
                prop_name = name_item.data(Qt.ItemDataRole.UserRole)
                if prop_name in geo_map:
                    val_item = self.item(row, 1)
                    if val_item:
                        val_item.setText(geo_map[prop_name])

        self.block_sync = False