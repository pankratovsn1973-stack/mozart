# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/property_editor.py

from PySide6.QtCore import Signal
from .property_editor_sync import PropertyEditorSync
from .designer_data_model import DesignerDataModel
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry


class PropertyEditor(PropertyEditorSync):
    """Главный координатор инспектора свойств, связывающий UI, логику барьеров и модель метаданных."""
    property_changed = Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cell_value_committed.connect(self._on_property_value_committed)

    def _on_property_value_committed(self, prop_name: str, converted_value):
        """Запись изменений из UI-ячейки инспектора в локальную СУБД в памяти (буфер дельты)."""
        if not self.current_control_id:
            return

        DesignerDataModel().set_value(self.current_control_id, prop_name, str(converted_value), is_delta=True)

        from .property_applier import PropertyApplier
        registry = FormObjectsRegistry()

        is_form = False
        target_widget = registry.get_widget_by_id(str(self.current_control_id))

        if target_widget and target_widget.__class__.__name__ == "FormBackground":
            is_form = True
        if str(self.current_control_id) in ("0", "form_root"):
            is_form = True

        if is_form:
            if self._designer_ref and getattr(self._designer_ref, 'runtime_form', None):
                # Напрямую прокидываем измененную геометрию и параметры в инстанс бланка формы
                PropertyApplier.apply_to_form(self._designer_ref.runtime_form, prop_name, converted_value)
                self._designer_ref.runtime_form.update()
        else:
            if self.current_item:
                if isinstance(self.current_item, ControlItemBase):
                    PropertyApplier.apply_to_control(self.current_item, prop_name, converted_value)
                else:
                    if hasattr(self.current_item, prop_name):
                        try:
                            setattr(self.current_item, prop_name, converted_value)
                        except:
                            pass

        self.property_changed.emit(self.current_control_id, prop_name, converted_value)
