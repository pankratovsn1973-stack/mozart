# mozart_import/wizards/execute_page.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWizardPage, QVBoxLayout, QProgressBar, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal
from lang.local_translator import LocalTranslator
from ..core.models import ImportProfile, SourceType, MappingProposal, MatchedEntity, MatchedField
from ..core.profile_manager import ProfileManager
from ..core.import_engine import ImportEngine
from ..utils.field_creator import FieldCreator


class ImportThread(QThread):
    progress = Signal(int, int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, db, connector, profile):
        super().__init__()
        self.db = db
        self.connector = connector
        self.profile = profile

    def run(self):
        try:
            engine = ImportEngine(self.db, self.connector, self.profile)
            stats = engine.run(progress_callback=self.progress.emit)
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class ExecutePage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = LocalTranslator()
        self.setTitle(self.translator.tr('execute_page_title'))
        self.setSubTitle(self.translator.tr('execute_page_subtitle'))

        layout = QVBoxLayout(self)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton(self.translator.tr('start_import_btn'))
        self.btn_start.clicked.connect(self.start_import)
        self.btn_start.setEnabled(False)
        btn_layout.addWidget(self.btn_start)
        layout.addLayout(btn_layout)

        self.import_thread = None

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('execute_page_title'))
        self.setSubTitle(self.translator.tr('execute_page_subtitle'))
        self.btn_start.setText(self.translator.tr('start_import_btn'))

    def initializePage(self):
        self.prepare_profile()
        self.btn_start.setEnabled(True)

    def prepare_profile(self):
        # Создаём недостающие сущности и поля
        creator = FieldCreator(self.wizard.db)
        if hasattr(self.wizard, 'pending_entities') and self.wizard.pending_entities:
            for node_item, entity_data in self.wizard.pending_entities:
                res = self.wizard.db.execute_query(
                    """INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisversioned, isecuritystrategy, status_id)
                       VALUES (%s, %s, %s, '', true, 1, 1) RETURNING id""",
                    (entity_data['cname'], entity_data['calias'], entity_data['class_id'])
                )
                if res:
                    entity_id = res[0][0]
                    node_item.node.entity_id = entity_id

        # Строим MappingProposal
        source_nodes = {n.id: n for n in getattr(self.wizard, 'source_nodes', [])}
        target_nodes = {}
        if hasattr(self.wizard, 'mozart_nodes'):
            for n in self.wizard.mozart_nodes:
                target_nodes[n.id] = n
        if hasattr(self.wizard, 'pending_entities'):
            for node_item, _ in self.wizard.pending_entities:
                target_nodes[node_item.node.id] = node_item.node

        links = getattr(self.wizard, 'links', [])
        target_groups = {}
        for link in links:
            target_id = link['target_node_id']
            if target_id not in target_groups:
                target_groups[target_id] = []
            target_groups[target_id].append(link)

        entities = []
        for target_id, link_list in target_groups.items():
            target_node = target_nodes.get(target_id)
            if not target_node:
                continue
            source_table_name = link_list[0]['source_node_id'].replace('src_', '')
            matched_fields = []
            for link in link_list:
                if link.get('target_field'):
                    is_ref = False
                    ref_entity_id = None
                    matched_fields.append(MatchedField(
                        source_field=link['source_field'],
                        target_field=link['target_field'],
                        confidence=1.0,
                        is_reference=is_ref,
                        ref_entitytype_id=ref_entity_id
                    ))
            entities.append(MatchedEntity(
                source_table=source_table_name,
                target_entity_id=target_node.entity_id,
                target_entity_name=target_node.name,
                confidence=1.0,
                fields=matched_fields,
                is_new=(target_node.entity_id is None)
            ))

        self.wizard.mapping_proposal = MappingProposal(
            source_schema=self.wizard.schema,
            entities=entities,
            unresolved_tables=[],
            suggestions_for_new_entities=[]
        )

        profile = ImportProfile(
            name=f"Import from {self.wizard.connector.source_path}",
            source_type=self.wizard.connector.source_type,
            source_path=self.wizard.connector.source_path,
            mapping_proposal=self.wizard.mapping_proposal,
            scene_json=getattr(self.wizard, 'import_scene_json', None)
        )
        self.wizard.profile = profile
        prof_mgr = ProfileManager(self.wizard.db)
        prof_mgr.save_profile(profile)

    def start_import(self):
        if not self.wizard.profile:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('profile_not_ready'))
            return
        self.btn_start.setEnabled(False)
        self.import_thread = ImportThread(self.wizard.db, self.wizard.connector, self.wizard.profile)
        self.import_thread.progress.connect(self.update_progress)
        self.import_thread.finished.connect(self.on_finished)
        self.import_thread.error.connect(self.on_error)
        self.import_thread.start()

    def update_progress(self, current, total):
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        self.log.append(f"{self.translator.tr('processed_records')}: {current} / {total}")

    def on_finished(self, stats):
        self.log.append(f"{self.translator.tr('import_finished')}. {self.translator.tr('inserted')}: {stats['inserted']}, {self.translator.tr('updated')}: {stats['updated']}, {self.translator.tr('errors')}: {stats['errors']}")
        QMessageBox.information(self, self.translator.tr('import_finished_title'), self.translator.tr('import_finished'))
        self.btn_start.setEnabled(False)

    def on_error(self, msg):
        self.log.append(f"{self.translator.tr('error')}: {msg}")
        QMessageBox.critical(self, self.translator.tr('error'), msg)
        self.btn_start.setEnabled(True)