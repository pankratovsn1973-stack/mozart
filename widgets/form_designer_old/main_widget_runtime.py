# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/main_widget_runtime.py

from PySide6.QtWidgets import QGraphicsScene
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel
from .designer_serializer import DesignerSerializer


class FormDesignerRuntime:
    """Изолированный сервис обработки методов рантайма бланка формы."""

    @staticmethod
    def load_form_template(designer_instance, width, height, title, controls_data=None):
        """Инициализирует шаблон бланка формы и наполняет In-Memory СУБД."""
        if designer_instance.property_panel:
            designer_instance.property_panel.block_sync = True

        designer_instance.runtime_form = designer_instance.scene.init_form(width, height, title)

        if designer_instance.db and designer_instance.form_id:
            try:
                res = designer_instance.db.execute_query(
                    "SELECT mstate_json FROM meta.forms WHERE id = %s",
                    (designer_instance.form_id,)
                )
                if res:
                    designer_instance._raw_mstate_json = str(res)
            except Exception as e:
                print(f"[Runtime] Ошибка чтения mstate_json: {e}")

        explicit_fid = "form_root"
        FormObjectsRegistry().register_object(designer_instance.runtime_form, explicit_id=explicit_fid)

        model = DesignerDataModel()
        model.properties_instances[(explicit_fid, "width")] = str(int(width))
        model.properties_instances[(explicit_fid, "height")] = str(int(height))
        model.properties_instances[(explicit_fid, "x")] = "0"
        model.properties_instances[(explicit_fid, "y")] = "0"
        model.properties_instances[(explicit_fid, "title")] = str(title)
        model.properties_instances[(explicit_fid, "form_alias")] = "OrdinaryDictionary"

        if controls_data:
            designer_instance.scene.load_controls(controls_data)

        # Переводим инспектор в ленивый режим: очищаем и ждем первого клика по сетке/контролу
        designer_instance.property_panel.clearContents()
        designer_instance.property_panel.setRowCount(0)
        designer_instance.property_panel.current_control_id = None
        designer_instance.property_panel.block_sync = False

        if designer_instance.view:
            designer_instance.view.resetCachedContent()

        designer_instance.scene.invalidate(
            designer_instance.scene.sceneRect(),
            QGraphicsScene.SceneLayer.BackgroundLayer
        )
        designer_instance.scene.update()

        DesignerSerializer.update_debug_grid(designer_instance.db_debug_table, explicit_fid)
        return designer_instance.runtime_form

    @staticmethod
    def sync_role(designer_instance, role_alias):
        """Синхронизация роли бизнес-формы."""
        if designer_instance.runtime_form:
            fid = "form_root"
            setattr(designer_instance.runtime_form, 'form_role', role_alias)
            DesignerDataModel().set_value(fid, "form_role", role_alias, is_delta=True)
            designer_instance.property_panel.set_form(designer_instance)
            DesignerSerializer.update_debug_grid(designer_instance.db_debug_table, fid)

    @staticmethod
    def sync_entity(designer_instance, entity_alias):
        """Синхронизация привязки сущности к бланку формы."""
        if designer_instance.runtime_form:
            fid = "form_root"
            designer_instance.runtime_form.entity_alias = entity_alias
            DesignerDataModel().set_value(fid, "entity_alias", entity_alias, is_delta=True)
            designer_instance.property_panel.set_form(designer_instance)
            DesignerSerializer.update_debug_grid(designer_instance.db_debug_table, fid)
