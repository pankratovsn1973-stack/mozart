# mozart_import/designer/designer_import.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QProgressDialog, QMessageBox
from PySide6.QtCore import Qt
from ..core.models import ImportProfile, SourceType, MappingProposal, MatchedEntity, MatchedField
from ..utils.field_creator import FieldCreator
from ..core.import_engine import ImportEngine
from .designer_mass_field_dialog import MassFieldDialog


class ImportOperations:
    """Методы импорта и создания полей."""
    def __init__(self, parent, db, connector, translator, source_tables, mozart_entities, import_links):
        self.parent = parent
        self.db = db
        self.connector = connector
        self.translator = translator
        self.source_tables = source_tables
        self.mozart_entities = mozart_entities
        self.import_links = import_links

    def set_source_tables(self, tables):
        self.source_tables = tables

    def set_mozart_entities(self, entities):
        self.mozart_entities = entities

    def set_import_links(self, links):
        self.import_links = links

    def create_fields_from_checked(self, target_entity_item, source_tree_manager):
        entity_id = target_entity_item.data(0, Qt.UserRole)
        checked_fields = source_tree_manager.get_checked_fields()
        if not checked_fields:
            QMessageBox.warning(self.parent, self.translator.tr('warning'), self.translator.tr('no_fields_selected'))
            return
        dlg = MassFieldDialog(self.parent, checked_fields, self.translator)
        if dlg.exec_():
            fields_to_create = dlg.get_fields()
            if not fields_to_create:
                return
            creator = FieldCreator(self.db)
            for f in fields_to_create:
                creator.create_fields(entity_id, [{
                    'cfieldname': f['cfieldname'][:63],
                    'cfieldtype': f['cfieldtype'],
                    'calias': f['calias'][:50],
                    'nlength': f['nlength']
                }])

    def perform_import(self):
        creator = FieldCreator(self.db)
        for link in self.import_links:
            if link['type'] == 'import' and link['target_field']:
                check = self.db.execute_query(
                    "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s",
                    (link['target_entity_id'], link['target_field'])
                )
                if not check:
                    creator.create_fields(link['target_entity_id'], [{
                        'cfieldname': link['target_field'][:63],
                        'cfieldtype': 'C',
                        'calias': link['target_field'].capitalize()[:50],
                        'nlength': 255
                    }])
            elif link['type'] == 'sourceid':
                check = self.db.execute_query(
                    "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname='sourceid'",
                    (link['target_entity_id'],)
                )
                if not check:
                    creator.create_fields(link['target_entity_id'], [{
                        'cfieldname': 'sourceid',
                        'cfieldtype': 'C',
                        'calias': 'Source ID',
                        'nlength': 100
                    }])

        # Группировка связей по целевой сущности
        groups = {}
        for link in self.import_links:
            eid = link['target_entity_id']
            if eid not in groups:
                groups[eid] = []
            groups[eid].append(link)

        entities = []
        for eid, links in groups.items():
            target_entity = None
            for ent in self.mozart_entities:
                if ent['id'] == eid:
                    target_entity = ent
                    break
            if not target_entity:
                continue
            source_table_name = links[0]['source_table']
            matched_fields = []
            for link in links:
                if link['type'] == 'import' and link['target_field']:
                    matched_fields.append(MatchedField(
                        source_field=link['source_field'],
                        target_field=link['target_field']
                    ))
            entities.append(MatchedEntity(
                source_table=source_table_name,
                target_entity_id=eid,
                target_entity_name=target_entity['cname'],
                confidence=1.0,
                fields=matched_fields,
                is_new=False
            ))

        mapping_proposal = MappingProposal(
            source_schema=self.connector.get_schema(),
            entities=entities,
            unresolved_tables=[],
            suggestions_for_new_entities=[]
        )
        profile = ImportProfile(
            name=self.connector.source_path,
            source_type=SourceType.FILE,
            source_path=self.connector.source_path,
            mapping_proposal=mapping_proposal
        )
        progress = QProgressDialog(self.translator.tr('import_progress'), self.translator.tr('cancel'), 0, 0, self.parent)
        progress.setWindowModality(Qt.WindowModal)
        try:
            engine = ImportEngine(self.db, self.connector, profile)
            stats = engine.run()
            progress.close()
            QMessageBox.information(self.parent, self.translator.tr('import_finished_title'),
                                    self.translator.tr('import_finished_stats').format(stats['inserted'], stats['updated'], stats['errors']))
        except Exception as e:
            progress.close()
            QMessageBox.critical(self.parent, self.translator.tr('error'), str(e))