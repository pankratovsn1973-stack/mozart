# -*- coding: utf-8 -*-

import json
from PySide6.QtWidgets import QWizardPage, QVBoxLayout, QPushButton, QMessageBox, QHBoxLayout, QDialog, QVBoxLayout as QVBoxLayoutD, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from lang.local_translator import LocalTranslator
from ..graph.graphics_view import GraphicsView
from ..graph.relation_scene import RelationScene
from ..core.models import Node, NodeType, Field, DataType, LinkType
from .wizard_dialogs import NewEntityDialog


class RelationPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = LocalTranslator()
        self.setTitle(self.translator.tr('relation_page_title'))
        self.setSubTitle(self.translator.tr('relation_page_subtitle'))

        layout = QVBoxLayout(self)

        self.scene = RelationScene(self, relation_page=self)  # передаём себя
        self.view = GraphicsView(self.scene)
        layout.addWidget(self.view, 1)

        btn_layout = QHBoxLayout()
        self.btn_load_source = QPushButton(self.translator.tr('load_source_btn'))
        self.btn_load_source.clicked.connect(self.load_source)
        self.btn_load_mozart = QPushButton(self.translator.tr('load_mozart_btn'))
        self.btn_load_mozart.clicked.connect(self.load_existing_entities)
        self.btn_create_entity = QPushButton(self.translator.tr('create_entity_btn'))
        self.btn_create_entity.clicked.connect(self.create_entity)
        self.btn_save_mapping = QPushButton(self.translator.tr('save_mapping_btn'))
        self.btn_save_mapping.clicked.connect(self.save_mapping)
        btn_layout.addWidget(self.btn_load_source)
        btn_layout.addWidget(self.btn_load_mozart)
        btn_layout.addWidget(self.btn_create_entity)
        btn_layout.addWidget(self.btn_save_mapping)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.source_nodes = []
        self.mozart_nodes = []

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('relation_page_title'))
        self.setSubTitle(self.translator.tr('relation_page_subtitle'))
        self.btn_load_source.setText(self.translator.tr('load_source_btn'))
        self.btn_load_mozart.setText(self.translator.tr('load_mozart_btn'))
        self.btn_create_entity.setText(self.translator.tr('create_entity_btn'))
        self.btn_save_mapping.setText(self.translator.tr('save_mapping_btn'))

    def clear_scene(self):
        self.scene.clear()
        self.source_nodes = []
        self.mozart_nodes = []

    def load_source(self):
        if not self.wizard.connector:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('connector_not_ready'))
            return
        self.clear_scene()
        schema = self.wizard.connector.get_schema()
        if not schema.tables:
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('no_tables_found'))
            return
        x = 50
        y = 50
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
                elif f.field_type.name == 'DATETIME':
                    dt = DataType.DATETIME
                fields.append(Field(
                    name=f.name,
                    data_type=dt,
                    is_primary_key=f.is_primary_key,
                    is_foreign_key=f.is_foreign_key,
                    references=f.refers_to
                ))
            node = Node(
                id=f"src_{table.name}",
                name=table.name,
                node_type=NodeType.SOURCE_TABLE,
                fields=fields,
                x=x, y=y,
                table_name=table.name
            )
            self.scene.add_node(node)
            self.source_nodes.append(node)
            x += 250
            if x > 500:
                x = 50
                y += 250

        # Автоматические связи FK
        for node in self.source_nodes:
            for field in node.fields:
                if field.is_foreign_key and field.references:
                    target_table_name = field.references
                    for target_node in self.source_nodes:
                        if target_node.table_name == target_table_name:
                            target_field = None
                            for tf in target_node.fields:
                                if tf.is_primary_key:
                                    target_field = tf
                                    break
                            if target_field:
                                start_fi = self.find_field_item(node, field.name)
                                end_fi = self.find_field_item(target_node, target_field.name)
                                if start_fi and end_fi:
                                    self.scene.add_link(start_fi, end_fi, LinkType.FK_SOURCE)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('source_loaded').format(len(schema.tables)))

    def find_field_item(self, node_item, field_name):
        for fi in node_item.field_items:
            if fi.field.name == field_name:
                return fi
        return None

    def load_existing_entities(self):
        if not self.wizard.db:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('db_not_ready'))
            return
        rows = self.wizard.db.execute_query("SELECT id, cname, calias, class_id FROM meta.entitytypes ORDER BY cname")
        x = 600
        y = 50
        for eid, cname, calias, class_id in rows:
            class_res = self.wizard.db.execute_query("SELECT calias FROM meta.entity_classes WHERE id=%s", (class_id,))
            class_alias = class_res[0][0] if class_res else "DICT"
            fields = []
            frows = self.wizard.db.execute_query("SELECT cfieldname, cfieldtype FROM meta.fields WHERE entitytypeid=%s", (eid,))
            for fname, ftype in frows:
                dt = DataType.STRING
                if ftype == 'I':
                    dt = DataType.INTEGER
                elif ftype == 'N':
                    dt = DataType.FLOAT
                elif ftype == 'L':
                    dt = DataType.BOOLEAN
                elif ftype == 'D':
                    dt = DataType.DATE
                elif ftype == 'T':
                    dt = DataType.DATETIME
                fields.append(Field(name=fname, data_type=dt))
            node = Node(
                id=f"moz_{eid}",
                name=f"{cname} ({calias})",
                node_type=NodeType.MOZART_ENTITY,
                fields=fields,
                x=x, y=y,
                entity_id=eid,
                class_alias=class_alias
            )
            self.scene.add_node(node)
            self.mozart_nodes.append(node)
            x += 250
            if x > 1200:
                x = 600
                y += 250

        # Связи композиции
        comps = self.wizard.db.execute_query("SELECT parent_entityid, child_entityid, c_link_fieldname FROM meta.entity_composition")
        for parent_id, child_id, link_field in comps:
            parent_node = None
            child_node = None
            for n in self.mozart_nodes:
                if n.entity_id == parent_id:
                    parent_node = n
                if n.entity_id == child_id:
                    child_node = n
            if parent_node and child_node:
                # Ищем поле в дочерней сущности с именем link_field
                child_field = None
                for f in child_node.fields:
                    if f.name == link_field:
                        child_field = f
                        break
                if child_field:
                    # Для родителя используем первое поле (или можно создать линию без привязки к полю)
                    parent_field = parent_node.fields[0] if parent_node.fields else None
                    if parent_field:
                        start_fi = self.find_field_item(parent_node, parent_field.name)
                        end_fi = self.find_field_item(child_node, child_field.name)
                        if start_fi and end_fi:
                            self.scene.add_link(start_fi, end_fi, LinkType.COMPOSITION)
        QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('mozart_loaded').format(len(rows)))

    def create_entity(self):
        dlg = NewEntityDialog(self, self.wizard.db)
        if dlg.exec_():
            data = dlg.get_data()
            node = Node(
                id=f"new_{data['calias']}",
                name=data['cname'],
                node_type=NodeType.MOZART_ENTITY,
                fields=[],
                x=600, y=300,
                class_alias="DICT"
            )
            self.scene.add_node(node)
            if not hasattr(self.wizard, 'pending_entities'):
                self.wizard.pending_entities = []
            self.wizard.pending_entities.append((node, data))
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('entity_added_to_scene'))

    def save_mapping(self):
        nodes_pos = {}
        for node_item in self.scene.nodes.values():
            nodes_pos[node_item.node.id] = {'x': node_item.node.x, 'y': node_item.node.y}
        links_data = []
        for link_line in self.scene.links:
            link_dict = {
                'source_node_id': link_line.start_item.node.id,
                'source_field': link_line.start_field_item.field.name,
                'target_node_id': link_line.end_item.node.id,
                'target_field': link_line.end_field_item.field.name,
                'link_type': link_line.link_type.value,
                'is_source_id': getattr(link_line, 'is_source_id', False)
            }
            links_data.append(link_dict)
        scene_data = {
            'nodes_pos': nodes_pos,
            'links': links_data
        }
        self.wizard.import_scene_json = json.dumps(scene_data, ensure_ascii=False)
        self.wizard.source_nodes = self.source_nodes
        self.wizard.mozart_nodes = self.mozart_nodes
        self.wizard.links = links_data
        self.wizard.next()

    def preview_table(self, node_item):
        if not self.wizard.connector:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('connector_not_ready'))
            return
        table_name = node_item.node.table_name
        sample = self.wizard.connector.get_table_sample(table_name, limit=20)
        if not sample:
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('no_data'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.translator.tr('preview_table_title').format(table_name))
        layout = QVBoxLayoutD(dlg)
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