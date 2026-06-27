# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/tabs/forms/form_properties_dialog.py

import json
from PySide6.QtWidgets import QDialog, QMessageBox
from .property_dialog_ui import PropertyDialogUI


class FormPropertiesDialog(PropertyDialogUI):
    """Диалог редактирования метаданных и визуального конструирования ERP-формы."""

    def __init__(self, parent=None, data=None, db=None, form_id=None):
        super().__init__(parent, db, form_id)
        self.data = data if data else {}
        self.deleted_control_ids = []  # Хранилище идентификаторов удаленных объектов
        self._load_data()

    def _load_data(self):
        """Безопасная распаковка данных с защитой от передачи сырых list-массивов из БД."""
        if not self.data:
            return

        raw_cname = self.data.get("cname", " ")
        raw_calias = self.data.get("calias", " ")

        if isinstance(raw_cname, list) and len(raw_cname) > 0:
            sub = raw_cname
            clean_cname = str(sub) if isinstance(sub, (list, tuple)) else str(sub)
        else:
            clean_cname = str(raw_cname)

        if isinstance(raw_calias, list) and len(raw_calias) > 0:
            sub = raw_calias
            clean_calias = str(sub) if isinstance(sub, (list, tuple)) and len(sub) > 1 else str(sub)
        else:
            clean_calias = str(raw_calias)

        self.edit_cname.setText(clean_cname)
        self.edit_calias.setText(clean_calias)

        entity_id = self.data.get("ientitytypeid")
        if isinstance(entity_id, list) and len(entity_id) > 0:
            sub = entity_id
            entity_id = sub if isinstance(sub, (list, tuple)) and len(sub) > 2 else sub

        if entity_id and hasattr(self, 'edit_ientitytypeid') and self.edit_ientitytypeid:
            idx = self.edit_ientitytypeid.findData(int(entity_id))
            if idx >= 0:
                self.edit_ientitytypeid.setCurrentIndex(idx)

        mstate = self.data.get("mstate_json")
        if isinstance(mstate, list) and len(mstate) > 0:
            sub = mstate
            mstate = sub if isinstance(sub, (list, tuple)) and len(sub) > 3 else sub

        controls_list = []
        if mstate:
            try:
                if isinstance(mstate, str):
                    mstate_dict = json.loads(mstate)
                else:
                    mstate_dict = mstate

                # ВХОДНОЙ ФИЛЬТР: Очищаем старый мусор в mstate_json при открытии формы
                raw_controls = mstate_dict.get("controls", [])
                system_garbage_classes = ('formbackground', 'resizehandle', 'qlineedit', 'qpushbutton')

                for ctrl in raw_controls:
                    if str(ctrl.get("cclass", " ")).lower() not in system_garbage_classes:
                        controls_list.append(ctrl)
            except Exception as e:
                print(f"[FormPropertiesDialog] Ошибка парсинга mstate_json: {e}")

        if self.form_id and self.db:
            sql = """
                SELECT id, parentid, calias, cclass, mproperties_json 
                FROM meta.form_elements 
                WHERE formid = %s 
                ORDER BY isortorder, id
            """
            rows = self.db.execute_query(sql, (self.form_id,))
            if rows and isinstance(rows, list) and len(rows) > 0:
                controls_list = []
                for row in rows:
                    eid, pid, calias, cclass, props_json = row
                    try:
                        props = json.loads(props_json) if props_json else {}
                    except:
                        props = {}

                    controls_list.append({
                        "id": str(eid),
                        "parentid": str(pid) if pid else None,
                        "calias": str(calias),
                        "cclass": str(cclass),
                        "properties": props
                    })

        if controls_list and hasattr(self, 'designer') and self.designer:
            w = int(self.data.get("width", 942))
            h = int(self.data.get("height", 928))
            t = clean_cname if clean_cname else "СтандСправочник"

            self.designer.init_form(w, h, t)
            if hasattr(self.designer, 'scene') and self.designer.scene:
                self.designer.scene.load_controls(controls_list)
                # Подключаем каскадный трекер удаления элементов холста
                self.designer.scene.control_deleted.connect(self._on_control_deleted)

    def _on_control_deleted(self, control_id):
        """Слот-накопитель удаленных идентификаторов для передачи СУБД."""
        cid_str = str(control_id).strip()
        if cid_str.isdigit() and int(cid_str) > 0:
            val_id = int(cid_str)
            if val_id not in self.deleted_control_ids:
                self.deleted_control_ids.append(val_id)

    def _get_visual_designer_data(self):
        """
        Адаптер для сбора данных из нового FormDesignerScene (Unit of Work).
        Возвращает структуру, совместимую со старым форматом forms_tab.py.
        """
        designer = getattr(self, 'designer', None)
        scene = getattr(designer, 'scene', None) if designer else None

        if not scene or not hasattr(scene, 'prepare_save_data'):
            return None

        uow_data = scene.prepare_save_data()

        # Объединяем inserts и updates в единый список controls
        all_controls = []
        for ctrl in uow_data.get('inserts', []):
            all_controls.append(ctrl)
        for ctrl in uow_data.get('updates', []):
            all_controls.append(ctrl)

        # Добавляем удаленные ID из UOW к локальному буферу диалога
        for did in uow_data.get('deletes', []):
            if did not in self.deleted_control_ids:
                self.deleted_control_ids.append(did)

        return {
            "controls": all_controls,
            "deleted_ids": list(self.deleted_control_ids),
            "mstate_json": {}  # Заполняется ниже в get_data
        }

    def get_data(self) -> dict:
        """Собирает измененные данные и пачку удаленных ID для рекурсивной хранимой процедуры."""
        cname = self.edit_cname.text().strip()
        calias = self.edit_calias.text().strip()

        entity_id = None
        if hasattr(self, 'edit_ientitytypeid') and self.edit_ientitytypeid:
            entity_id = self.edit_ientitytypeid.currentData()

        if not cname or not calias:
            QMessageBox.warning(self, "Ошибка", "Поля 'Имя' и 'Алиас' обязательны для заполнения!")
            return {}

        # ✅ Пытаемся получить данные из нового визуального дизайнера
        designer_payload = self._get_visual_designer_data()

        # Fallback на старый механизм, если новый дизайнер не активен
        if not designer_payload:
            if hasattr(self, 'designer') and self.designer:
                designer_payload = self.designer.get_form_data()
            else:
                designer_payload = {"mstate_json": {}, "controls": [], "deleted_ids": []}

        # Формируем итоговый mstate_json
        mstate_json = {
            "geometry": {
                "width": int(
                    getattr(self.designer, 'form_width', 942) if hasattr(self.designer, 'form_width') else 942),
                "height": int(
                    getattr(self.designer, 'form_height', 928) if hasattr(self.designer, 'form_height') else 928)
            },
            "controls": designer_payload.get("controls", [])
        }

        return {
            "cname": cname,
            "calias": calias,
            "ientitytypeid": entity_id,
            "mstate_json": mstate_json,
            "controls": designer_payload.get("controls", []),
            "deleted_ids": designer_payload.get("deleted_ids", self.deleted_control_ids)
        }