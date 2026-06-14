# mozart_import/utils/field_creator.py
# -*- coding: utf-8 -*-

from database import DatabaseService


class FieldCreator:
    def __init__(self, db: DatabaseService):
        self.db = db

    def create_fields(self, entity_id: int, fields: list) -> list:
        created_ids = []
        for f in fields:
            exists = self.db.execute_query(
                "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
                (entity_id, f['cfieldname'])
            )
            if exists:
                created_ids.append(exists[0][0])
                continue

            cfieldname = f['cfieldname'][:63]
            calias = f.get('calias', cfieldname.capitalize())[:50]
            cfieldtype = f.get('cfieldtype', 'C')
            nlength = f.get('nlength', 255)
            ndecimals = f.get('ndecimals', 0)
            lisindexed = f.get('lisindexed', True)
            ref_entitytypeid = f.get('ref_entitytypeid', None)

            res = self.db.execute_query(
                """INSERT INTO meta.fields
                   (entitytypeid, cfieldname, cfieldtype, calias,
                    nlength, ndecimals, lisindexed, ref_entitytypeid, status_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                   RETURNING id""",
                (entity_id, cfieldname, cfieldtype, calias,
                 nlength, ndecimals, lisindexed, ref_entitytypeid)
            )
            if res:
                field_id = res[0][0]
                self.db.execute_procedure("meta.p_field_sync", (field_id,))
                created_ids.append(field_id)
            else:
                raise Exception(f"Failed to create field {cfieldname}")
        return created_ids