# mozart_import/designer/designer_main.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import (QTreeWidgetItem, QPushButton, QMessageBox, QDialog, from PySide6.QtGui import QAction                              QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,                              QTableWidget, QTableWidgetItem, QHeaderView, QMenu,                              QTabWidget, QProgressDialog, QHBoxLayout,                              QLabel, QCheckBox, QSpinBox, QFrame)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from ..core.models import (SourceTable, SourceField, FieldType, ImportProfile,
                           SourceType, MappingProposal, MatchedEntity, MatchedField)
from ..utils.field_creator import FieldCreator
from ..core.import_engine import ImportEngine
from ..core.profile_manager import ProfileManager
from .designer_mass_field_dialog import MassFieldDialog


class ImportDesigner(QMainWindow):
    def __init__(self, db, connector, parent=None):
        super().__init__(parent)
        self.db = db
        self.connector = connector
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('import_designer_title'))
        self.resize(1200, 800)
        self.editing_profile_id = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        self.splitter = QSplitter(Qt.Horizontal)
        top_layout.addWidget(self.splitter)

        left_tabs = QTabWidget()
        self.source_tree = QTreeWidget()
        self.source_tree.setHeaderLabels([self.translator.tr('source_tables'), self.translator.tr('rows')])
        self.source_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.source_tree.customContextMenuRequested.connect(self.source_context_menu)
        left_tabs.addTab(self.source_tree, self.translator.tr('source_tables'))

        self.source_links_table = QTableWidget(0, 4)
        self.source_links_table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_table'),
            self.translator.tr('target_field')
        ])
        self.source_links_table.horizontalHeader().setStretchLastSection(True)
        left_tabs.addTab(self.source_links_table, self.translator.tr('source_links'))
        self.splitter.addWidget(left_tabs)

        self.mozart_tree = QTreeWidget()
        self.mozart_tree.setHeaderLabels([self.translator.tr('mozart_entities'), ""])
        self.mozart_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mozart_tree.customContextMenuRequested.connect(self.mozart_context_menu)
        self.splitter.addWidget(self.mozart_tree)

        main_layout.addWidget(top_widget, 2)

        splitter_handle = QFrame()
        splitter_handle.setFrameShape(QFrame.HLine)
        splitter_handle.setFrameShadow(QFrame.Sunken)
        splitter_handle.setCursor(Qt.SizeVerCursor)
        splitter_handle.mousePressEvent = self.start_splitter_drag
        splitter_handle.mouseMoveEvent = self.drag_splitter
        splitter_handle.mouseReleaseEvent = self.stop_splitter_drag
        main_layout.addWidget(splitter_handle)
        self.splitter_handle = splitter_handle
        self.dragging = False
        self.drag_start_y = 0
        self.start_height = 0

        self.links_table = QTableWidget(0, 6)
        self.links_table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_entity'),
            self.translator.tr('target_field'),
            self.translator.tr('type'),
            ''
        ])
        self.links_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.links_table, 1)

        btn_layout = QHBoxLayout()
        self.btn_add_link = QPushButton(self.translator.tr('add_import_link'))
        self.btn_add_link.clicked.connect(self.add_import_link)
        self.btn_save = QPushButton(self.translator.tr('save_profile'))
        self.btn_save.clicked.connect(self.save_profile)
        self.btn_import = QPushButton(self.translator.tr('start_import'))
        self.btn_import.clicked.connect(self.perform_import)
        self.btn_create_entity = QPushButton(self.translator.tr('create_entity'))
        self.btn_create_entity.clicked.connect(self.create_entity)
        btn_layout.addWidget(self.btn_create_entity)
        btn_layout.addWidget(self.btn_add_link)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_import)
        main_layout.addLayout(btn_layout)

        self.source_tables = []
        self.mozart_entities = []
        self.source_fk_links = []
        self.import_links = []

        self.load_source()
        self.load_mozart()
        self.retranslate_ui()
        self.links_table.setMinimumHeight(150)
        self.links_table.setMaximumHeight(400)

    def set_profile_for_edit(self, profile):
        self.editing_profile_id = profile.id
        self.restore_profile(profile)

    def restore_profile(self, profile):
        self.source_tables = []
        self.import_links = []
        self.source_fk_links = []
        self.source_tree.clear()
        self.source_links_table.setRowCount(0)
        self.links_table.setRowCount(0)

        self.load_source()
        self.source_fk_links = profile.source_fk_links
        self.update_source_links_table()

        self.import_links = []
        for link in profile.import_links:
            target_entity_id = None
            for ent in self.mozart_entities:
                if ent['id'] == link['target_entity_id']:
                    target_entity_id = ent['id']
                    break
            if not target_entity_id:
                continue
            for mapping in link['mappings']:
                self.import_links.append({
                    'source_table': link['source_table'],
                    'source_field': mapping['source_field'],
                    'target_entity_id': target_entity_id,
                    'target_field': mapping['target_field'],
                    'type': 'sourceid' if mapping.get('is_source_id') else 'import'
                })
        self.update_import_links_table()
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('profile_loaded'))

    def start_splitter_drag(self, event):
        self.dragging = True
        self.drag_start_y = event.globalY()
        self.start_height = self.links_table.height()
        self.setCursor(Qt.SizeVerCursor)

    def drag_splitter(self, event):
        if self.dragging:
            delta = event.globalY() - self.drag_start_y
            new_height = self.start_height - delta
            new_height = max(100, min(600, new_height))
            self.links_table.setMinimumHeight(new_height)
            self.links_table.setMaximumHeight(new_height)

    def stop_splitter_drag(self, event):
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.tr('import_designer_title'))
        self.source_tree.setHeaderLabels([self.translator.tr('source_tables'), self.translator.tr('rows')])
        self.mozart_tree.setHeaderLabels([self.translator.tr('mozart_entities'), ""])
        self.source_links_table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_table'),
            self.translator.tr('target_field')
        ])
        self.links_table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_entity'),
            self.translator.tr('target_field'),
            self.translator.tr('type'),
            ''
        ])
        self.btn_create_entity.setText(self.translator.tr('create_entity'))
        self.btn_add_link.setText(self.translator.tr('add_import_link'))
        self.btn_save.setText(self.translator.tr('save_profile'))
        self.btn_import.setText(self.translator.tr('start_import'))

    def load_source(self):
        self.source_tree.clear()
        schema = self.connector.get_schema()
        self.source_tables = schema.tables
        for table in self.source_tables:
            row_count = self.connector.get_row_count(table.name)
            count_str = str(row_count) if row_count is not None else '?'
            item = QTreeWidgetItem([table.name, count_str])
            item.setData(0, Qt.UserRole, table.name)
            for field in table.fields:
                field_item = QTreeWidgetItem([f"  {field.name} ({field.field_type.name})", ""])
                field_item.setData(0, Qt.UserRole, field.name)
                field_item.setFlags(field_item.flags() | Qt.ItemIsUserCheckable)
                field_item.setCheckState(0, Qt.Unchecked)
                item.addChild(field_item)
            self.source_tree.addTopLevelItem(item)
        self.detect_source_fk_links()
        self.update_source_links_table()

    def detect_source_fk_links(self):
        self.source_fk_links = []
        for table in self.source_tables:
            for field in table.fields:
                if field.is_foreign_key and field.refers_to:
                    self.source_fk_links.append({
                        'source_table': table.name,
                        'source_field': field.name,
                        'target_table': field.refers_to,
                        'target_field': 'id'
                    })

    def update_source_links_table(self):
        self.source_links_table.setRowCount(len(self.source_fk_links))
        for row, link in enumerate(self.source_fk_links):
            self.source_links_table.setItem(row, 0, QTableWidgetItem(link['source_table']))
            self.source_links_table.setItem(row, 1, QTableWidgetItem(link['source_field']))
            self.source_links_table.setItem(row, 2, QTableWidgetItem(link['target_table']))
            self.source_links_table.setItem(row, 3, QTableWidgetItem(link['target_field']))

    def load_mozart(self):
        self.mozart_tree.clear()
        rows = self.db.execute_query("SELECT id, cname, calias, class_id FROM meta.entitytypes ORDER BY cname")
        self.mozart_entities = []
        for eid, cname, calias, class_id in rows:
            class_res = self.db.execute_query("SELECT calias FROM meta.entity_classes WHERE id=%s", (class_id,))
            class_alias = class_res[0][0] if class_res else "DICT"
            fields = self.db.execute_query("SELECT cfieldname, cfieldtype FROM meta.fields WHERE entitytypeid=%s", (eid,))
            item = QTreeWidgetItem([f"{cname} ({calias} - {class_alias})", ""])
            item.setData(0, Qt.UserRole, eid)
            for fname, ftype in fields:
                fitem = QTreeWidgetItem([f"  {fname} ({ftype})", ""])
                fitem.setData(0, Qt.UserRole, fname)
                item.addChild(fitem)
            self.mozart_tree.addTopLevelItem(item)
            self.mozart_entities.append({
                'id': eid, 'cname': cname, 'calias': calias, 'class_alias': class_alias, 'fields': [f[0] for f in fields]
            })

    def source_context_menu(self, pos):
        item = self.source_tree.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        if item.parent() is None:
            preview_action = QAction(self.translator.tr('preview_table'), None)
            preview_action.triggered.connect(lambda: self.preview_table(item))
            menu.addAction(preview_action)
            add_link_action = QAction(self.translator.tr('add_source_link'), None)
            add_link_action.triggered.connect(lambda: self.add_source_link(item))
            menu.addAction(add_link_action)
            select_all_action = QAction(self.translator.tr('select_all_fields'), None)
            select_all_action.triggered.connect(lambda: self.set_checks_for_table(item, Qt.Checked))
            menu.addAction(select_all_action)
            deselect_all_action = QAction(self.translator.tr('deselect_all_fields'), None)
            deselect_all_action.triggered.connect(lambda: self.set_checks_for_table(item, Qt.Unchecked))
            menu.addAction(deselect_all_action)
        menu.exec_(self.source_tree.mapToGlobal(pos))

    def set_checks_for_table(self, table_item, state):
        for i in range(table_item.childCount()):
            field_item = table_item.child(i)
            field_item.setCheckState(0, state)

    def add_source_link(self, table_item):
        table_name = table_item.data(0, Qt.UserRole)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('add_source_link_title'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        source_field_combo = QComboBox()
        for t in self.source_tables:
            if t.name == table_name:
                for f in t.fields:
                    source_field_combo.addItem(f.name, f.name)
                break
        form.addRow(self.translator.tr('source_field'), source_field_combo)
        target_table_combo = QComboBox()
        for t in self.source_tables:
            if t.name != table_name:
                target_table_combo.addItem(t.name, t.name)
        form.addRow(self.translator.tr('target_table'), target_table_combo)
        target_field_combo = QComboBox()
        target_table_combo.currentIndexChanged.connect(lambda: self.update_target_fields(target_table_combo, target_field_combo))
        self.update_target_fields(target_table_combo, target_field_combo)
        form.addRow(self.translator.tr('target_field'), target_field_combo)
        layout.addLayout(form)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_():
            self.source_fk_links.append({
                'source_table': table_name,
                'source_field': source_field_combo.currentData(),
                'target_table': target_table_combo.currentData(),
                'target_field': target_field_combo.currentData()
            })
            self.update_source_links_table()

    def update_target_fields(self, target_table_combo, target_field_combo):
        target_table = target_table_combo.currentData()
        target_field_combo.clear()
        for t in self.source_tables:
            if t.name == target_table:
                for f in t.fields:
                    target_field_combo.addItem(f.name, f.name)
                break

    def mozart_context_menu(self, pos):
        item = self.mozart_tree.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        if item.parent() is None:
            create_action = QAction(self.translator.tr('create_fields_from_checked'), None)
            create_action.triggered.connect(lambda: self.create_fields_from_checked(item))
            menu.addAction(create_action)
        menu.exec_(self.mozart_tree.mapToGlobal(pos))

    def create_fields_from_checked(self, target_entity_item):
        entity_id = target_entity_item.data(0, Qt.UserRole)
        checked_fields = []
        root = self.source_tree.invisibleRootItem()
        for i in range(root.childCount()):
            table_item = root.child(i)
            for j in range(table_item.childCount()):
                field_item = table_item.child(j)
                if field_item.checkState(0) == Qt.Checked:
                    checked_fields.append({
                        'source_field_name': field_item.data(0, Qt.UserRole),
                        'source_table': table_item.data(0, Qt.UserRole)
                    })
        if not checked_fields:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('no_fields_selected'))
            return
        dlg = MassFieldDialog(self, checked_fields, self.translator)
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
            self.load_mozart()
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('fields_created'))

    def preview_table(self, table_item):
        table_name = table_item.data(0, Qt.UserRole)
        sample = self.connector.get_table_sample(table_name, limit=20)
        if not sample:
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('no_data'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('preview_table_title').format(table_name))
        layout = QVBoxLayout(dlg)
        table = QTableWidget()
        headers = list(sample[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(sample))
        for i, row in enumerate(sample):
            for j, col in enumerate(headers):
                table.setItem(i, j, QTableWidgetItem(str(row.get(col, ''))))
        layout.addWidget(table)
        dlg.exec_()

    def create_entity(self):
        from ..wizards.wizard_dialogs import NewEntityDialog
        dlg = NewEntityDialog(self, self.db)
        if dlg.exec_():
            data = dlg.get_data()
            res = self.db.execute_query(
                """INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisversioned, isecuritystrategy, status_id)
                   VALUES (%s, %s, %s, '', true, 1, 1) RETURNING id""",
                (data['cname'], data['calias'], data['class_id'])
            )
            if res:
                entity_id = res[0][0]
                self.load_mozart()
                QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('entity_created'))

    def add_import_link(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('add_import_link_title'))
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        src_table_combo = QComboBox()
        for t in self.source_tables:
            src_table_combo.addItem(t.name, t.name)
        form.addRow(self.translator.tr('source_table'), src_table_combo)
        src_field_combo = QComboBox()
        src_table_combo.currentIndexChanged.connect(lambda: self.update_src_fields(src_table_combo, src_field_combo))
        self.update_src_fields(src_table_combo, src_field_combo)
        form.addRow(self.translator.tr('source_field'), src_field_combo)
        target_entity_combo = QComboBox()
        for ent in self.mozart_entities:
            target_entity_combo.addItem(f"{ent['cname']} ({ent['calias']})", ent['id'])
        form.addRow(self.translator.tr('target_entity'), target_entity_combo)
        target_field_combo = QComboBox()
        target_entity_combo.currentIndexChanged.connect(lambda: self.update_target_fields_entity(target_entity_combo, target_field_combo))
        self.update_target_fields_entity(target_entity_combo, target_field_combo)
        form.addRow(self.translator.tr('target_field'), target_field_combo)
        type_combo = QComboBox()
        type_combo.addItem(self.translator.tr('import_type'), 'import')
        type_combo.addItem(self.translator.tr('sourceid_type'), 'sourceid')
        form.addRow(self.translator.tr('type'), type_combo)
        layout.addLayout(form)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_():
            target_field = target_field_combo.currentData()
            self.import_links.append({
                'source_table': src_table_combo.currentData(),
                'source_field': src_field_combo.currentData(),
                'target_entity_id': target_entity_combo.currentData(),
                'target_field': target_field,
                'type': type_combo.currentData()
            })
            self.update_import_links_table()

    def update_src_fields(self, src_table_combo, src_field_combo):
        table_name = src_table_combo.currentData()
        src_field_combo.clear()
        for t in self.source_tables:
            if t.name == table_name:
                for f in t.fields:
                    src_field_combo.addItem(f.name, f.name)
                break

    def update_target_fields_entity(self, target_entity_combo, target_field_combo):
        entity_id = target_entity_combo.currentData()
        target_field_combo.clear()
        for ent in self.mozart_entities:
            if ent['id'] == entity_id:
                for fname in ent['fields']:
                    target_field_combo.addItem(fname, fname)
                break

    def update_import_links_table(self):
        self.links_table.setRowCount(len(self.import_links))
        for row, link in enumerate(self.import_links):
            self.links_table.setItem(row, 0, QTableWidgetItem(link['source_table']))
            self.links_table.setItem(row, 1, QTableWidgetItem(link['source_field']))
            entity_name = ''
            for ent in self.mozart_entities:
                if ent['id'] == link['target_entity_id']:
                    entity_name = ent['cname']
                    break
            self.links_table.setItem(row, 2, QTableWidgetItem(entity_name))
            self.links_table.setItem(row, 3, QTableWidgetItem(link['target_field'] or ''))
            self.links_table.setItem(row, 4, QTableWidgetItem(link['type']))
            btn = QPushButton(self.translator.tr('delete'))
            btn.clicked.connect(lambda checked, r=row: self.remove_import_link(r))
            self.links_table.setCellWidget(row, 5, btn)

    def remove_import_link(self, row):
        self.import_links.pop(row)
        self.update_import_links_table()

    def save_profile(self):
        source_tables = []
        for table in self.source_tables:
            sample_rows = []
            if hasattr(table, 'sample_rows') and table.sample_rows:
                sample_rows = table.sample_rows[:5]
            source_tables.append({
                'name': table.name,
                'row_count': self.connector.get_row_count(table.name),
                'sample_rows': sample_rows
            })
        target_entities = []
        seen = set()
        for link in self.import_links:
            eid = link['target_entity_id']
            if eid not in seen:
                for ent in self.mozart_entities:
                    if ent['id'] == eid:
                        target_entities.append({'id': eid, 'name': ent['cname']})
                        seen.add(eid)
                        break
        import_links = []
        for link in self.import_links:
            mappings = [{
                'source_field': link['source_field'],
                'target_field': link['target_field'],
                'field_type': 'C',
                'field_length': 255,
                'is_source_id': (link['type'] == 'sourceid')
            }]
            import_links.append({
                'source_table': link['source_table'],
                'target_entity_id': link['target_entity_id'],
                'mappings': mappings
            })
        profile = ImportProfile(
            name=self.connector.source_path,
            source_type=SourceType.FILE,
            source_path=self.connector.source_path,
            source_tables=source_tables,
            target_entities=target_entities,
            import_links=import_links,
            source_fk_links=self.source_fk_links
        )
        if self.editing_profile_id:
            profile.id = self.editing_profile_id
        prof_mgr = ProfileManager(self.db)
        prof_mgr.save_profile(profile)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('profile_saved'))

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
        progress = QProgressDialog(self.translator.tr('import_progress'), self.translator.tr('cancel'), 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        try:
            engine = ImportEngine(self.db, self.connector, profile)
            stats = engine.run()
            progress.close()
            QMessageBox.information(self, self.translator.tr('import_finished_title'),
                                    self.translator.tr('import_finished_stats').format(stats['inserted'], stats['updated'], stats['errors']))
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, self.translator.tr('error'), str(e))