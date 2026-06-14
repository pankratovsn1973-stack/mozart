# mozart_import/utils/ext_helper.py
# -*- coding: utf-8 -*-

from database import DatabaseService


class ExtHelper:
    """Вспомогательный класс для работы с ext-таблицами и полями."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def get_ext_table_name(self, entity_alias: str) -> str:
        return f"ext.ext_{entity_alias.lower()}"

    def _add_system_column(self, ext_table: str, column_name: str, column_type: str, alias: str = None):
        """Добавляет служебную колонку в ext-таблицу (без создания записи в meta.fields)."""
        self.db.execute_query(
            f"ALTER TABLE {ext_table} ADD COLUMN IF NOT EXISTS {column_name} {column_type}",
            fetch=False
        )
        if column_name == 'sourceid' and alias:
            self.db.execute_query(
                f"CREATE INDEX IF NOT EXISTS ix_{alias}_sourceid ON {ext_table} (sourceid)",
                fetch=False
            )

    def ensure_ext_table(self, entity_id: int, entity_cname: str, sourceid_type: str = 'TEXT') -> str:
        """Проверяет существование ext-таблицы, создаёт при необходимости."""
        ext_table = f"ext.ext_{entity_cname.lower()}"

        check = self.db.execute_query("SELECT to_regclass(%s)", (ext_table,))
        table_exists = check and check[0][0]

        if not table_exists:
            sql = f"""
                CREATE TABLE {ext_table} (
                    id SERIAL PRIMARY KEY,
                    versionid INTEGER NOT NULL REFERENCES data.entity_versions(id) ON DELETE CASCADE
                )
            """
            self.db.execute_query(sql, fetch=False)
            self._add_system_column(ext_table, 'sourceid', sourceid_type, entity_cname.lower())
            self._add_system_column(ext_table, 'data_hash', 'varchar(32)')

        return ext_table

    def ensure_field(self, entity_id: int, field_name: str, field_type: str = 'C',
                     calias: str = None, ref_entity_id: int = None,
                     ref_class_id: int = None, length: int = 255) -> int:
        """
        Создаёт поле в meta.fields и вызывает p_field_sync.
        Поддерживает создание ссылочных полей с ref_entitytype_id или ref_class_id.
        """
        if field_name in ('id', 'versionid', 'sourceid', 'data_hash'):
            raise ValueError(f"Название поля '{field_name}' зарезервировано для системных колонок")

        if calias is None:
            calias = field_name.capitalize()

        # Проверяем существование
        existing = self.db.execute_query(
            "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
            (entity_id, field_name)
        )
        if existing:
            return existing[0][0]

        # Для ссылочного типа
        if field_type == 'R':
            # Если есть ref_class_id, но нет ref_entity_id, пока оставляем NULL
            # Пользователь сможет выбрать конкретную сущность позже в интерфейсе
            ref_id = ref_entity_id
            if ref_id is None and ref_class_id is not None:
                # Временно оставляем NULL, позже можно будет заполнить
                ref_id = None

            res = self.db.execute_query(
                """INSERT INTO meta.fields
                   (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, ref_entitytypeid, status_id, is_system)
                   VALUES (%s, %s, 'R', %s, %s, %s, %s, 1, False)
                   RETURNING id""",
                (entity_id, field_name, calias, 0, True, ref_id)
            )
        else:
            res = self.db.execute_query(
                """INSERT INTO meta.fields
                   (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id, is_system)
                   VALUES (%s, %s, %s, %s, %s, %s, 1, False)
                   RETURNING id""",
                (entity_id, field_name, field_type, calias, length, True)
            )

        if res:
            field_id = res[0][0]
            self.db.execute_procedure("meta.p_field_sync", (field_id,))
            return field_id
        return None

    def update_field_reference(self, field_id: int, new_ref_entity_id: int) -> bool:
        """
        Обновляет целевую сущность для ссылочного поля.
        Используется, когда пользователь выбирает конкретную сущность из класса.
        """
        try:
            self.db.execute_query(
                "UPDATE meta.fields SET ref_entitytypeid = %s WHERE id = %s",
                (new_ref_entity_id, field_id), fetch=False
            )
            self.db.execute_procedure("meta.p_field_sync", (field_id,))
            return True
        except Exception as e:
            print(f"Ошибка обновления ссылки: {e}")
            return False