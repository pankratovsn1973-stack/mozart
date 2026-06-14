# mozart_import/designer/designer_v2.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton,                              QHBoxLayout, QMessageBox, QDialog, QTableWidget,                              QTableWidgetItem, QLabel, QComboBox, QApplication)
from PySide6.QtCore import Qt
from database import DatabaseService
from lang.local_translator import LocalTranslator
from ..graph.graphics_view import GraphicsView
from ..graph.relation_scene import RelationScene
from ..graph.graphics_items import SOURCE_ID_FIELD
from ..core.models import (Node, NodeType, Field, DataType, LinkType,
                           ImportProfile, SourceType)
from ..core.profile_manager import ProfileManager
from ..core.import_orchestrator import ImportOrchestrator
from ..utils.field_creator import FieldCreator
from ..utils.ext_helper import ExtHelper
from .entity_creator import EntityCreator
from .link_edit_dialog import LinkEditDialog
from .source_ref_dialog import SourceRefDialog
from .scene_profile_adapter import SceneProfileAdapter
from ..gui.progress_dialog import ImportProgressDialog


class ImportDesignerV2(QMainWindow):
    """Визуальный конструктор импорта."""

    def __init__(self, db: DatabaseService, connector, parent=None):
        super().__init__(parent)
        self.db = db
        self.connector = connector
        self.translator = LocalTranslator()
        self.editing_profile_id = None
        self.field_creator = FieldCreator(self.db)
        self.ext_helper = ExtHelper(self.db)
        self.entity_creator = EntityCreator(self.db)

        self.setWindowTitle(self.translator.tr('import_designer_title'))
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Сцена
        self.scene = RelationScene(self)
        self.scene.on_preview_table = self.preview_table
        self.scene.on_create_entity = self.create_entity_from_source
        self.scene.on_create_fields_from_source = self.create_fields_for_mozart
        self.scene.on_edit_link = self.edit_link_between
        self.scene.on_set_source_refs = self.edit_source_refs

        self.view = GraphicsView(self.scene)
        main_layout.addWidget(self.view, 1)

        # Панель управления
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton(self.translator.tr('save_profile'))
        self.btn_save.clicked.connect(self.save_profile)
        self.btn_import = QPushButton(self.translator.tr('start_import'))
        self.btn_import.clicked.connect(self.perform_import)

        # Комбобокс выбора режима импорта (локализованный)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.translator.tr('import_mode_append'), "append")
        self.mode_combo.addItem(self.translator.tr('import_mode_full_update'), "full_update")
        btn_layout.addWidget(QLabel(self.translator.tr('import_mode_label')))
        btn_layout.addWidget(self.mode_combo)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_import)
        main_layout.addLayout(btn_layout)

        self.load_source_tables()
        self.load_mozart_entities()

    # -----------------------------------------------------------------
    # Загрузка таблиц источника
    # -----------------------------------------------------------------
    def load_source_tables(self):
        schema = self.connector.get_schema()
        divider = self.scene.divider_x
        x, y = 30, 30
        for table in schema.tables:
            fields = []
            for f in table.fields:
                dt = DataType.STRING
                if f.field_type.name == 'INTEGER':
                    dt = DataType.INTEGER
                elif f.field_type.name == 'FLOAT':
                    dt = DataType.FLOAT
                elif f.field_type.name == 'BOOLEAN':
                    dt = DataType.BOOLEAN
                elif f.field_type.name == 'DATE':
                    dt = DataType.DATE
                fields.append(Field(name=f.name, data_type=dt,
                                    is_primary_key=f.is_primary_key,
                                    is_foreign_key=f.is_foreign_key,
                                    references=f.refers_to))
            node = Node(id=f"src_{table.name}", name=table.name,
                        node_type=NodeType.SOURCE_TABLE, fields=fields,
                        x=x, y=y, table_name=table.name)
            node.refs = {}
            self.scene.add_node(node)
            y += 180
            if y > self.scene.height() - 200:
                y = 30
                x += 280
                if x > divider - 240:
                    break

        # FK-связи источника
        for node_item in list(self.scene.nodes.values()):
            if node_item.node.node_type != NodeType.SOURCE_TABLE:
                continue
            for field in node_item.node.fields:
                if field.is_foreign_key and field.references:
                    for target_item in self.scene.nodes.values():
                        if (target_item.node.table_name == field.references
                                and target_item.node.node_type == NodeType.SOURCE_TABLE):
                            pk = next((f for f in target_item.node.fields if f.is_primary_key), None)
                            if pk:
                                src_fi = self._find_field_item(node_item, field.name)
                                tgt_fi = self._find_field_item(target_item, pk.name)
                                if src_fi and tgt_fi:
                                    self.scene.add_link(src_fi, tgt_fi, LinkType.FK_SOURCE)

    # -----------------------------------------------------------------
    # Загрузка сущностей Mozart
    # -----------------------------------------------------------------
    def load_mozart_entities(self):
        # Сохраняем существующие связи перед перезагрузкой
        existing_links = []
        for link in self.scene.links:
            if link.link_type == LinkType.IMPORT:
                existing_links.append({
                    'source_table': link.start_item.node.table_name,
                    'source_field': link.start_field_item.field.name,
                    'target_entity_id': link.end_item.node.entity_id,
                    'target_field': link.end_field_item.field.name,
                    'mappings': link.mappings
                })

        # Удаляем старые Mozart-ноды
        to_remove = [nid for nid, ni in self.scene.nodes.items()
                     if ni.node.node_type == NodeType.MOZART_ENTITY]
        for nid in to_remove:
            self.scene.removeItem(self.scene.nodes[nid])
            del self.scene.nodes[nid]
        for link in self.scene.links[:]:
            if link.link_type == LinkType.IMPORT:
                self.scene.removeItem(link)
                self.scene.links.remove(link)

        rows = self.db.execute_query(
            "SELECT id, cname, calias, class_id FROM meta.entitytypes ORDER BY cname"
        )
        divider = self.scene.divider_x
        x, y = divider + 30, 30
        for eid, cname, calias, class_id in rows:
            class_res = self.db.execute_query(
                "SELECT calias FROM meta.entity_classes WHERE id=%s", (class_id,))
            class_alias = class_res[0][0] if class_res else "DICT"

            fields = []
            frows = self.db.execute_query(
                "SELECT cfieldname, cfieldtype FROM meta.fields WHERE entitytypeid=%s AND is_system=False ORDER BY isortorder",
                (eid,))
            for fname, ftype in frows:
                dt = DataType.STRING
                if ftype == 'I':
                    dt = DataType.INTEGER
                elif ftype == 'N':
                    dt = DataType.FLOAT
                elif ftype == 'L':
                    dt = DataType.BOOLEAN
                fields.append(Field(name=fname, data_type=dt))

            node = Node(id=f"moz_{eid}", name=f"{cname} ({calias})",
                        node_type=NodeType.MOZART_ENTITY, fields=fields,
                        x=x, y=y, entity_id=eid, class_alias=class_alias)
            self.scene.add_node(node)
            y += 180
            if y > self.scene.height() - 200:
                y = 30
                x += 280

        # Восстанавливаем связи
        for ld in existing_links:
            src_node = self._find_node_by_table(ld['source_table'])
            tgt_node = self._find_node_by_entity(ld['target_entity_id'])
            if src_node and tgt_node:
                self.scene.add_link(src_node, tgt_node, LinkType.IMPORT, mappings=ld.get('mappings'))

    # -----------------------------------------------------------------
    # Диалог настройки связи (импорта)
    # -----------------------------------------------------------------
    def edit_link_between(self, source_node_item, mozart_node_item, existing_mappings, checked_source_fields,
                          source_refs):
        if not checked_source_fields:
            checked_source_fields = [fi.field.name for fi in source_node_item.field_items]

        target_fields = [fi.field.name for fi in mozart_node_item.field_items]
        if SOURCE_ID_FIELD not in target_fields:
            target_fields.append(SOURCE_ID_FIELD)

        dlg = LinkEditDialog(checked_source_fields, target_fields, existing_mappings, source_refs, self)
        if dlg.exec_():
            new_mappings = dlg.get_mappings()
            if not new_mappings:
                return

            old_link = self.scene.find_link_between(source_node_item, mozart_node_item)
            if old_link:
                self.scene.remove_link(old_link)

            self.scene.add_link(source_node_item, mozart_node_item, LinkType.IMPORT, mappings=new_mappings)
            self.scene.update_all_links()
            QMessageBox.information(self, self.translator.tr('link_updated_title'),
                                    self.translator.tr('link_updated_message'))

    # -----------------------------------------------------------------
    # Диалог настройки ссылочных полей источника
    # -----------------------------------------------------------------
    def edit_source_refs(self, source_node_item):
        table_name = source_node_item.node.table_name
        fields = [fi.field.name for fi in source_node_item.field_items]
        all_tables = []
        for ni in self.scene.nodes.values():
            if ni.node.node_type == NodeType.SOURCE_TABLE:
                all_tables.append(ni.node.table_name)
        current_refs = getattr(source_node_item.node, 'refs', {})

        dlg = SourceRefDialog(table_name, fields, all_tables, current_refs, self)
        if dlg.exec_():
            new_refs = dlg.get_refs()
            for ni in self.scene.nodes.values():
                if ni.node.node_type == NodeType.SOURCE_TABLE and ni.node.table_name == table_name:
                    ni.node.refs = new_refs
                    break
            QMessageBox.information(self, self.translator.tr('refs_saved_title'),
                                    self.translator.tr('refs_saved_message'))

    # -----------------------------------------------------------------
    # Превью, создание сущности, создание полей
    # -----------------------------------------------------------------
    def preview_table(self, node_item):
        table_name = node_item.node.table_name
        try:
            sample = self.connector.get_table_sample(table_name, limit=100)
        except Exception as e:
            QMessageBox.warning(self, self.translator.tr('error'),
                                f"{self.translator.tr('error_fetch_data')}: {e}")
            return
        if not sample:
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('no_data'))
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(table_name)
        layout = QVBoxLayout(dlg)
        table = QTableWidget()
        if sample:
            headers = list(sample[0].keys())
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(sample))
            for i, row in enumerate(sample):
                for j, col in enumerate(headers):
                    table.setItem(i, j, QTableWidgetItem(str(row.get(col, ''))))
        layout.addWidget(table)
        dlg.exec_()

    def create_entity_from_source(self, source_node_item):
        from ..wizards.wizard_dialogs import NewEntityDialog
        dlg = NewEntityDialog(self, self.db)
        dlg.name_edit.setText(source_node_item.node.name.capitalize())
        dlg.alias_edit.setText(source_node_item.node.name.lower().replace(' ', '_'))
        if dlg.exec_():
            data = dlg.get_data()
            sample = None
            try:
                sample_rows = self.connector.get_table_sample(source_node_item.node.table_name, limit=1)
                if sample_rows:
                    sample = sample_rows[0]
            except Exception:
                pass
            checked = source_node_item.get_checked_fields()
            entity_id = self.entity_creator.create_entity_from_source(
                entity_name=data['cname'],
                entity_alias=data['calias'],
                class_id=data['class_id'],
                source_table_name=source_node_item.node.table_name,
                checked_fields=checked,
                source_sample=sample
            )
            if entity_id:
                self.load_mozart_entities()
                QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('entity_created'))

    def create_fields_for_mozart(self, mozart_node_item):
        src_item = None
        for ni in self.scene.nodes.values():
            if ni.node.node_type == NodeType.SOURCE_TABLE and ni.is_checked():
                src_item = ni
                break
        if not src_item:
            QMessageBox.warning(self, self.translator.tr('warning'),
                                self.translator.tr('warning_select_source_table'))
            return

        sample = None
        try:
            sample_rows = self.connector.get_table_sample(src_item.node.table_name, limit=1)
            if sample_rows:
                sample = sample_rows[0]
        except Exception:
            pass

        fields_to_create = []
        for src_field in src_item.get_checked_fields():
            from .designer_utils import to_field_name
            mozart_name = to_field_name(src_field)
            field_type = 'C'
            nlength = 255
            if sample and src_field in sample:
                val = sample[src_field]
                if isinstance(val, int):
                    field_type = 'I'
                    nlength = 0
                elif isinstance(val, float):
                    field_type = 'N'
                    nlength = 15
                elif isinstance(val, bool):
                    field_type = 'L'
                    nlength = 0
            fields_to_create.append({
                'cfieldname': mozart_name,
                'cfieldtype': field_type,
                'calias': src_field.capitalize()[:50],
                'nlength': nlength,
                'lisindexed': True
            })
        if fields_to_create:
            self.field_creator.create_fields(mozart_node_item.node.entity_id, fields_to_create)
            self.load_mozart_entities()
            QMessageBox.information(self, self.translator.tr('info'),
                                    f"{self.translator.tr('fields_created')} {len(fields_to_create)}")

    # -----------------------------------------------------------------
    # Сохранение и импорт
    # -----------------------------------------------------------------
    def save_profile(self):
        profile = SceneProfileAdapter.scene_to_profile(self.scene, self.connector, self.db, self.editing_profile_id)
        profile.import_mode = self.mode_combo.currentData()
        prof_mgr = ProfileManager(self.db)
        prof_mgr.save_profile(profile)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('profile_saved'))

    def perform_import(self):
        profile = SceneProfileAdapter.scene_to_profile(self.scene, self.connector, self.db, self.editing_profile_id)
        profile.import_mode = self.mode_combo.currentData()

        source_tables = list(set([link['source_table'] for link in profile.import_links]))
        if not source_tables:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_no_tables'))
            return

        progress_dlg = ImportProgressDialog(len(source_tables), self)
        orchestrator = ImportOrchestrator(self.db, self.connector, profile)

        def on_progress(event, **kwargs):
            if event == 'table_start':
                progress_dlg.start_table(kwargs['table_name'], kwargs.get('total_records', 0))
            elif event == 'table_update':
                progress_dlg.update_table_progress(kwargs['processed'], kwargs.get('total', 0))
            elif event == 'table_finish':
                progress_dlg.finish_table(
                    kwargs.get('inserted', 0), kwargs.get('updated', 0),
                    kwargs.get('errors', 0), kwargs.get('skipped', 0)
                )
            elif event == 'all_finish':
                stats = kwargs.get('stats', {})
                msg = self.translator.tr('import_finished_stats').format(
                    stats.get('inserted', 0), stats.get('updated', 0), stats.get('errors', 0))
                if stats.get('skipped', 0) > 0:
                    msg += f", {self.translator.tr('skipped_count')}: {stats.get('skipped', 0)}"
                QMessageBox.information(self, self.translator.tr('import_finished_title'), msg)
                if orchestrator.errors:
                    QMessageBox.warning(self, self.translator.tr('warning'), "\n".join(orchestrator.errors[:20]))

        try:
            progress_dlg.show()
            QApplication.processEvents()
            stats = orchestrator.run(progress_callback=on_progress, progress_dialog=progress_dlg)
            progress_dlg.finish_all()
            progress_dlg.accept()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))
            progress_dlg.reject()

    def load_profile_links(self, profile: ImportProfile):
        for link in self.scene.links[:]:
            if link.link_type == LinkType.IMPORT:
                self.scene.removeItem(link)
                self.scene.links.remove(link)
        SceneProfileAdapter.restore_scene(self.scene, profile)
        idx = self.mode_combo.findData(profile.import_mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)

    # -----------------------------------------------------------------
    # Вспомогательные методы
    # -----------------------------------------------------------------
    def _find_field_item(self, node_item, field_name):
        for fi in node_item.field_items:
            if fi.field.name == field_name:
                return fi
        return None

    def _find_node_by_table(self, table_name):
        for ni in self.scene.nodes.values():
            if ni.node.node_type == NodeType.SOURCE_TABLE and ni.node.table_name == table_name:
                return ni
        return None

    def _find_node_by_entity(self, entity_id):
        for ni in self.scene.nodes.values():
            if ni.node.node_type == NodeType.MOZART_ENTITY and ni.node.entity_id == entity_id:
                return ni
        return None