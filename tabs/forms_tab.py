# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/tabs/forms_tab.py

import json
from PySide6.QtWidgets import QMessageBox, QDialog
from .forms_tab_ui import FormsTabUI
from .forms.form_properties_dialog import FormPropertiesDialog
from .forms.form_wizard import FormWizard
from .forms_wizard_factory import FormsWizardFactory


class FormsTab(FormsTabUI):
    """Контроллер вкладки: управление жизненным циклом и атомарный UPSERT в PostgreSQL."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)

    def add_form(self):
        """Добавление новой формы."""
        reply = QMessageBox.question(
            self, self.translator.tr('question'), self.translator.tr('use_form_wizard'),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            wizard = FormWizard(self.db, parent=self)
            if wizard.exec() == QDialog.Accepted:
                self._create_form_from_wizard(wizard.get_result())
        else:
            dlg = FormPropertiesDialog(None, db=self.db)
            if dlg.exec() == QDialog.Accepted:
                self._save_form(dlg.get_data())

    def edit_form(self):
        """Редактирование формы."""
        form_id = self.get_selected_id()
        if not form_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_form'))
            return

        sql = "SELECT cname, calias, ientitytypeid, mstate_json FROM meta.forms WHERE id = %s"
        row = self.db.execute_query(sql, (form_id,))
        if not row or not isinstance(row, list) or len(row) == 0:
            return

        # ИСПРАВЛЕНО: Извлекаем атомарные поля из первой записи (row[0]) массива СУБД PostgreSQL
        db_record = row[0] if isinstance(row[0], (list, tuple)) else row

        # Защищаем типы данных от прорыва сырых массивов
        cname_val = db_record[0] if len(db_record) > 0 else " "
        calias_val = db_record[1] if len(db_record) > 1 else " "
        entity_val = db_record[2] if len(db_record) > 2 else None
        mstate_val = db_record[3] if len(db_record) > 3 else "{}"

        data = {
            "cname": str(cname_val).strip(),
            "calias": str(calias_val).strip(),
            "ientitytypeid": entity_val,
            "mstate_json": mstate_val
        }

        # Чтение геометрии бланка из mstate_json для корректного масштабирования при старте
        if mstate_val:
            try:
                if isinstance(mstate_val, str):
                    m_dict = json.loads(mstate_val)
                else:
                    m_dict = mstate_val
                geom = m_dict.get("geometry", {})
                if geom:
                    data["width"] = geom.get("width", 942)
                    data["height"] = geom.get("height", 928)
            except:
                pass

        dlg = FormPropertiesDialog(None, data, db=self.db, form_id=form_id)
        if dlg.exec() == QDialog.Accepted:
            self._save_form(dlg.get_data(), form_id)

    def delete_form(self):
        """Удаление формы."""
        form_id = self.get_selected_id()
        if not form_id:
            return
        res = self.db.execute_query("SELECT COUNT(*) FROM meta.form_elements WHERE formid = %s", (form_id,))
        count = res if res and isinstance(res, list) and len(res) > 0 else 0
        msg = self.translator.tr('confirm_delete_form')
        if count > 0:
            msg += f"\n\n{self.translator.tr('warning_form_has_elements')}: {count}"
        if QMessageBox.question(self, self.translator.tr('confirm_delete'), msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM meta.form_elements WHERE formid = %s", (form_id,), fetch=False)
            self.db.execute_query("DELETE FROM meta.forms WHERE id = %s", (form_id,), fetch=False)
            self.load_forms()

    def _save_form(self, data, form_id=None):
        """Сохраняет форму и её элементы в БД за один атомарный шаг с выводом сырого дампа."""
        mstate = data.get("mstate_json")
        if isinstance(mstate, dict):
            mstate = json.dumps(mstate, ensure_ascii=False)

        # Вывод очищенного дампа в консоль
        print("\n" + "=" * 80)
        print(f"📡 --- ДАМП СОХРАНЕНИЯ ERP-ФОРМЫ (ID в БД: {form_id}) ---")
        print(f"Имя формы (cname):  {data.get('cname')}")
        print(f"Алиас формы (calias): {data.get('calias')}")
        print(f"Сущность (entity id): {data.get('ientitytypeid')}")
        print("-" * 80)
        print("Сырой JSON-паспорт (mstate_json), отправляемый в meta.forms:")
        print(mstate)
        print("-" * 80)
        print(f"Количество контролов для meta.form_elements: {len(data.get('controls', []))}")
        for idx, ctrl in enumerate(data.get('controls', [])):
            print(
                f"  [{idx}] ID: {ctrl.get('id')}, ParentID: {ctrl.get('parentid')}, Alias: {ctrl.get('calias')}, Class: {ctrl.get('cclass')}, Geo: {ctrl.get('properties', {})}")
        print(f"Переданные ID на каскадное удаление (deleted_ids): {data.get('deleted_ids', [])}")
        print("=" * 80 + "\n")

        if form_id:
            sql = "UPDATE meta.forms SET cname=%s, calias=%s, ientitytypeid=%s, mstate_json=%s WHERE id=%s"
            self.db.execute_query(sql, (data["cname"], data["calias"], data["ientitytypeid"], mstate, form_id),
                                  fetch=False)
        else:
            sql = "INSERT INTO meta.forms (cname, calias, ientitytypeid, mstate_json) VALUES (%s, %s, %s, %s) RETURNING id"
            res = self.db.execute_query(sql, (data["cname"], data["calias"], data["ientitytypeid"], mstate))
            if res and isinstance(res, list) and len(res) > 0:
                form_id = res[0][0] if isinstance(res[0], (list, tuple)) else res[0]

        if form_id and "controls" in data:
            self._save_controls_upsert(form_id, data["controls"], data.get("deleted_ids", []))

        self.load_forms()
        return form_id

    def _save_controls_upsert(self, form_id, controls, deleted_ids=None):
        """Сохраняет все элементы, каскадно вычищая удаленные ветки через хранимую процедуру."""
        if deleted_ids and isinstance(deleted_ids, list):
            valid_ids = [int(x) for x in deleted_ids if str(x).isdigit()]
            if valid_ids:
                self.db.execute_query(
                    "SELECT meta.delete_form_elements_tree(%s, %s::int[]);",
                    (int(form_id), valid_ids),
                    fetch=False
                )

        active_ids = []
        form_element_node = None
        system_garbage_classes = ('formbackground', 'resizehandle', 'formbackgroundsignals', 'qlineedit', 'qpushbutton')

        # Первый проход: собираем существующие ID и находим узел формы
        for ctrl in controls:
            cclass_str = str(ctrl.get("cclass", " ")).lower()
            cid = str(ctrl.get("id", " ")).strip()

            if cclass_str in system_garbage_classes or cid in ('1', '840') or ctrl.get("calias") == "control_840":
                continue

            if cclass_str == "form":
                form_element_node = ctrl
                continue

            # Собираем только валидные числовые ID
            if cid.isdigit() and int(cid) > 0:
                active_ids.append(int(cid))

        # Обработка корневого элемента формы
        existing_form_el = self.db.execute_query(
            "SELECT id FROM meta.form_elements WHERE formid = %s AND cclass = 'form' LIMIT 1",
            (form_id,)
        )
        allocated_form_el_id = None
        if existing_form_el and isinstance(existing_form_el, list) and len(existing_form_el) > 0:
            allocated_form_el_id = int(existing_form_el[0][0])
            active_ids.append(allocated_form_el_id)
            if form_element_node:
                form_element_node["id"] = str(allocated_form_el_id)

        # Удаляем из БД всё, чего нет в новом списке (кроме новых элементов с id=0)
        if active_ids:
            placeholders = ", ".join(["%s"] * len(active_ids))
            self.db.execute_query(
                f"DELETE FROM meta.form_elements WHERE formid = %s AND id NOT IN ({placeholders})",
                tuple([form_id] + active_ids), fetch=False
            )
        else:
            self.db.execute_query("DELETE FROM meta.form_elements WHERE formid = %s", (form_id,), fetch=False)

        sql_upsert = """
            INSERT INTO meta.form_elements (id, formid, calias, cclass, mproperties_json, parentid, isortorder, lisactive)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true) 
            ON CONFLICT (id) DO UPDATE 
            SET calias=EXCLUDED.calias, cclass=EXCLUDED.cclass, mproperties_json=EXCLUDED.mproperties_json, 
                parentid=EXCLUDED.parentid, isortorder=EXCLUDED.isortorder, lisactive=true;
        """
        sql_insert = """
            INSERT INTO meta.form_elements (formid, calias, cclass, mproperties_json, parentid, isortorder, lisactive) 
            VALUES (%s, %s, %s, %s, %s, %s, true) RETURNING id;
        """

        # Сохраняем корневой элемент формы
        if form_element_node:
            properties = form_element_node.get('properties', {})
            if allocated_form_el_id:
                self.db.execute_query(sql_upsert, (allocated_form_el_id, form_id,
                                                   form_element_node.get('calias', 'OrdinaryDictionary'), 'form',
                                                   json.dumps(properties, ensure_ascii=False), None, 0), fetch=False)
            else:
                res = self.db.execute_query(sql_insert,
                                            (form_id, form_element_node.get('calias', 'OrdinaryDictionary'), 'form',
                                             json.dumps(properties, ensure_ascii=False), None, 0))
                if res and isinstance(res, list) and len(res) > 0:
                    form_element_node['id'] = str(res[0][0])

        # Сохраняем остальные контролы
        for idx, control in enumerate(controls):
            cclass_str = str(control.get('cclass', '')).lower()
            cid_str = str(control.get('id', '')).strip()

            if cclass_str == 'form' or cclass_str in system_garbage_classes or cid_str in ('1', '840'):
                continue

            properties = control.get('properties', {})
            raw_pid = control.get("parentid")

            # Если родитель — системная строка 'form_root', в базу пишем NULL или ID формы
            if raw_pid == "form_root" and form_element_node:
                db_pid = int(form_element_node.get('id')) if str(form_element_node.get('id')).isdigit() else None
            else:
                db_pid = int(raw_pid) if (raw_pid and str(raw_pid).isdigit()) else None

            # ✅ ОБРАБОТКА НОВЫХ ЭЛЕМЕНТОВ (id=0 или пустой)
            if cid_str.isdigit() and int(cid_str) > 0:
                self.db.execute_query(sql_upsert, (int(cid_str), form_id, control.get('calias', ''),
                                                   control.get('cclass', 'textbox'),
                                                   json.dumps(properties, ensure_ascii=False), db_pid, (idx + 1) * 10),
                                      fetch=False)
            else:
                # Новый элемент: делаем INSERT и получаем сгенерированный ID
                res = self.db.execute_query(sql_insert,
                                            (form_id, control.get('calias', ''), control.get('cclass', 'textbox'),
                                             json.dumps(properties, ensure_ascii=False), db_pid, (idx + 1) * 10))
                if res and isinstance(res, list) and len(res) > 0:
                    new_id = res[0][0] if isinstance(res[0], (list, tuple)) else res[0]
                    control['id'] = str(new_id)
                    print(f"[SAVE] Создан новый контрол: {control.get('calias')} -> ID={new_id}")

    def _create_form_from_wizard(self, result):
        """Создаёт форму по результатам мастера, задействуя внешнюю фабрику."""
        form_json = FormsWizardFactory.generate_grid_json(result, self.db) if result.get('is_grid', False) \
            else FormsWizardFactory.generate_edit_json(result, self.db)

        self._save_form({
            'cname': result.get('cname', 'Новая форма от Мастера'),
            'calias': result.get('calias', 'wizard_form_alias'),
            'ientitytypeid': result.get('ientitytypeid'),
            'mstate_json': form_json.get('mstate_json', {}),
            'controls': form_json.get('controls', [])
        })