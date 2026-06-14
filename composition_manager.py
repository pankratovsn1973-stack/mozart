# composition_manager.py
from PySide6.QtWidgets import QMessageBox
from database import DatabaseService


class CompositionManager:
    def __init__(self, db=None, parent_widget=None):
        self.db = db or DatabaseService()
        self.parent = parent_widget

    def _get_entity_cname(self, entity_id: int) -> str:
        """Возвращает системное имя (cname) сущности, приводит к нижнему регистру."""
        res = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (entity_id,))
        if not res:
            raise ValueError(f"Сущность с id {entity_id} не найдена")
        return res[0][0].lower()

    def ensure_ext_table_and_field(self, child_entity_id, link_field_name):
        # Получаем cname дочерней сущности
        child_cname = self._get_entity_cname(child_entity_id)
        ext_table = f"ext.ext_{child_cname}"

        # Проверяем существование таблицы
        check_tab = self.db.execute_query("SELECT to_regclass(%s)", (ext_table,))
        if not check_tab or not check_tab[0][0]:
            sql_create = f"""
                CREATE TABLE IF NOT EXISTS {ext_table} (
                    id SERIAL PRIMARY KEY,
                    versionid INTEGER NOT NULL REFERENCES data.entity_versions(id) ON DELETE CASCADE
                )
            """
            self.db.execute_query(sql_create, fetch=False)

        # Проверяем наличие поля в meta.fields
        check_field = self.db.execute_query(
            "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
            (child_entity_id, link_field_name)
        )
        if not check_field:
            ins = self.db.execute_query(
                """INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, lisindexed, status_id)
                   VALUES (%s, %s, 'I', %s, true, 1) RETURNING id""",
                (child_entity_id, link_field_name, f"FK: {link_field_name}")
            )
            if ins:
                field_id = ins[0][0]
                self.db.execute_procedure("meta.p_field_sync", (field_id,))
        return True

    def add_composition(self, parent_entityid, child_entityid, role_id, link_field, sortorder=10):
        if not self.ensure_ext_table_and_field(child_entityid, link_field):
            if self.parent:
                QMessageBox.warning(self.parent, "Ошибка", "Не удалось подготовить ext-таблицу/поле")
            return False
        check = self.db.execute_query(
            """SELECT id FROM meta.entity_composition
               WHERE parent_entityid=%s AND child_entityid=%s AND role_id=%s""",
            (parent_entityid, child_entityid, role_id)
        )
        if check:
            if self.parent:
                QMessageBox.warning(self.parent, "Ошибка", "Такая связь уже существует")
            return False
        sql = """INSERT INTO meta.entity_composition
                 (parent_entityid, child_entityid, role_id, c_link_fieldname, isortorder)
                 VALUES (%s, %s, %s, %s, %s)"""
        self.db.execute_query(sql, (parent_entityid, child_entityid, role_id, link_field, sortorder), fetch=False)
        return True

    def update_composition(self, comp_id, parent_entityid, child_entityid, role_id, link_field, sortorder=10):
        if not self.ensure_ext_table_and_field(child_entityid, link_field):
            if self.parent:
                QMessageBox.warning(self.parent, "Ошибка", "Не удалось подготовить ext-таблицу/поле")
            return False
        check = self.db.execute_query(
            """SELECT id FROM meta.entity_composition
               WHERE parent_entityid=%s AND child_entityid=%s AND role_id=%s AND id!=%s""",
            (parent_entityid, child_entityid, role_id, comp_id)
        )
        if check:
            if self.parent:
                QMessageBox.warning(self.parent, "Ошибка", "Такая связь уже существует")
            return False
        sql = """UPDATE meta.entity_composition SET
                    parent_entityid=%s, child_entityid=%s, role_id=%s,
                    c_link_fieldname=%s, isortorder=%s
                 WHERE id=%s"""
        self.db.execute_query(sql, (parent_entityid, child_entityid, role_id, link_field, sortorder, comp_id), fetch=False)
        return True

    def delete_composition(self, comp_id):
        self.db.execute_query("DELETE FROM meta.entity_composition WHERE id=%s", (comp_id,), fetch=False)