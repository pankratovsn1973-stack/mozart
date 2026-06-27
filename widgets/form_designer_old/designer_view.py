# widgets/form_designer_old/designer_view.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPainter
from .control_item_base import ControlItemBase
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class DesignerGraphicsView(QGraphicsView):
    """Кастомный View, принудительно забирающий стрелки и DEL у системы Qt."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusNextPrevChild(self, next_child):
        scene = self.scene()
        if scene:
            has_selected = len([i for i in scene.selectedItems() if isinstance(i, ControlItemBase)]) > 0
            has_context = getattr(scene, '_active_context_container', None) is not None
            if has_selected or has_context:
                return False
        return super().focusNextPrevChild(next_child)

    def keyPressEvent(self, event: QKeyEvent):
        scene = self.scene()
        if not scene:
            super().keyPressEvent(event)
            return

        key = event.key()

        # ВОССТАНОВЛЕНИЕ КНОПКИ DEL: Перехватываем Delete / Backspace
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selected_items = [i for i in scene.selectedItems() if isinstance(i, ControlItemBase)]

            for item in selected_items:
                registry = FormObjectsRegistry()
                control_id = registry.get_id_by_widget(item)

                # Защита: запрещаем удалять сам бланк формы кнопкой DEL
                if control_id in ("0", "form_root", "") or (
                        hasattr(item, 'control_type') and item.control_type == 'form'):
                    continue

                # 1. Удаляем контрол физически с графической сцены Qt
                if hasattr(scene, 'delete_control'):
                    scene.delete_control(control_id)
                else:
                    scene.removeItem(item)

                # 2. Полностью вычищаем его свойства из In-Memory СУБД (Таблицы 1 и 2)
                model = DesignerDataModel()
                for (map_cid, prop_name) in list(model.properties_instances.keys()):
                    if map_cid == control_id:
                        del model.properties_instances[(map_cid, prop_name)]
                for (map_cid, prop_name) in list(model.properties_delta.keys()):
                    if map_cid == control_id:
                        del model.properties_delta[(map_cid, prop_name)]

            # Переключаем фокус инспектора и отладочного грида обратно на форму
            if hasattr(self.parent(), 'property_panel') and self.parent().property_panel:
                self.parent().property_panel.set_form(self.parent())

            event.accept()
            return

        # Навигация стрелками клавиатуры
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            has_selected = len([i for i in scene.selectedItems() if isinstance(i, ControlItemBase)]) > 0
            has_context = getattr(scene, '_active_context_container', None) is not None

            if has_selected or has_context:
                scene.keyPressEvent(event)
                event.accept()
                return

        super().keyPressEvent(event)
