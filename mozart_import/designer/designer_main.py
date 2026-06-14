# mozart_import/designer/designer_main.py
# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import (QTreeWidgetItem, QPushButton, QMessageBox, QDialog, from PySide6.QtGui import QAction                              QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,                              QTableWidget, QTableWidgetItem, QHeaderView, QMenu,                              QTabWidget, QProgressDialog, QHBoxLayout,                              QLabel, QCheckBox, QSpinBox, QFrame)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from ..core.models import ImportProfile, SourceType, FileFormat
from ..core.profile_manager import ProfileManager
from .designer_trees import SourceTreeManager, MozartTreeManager
from .designer_links import ImportLinksManager
from .designer_import import ImportOperations


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
        self.source_links_table = QTableWidget(0, 4)
        self.source_links_table.setHorizontalHeaderLabels([
            self.translator.tr('source_table'),
            self.translator.tr('source_field'),
            self.translator.tr('target_table'),
            self.translator.tr('target_field')
        ])
        self.source_links_table.horizontalHeader().setStretchLastSection(True)
        left_tabs.addTab(self.source_tree, self.translator.tr('source_tables'))
        left_tabs.addTab(self.source_links_table, self.translator.tr('source_links'))
        self.splitter.addWidget(left_tabs)

        self.mozart_tree = QTreeWidget()
        self.mozart_tree.setHeaderLabels([self.translator.tr('mozart_entities'), ""])
        self.mozart_tree.setContextMenuPolicy(Qt.CustomContextMenu)
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

        # Инициализация менеджеров
        self.source_manager = SourceTreeManager(self, self.source_tree, self.source_links_table,
                                                self.translator, self.connector)
        self.mozart_manager = MozartTreeManager(self, self.mozart_tree, self.translator, self.db)
        self.links_manager = None
        self.import_ops = None

        self.load_initial_data()
        self.setup_context_menus()
        self.links_table.setMinimumHeight(150)
        self.links_table.setMaximumHeight(400)

    def load_initial_data(self):
        self.source_manager.load_source()
        self.mozart_manager.load_mozart()
        self.links_manager = ImportLinksManager(self, self.links_table, self.translator,
                                                self.source_manager.source_tables,
                                                self.mozart_manager.mozart_entities)
        self.import_ops = ImportOperations(self, self.db, self.connector, self.translator,
                                           self.source_manager.source_tables,
                                           self.mozart_manager.mozart_entities,
                                           self.links_manager.import_links)

    def setup_context_menus(self):
        self.source_tree.customContextMenuRequested.connect(self.source_context_menu)
        self.mozart_tree.customContextMenuRequested.connect(self.mozart_context_menu)

    def source_context_menu(self, pos):
        item = self.source_tree.itemAt(pos)
        if not item or item.parent() is not None:
            return
        menu = QMenu()
        preview_action = QAction(self.translator.tr('preview_table'), None)
        preview_action.triggered.connect(lambda: self.source_manager.preview_table(item))
        menu.addAction(preview_action)
        add_link_action = QAction(self.translator.tr('add_source_link'), None)
        add_link_action.triggered.connect(lambda: self.source_manager.add_source_link(item))
        menu.addAction(add_link_action)
        select_all_action = QAction(self.translator.tr('select_all_fields'), None)
        select_all_action.triggered.connect(lambda: self.source_manager.set_checks_for_table(item, Qt.Checked))
        menu.addAction(select_all_action)
        deselect_all_action = QAction(self.translator.tr('deselect_all_fields'), None)
        deselect_all_action.triggered.connect(lambda: self.source_manager.set_checks_for_table(item, Qt.Unchecked))
        menu.addAction(deselect_all_action)
        menu.exec_(self.source_tree.mapToGlobal(pos))

    def mozart_context_menu(self, pos):
        item = self.mozart_tree.itemAt(pos)
        if not item or item.parent() is not None:
            return
        menu = QMenu()
        create_action = QAction(self.translator.tr('create_fields_from_checked'), None)
        create_action.triggered.connect(lambda: self.import_ops.create_fields_from_checked(item, self.source_manager))
        menu.addAction(create_action)
        menu.exec_(self.mozart_tree.mapToGlobal(pos))

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

    def add_import_link(self):
        self.links_manager.add_import_link()
        self.import_ops.set_import_links(self.links_manager.import_links)

    def save_profile(self):
        # 1. Сбор данных о таблицах источника
        source_tables = []
        for table in self.source_manager.source_tables:
            sample_rows = table.sample_rows[:5] if table.sample_rows else []
            source_tables.append({
                'name': table.name,
                'row_count': self.connector.get_row_count(table.name),
                'sample_rows': sample_rows
            })

        # 2. Сбор целевых сущностей
        target_entities = []
        seen = set()
        for link in self.links_manager.import_links:
            eid = link['target_entity_id']
            if eid not in seen:
                for ent in self.mozart_manager.mozart_entities:
                    if ent['id'] == eid:
                        target_entities.append({'id': eid, 'name': ent['cname']})
                        seen.add(eid)
                        break

        # 3. Собираем связи импорта
        import_links = []
        for link in self.links_manager.import_links:
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

        # 4. Сбор параметров подключения
        file_format = None
        db_type = None
        db_host = None
        db_port = None
        db_name = None
        db_user = None
        db_pass = None

        if hasattr(self.connector, 'file_format'):
            # FileConnector
            file_format = self.connector.file_format.value if isinstance(self.connector.file_format, FileFormat) else str(self.connector.file_format)
        elif hasattr(self.connector, 'db_type'):
            # DBConnector
            db_type = self.connector.db_type
            db_host = self.connector.host
            db_port = self.connector.port
            db_name = self.connector.database
            db_user = self.connector.user
            db_pass = self.connector.password
        # URLConnector не имеет дополнительных полей, кроме source_path

        # Определяем тип источника
        if hasattr(self.connector, 'file_format'):
            source_type = SourceType.FILE
        elif hasattr(self.connector, 'db_type'):
            source_type = SourceType.DATABASE
        else:
            source_type = SourceType.URL

        profile = ImportProfile(
            name=self.connector.source_path,
            source_type=source_type,
            source_path=self.connector.source_path,
            source_tables=source_tables,
            target_entities=target_entities,
            import_links=import_links,
            source_fk_links=self.source_manager.source_fk_links,
            file_format=file_format,
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_pass=db_pass
        )
        if self.editing_profile_id:
            profile.id = self.editing_profile_id

        prof_mgr = ProfileManager(self.db)
        prof_mgr.save_profile(profile)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('profile_saved'))

    def perform_import(self):
        self.import_ops.set_import_links(self.links_manager.import_links)
        self.import_ops.perform_import()

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
                self.mozart_manager.load_mozart()
                self.links_manager.set_mozart_entities(self.mozart_manager.mozart_entities)
                self.import_ops.set_mozart_entities(self.mozart_manager.mozart_entities)
                QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('entity_created'))

    def set_profile_for_edit(self, profile):
        self.editing_profile_id = profile.id
        self.restore_profile(profile)

    def restore_profile(self, profile):
        self.source_manager.source_tables = []
        self.source_manager.source_fk_links = profile.source_fk_links
        self.source_manager.update_source_links_table()
        self.links_manager.import_links = []
        for link in profile.import_links:
            for mapping in link['mappings']:
                self.links_manager.import_links.append({
                    'source_table': link['source_table'],
                    'source_field': mapping['source_field'],
                    'target_entity_id': link['target_entity_id'],
                    'target_field': mapping['target_field'],
                    'type': 'sourceid' if mapping.get('is_source_id') else 'import'
                })
        self.links_manager.update_import_links_table()
        self.import_ops.set_import_links(self.links_manager.import_links)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('profile_loaded'))