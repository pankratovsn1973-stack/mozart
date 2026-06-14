# mozart_import/graph/relation_scene.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QVBoxLayout, QHeaderView)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTransform

from .graphics_items import NodeItem, FieldItem, SOURCE_ID_FIELD
from .link_line import LinkLine
from ..core.models import Node, NodeType, LinkType
from lang.local_translator import LocalTranslator
from PySide6.QtWidgets import QGraphicsScene

class RelationScene(QGraphicsScene):
    """Графическая сцена конструктора импорта с виртуальным разделителем."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = LocalTranslator()
        self.setBackgroundBrush(QColor(245, 245, 245))
        scene_width = 3000
        scene_height = 3000
        self.setSceneRect(0, 0, scene_width, scene_height)

        self.divider_x = scene_width / 2
        self.nodes = {}
        self.links = []

        # Коллбэки
        self.on_edit_link = None
        self.on_preview_table = None
        self.on_create_entity = None
        self.on_create_fields_from_source = None
        self.on_set_source_refs = None

    def clear_scene(self):
        for node_item in list(self.nodes.values()):
            self.removeItem(node_item)
        for link in self.links[:]:
            self.removeItem(link)
        self.nodes.clear()
        self.links.clear()

    def add_node(self, node: Node):
        item = NodeItem(node)
        if node.node_type == NodeType.SOURCE_TABLE:
            max_x = self.divider_x - item.rect().width() - 10
            if node.x > max_x:
                node.x = max_x
            if node.x < 10:
                node.x = 10
        else:
            if node.x < self.divider_x + 10:
                node.x = self.divider_x + 10
        item.setPos(node.x, node.y)
        self.addItem(item)
        self.nodes[node.id] = item
        return item

    def add_link(self, start_node_item, end_node_item, link_type: LinkType, mappings=None):
        if link_type == LinkType.IMPORT:
            if (start_node_item.node.node_type != NodeType.SOURCE_TABLE or
                    end_node_item.node.node_type != NodeType.MOZART_ENTITY):
                return None
            if mappings:
                first_m = mappings[0]
                last_m = mappings[-1]
                src_fi = self._find_field_item(start_node_item, first_m['source_field'])
                tgt_fi = self._find_field_item(end_node_item, last_m.get('target_field'))
                if not src_fi or not tgt_fi:
                    if start_node_item.field_items and end_node_item.field_items:
                        src_fi = start_node_item.field_items[0]
                        tgt_fi = end_node_item.field_items[0]
                    else:
                        return None
                link = LinkLine(start_node_item, src_fi, end_node_item, tgt_fi, link_type, mappings=mappings)
                self.addItem(link)
                self.links.append(link)
                return link
            else:
                if start_node_item.field_items and end_node_item.field_items:
                    src_fi = start_node_item.field_items[0]
                    tgt_fi = end_node_item.field_items[0]
                    link = LinkLine(start_node_item, src_fi, end_node_item, tgt_fi, link_type)
                    self.addItem(link)
                    self.links.append(link)
                    return link
        elif link_type == LinkType.FK_SOURCE:
            if (start_node_item.node.node_type != NodeType.SOURCE_TABLE or
                    end_node_item.node.node_type != NodeType.SOURCE_TABLE):
                return None
            if start_node_item.field_items and end_node_item.field_items:
                src_fi = start_node_item.field_items[0]
                tgt_fi = end_node_item.field_items[0]
                link = LinkLine(start_node_item, src_fi, end_node_item, tgt_fi, link_type)
                self.addItem(link)
                self.links.append(link)
                return link
        return None

    def remove_link(self, link_line: LinkLine):
        """Удаляет линию со сцены и из списка links."""
        if link_line in self.links:
            self.links.remove(link_line)
        self.removeItem(link_line)

    def find_link_between(self, source_node_item, target_node_item):
        """Возвращает линию связи между двумя узлами, если она есть."""
        for link in self.links:
            if (link.link_type == LinkType.IMPORT and
                link.start_item == source_node_item and
                link.end_item == target_node_item):
                return link
        return None

    def _find_field_item(self, node_item, field_name):
        for fi in node_item.field_items:
            if fi.field.name == field_name:
                return fi
        return None

    # ------------ Контекстные меню ------------
    def contextMenuEvent(self, event):
        view = self.views()[0] if self.views() else None
        if view:
            scene_pos = view.mapToScene(event.pos())
        else:
            scene_pos = event.scenePos()
        item = self.itemAt(scene_pos, QTransform())
        if isinstance(item, NodeItem):
            self._show_node_context_menu(item, event.screenPos())
        elif isinstance(item, LinkLine):
            self._show_link_context_menu(item, event.screenPos())
        else:
            self._show_scene_context_menu(event.screenPos())

    def _show_node_context_menu(self, node_item, screen_pos):
        menu = QMenu()
        if node_item.node.node_type == NodeType.SOURCE_TABLE:
            act_preview = QAction(self.translator.tr('context_preview_table'), None)
            act_preview.triggered.connect(lambda: self.on_preview_table(node_item))
            menu.addAction(act_preview)

            act_create = QAction(self.translator.tr('context_create_entity'), None)
            act_create.triggered.connect(lambda: self.on_create_entity(node_item))
            menu.addAction(act_create)

            menu.addSeparator()
            act_refs = QAction(self.translator.tr('context_ref_fields'), None)
            act_refs.triggered.connect(lambda: self.on_set_source_refs(node_item))
            menu.addAction(act_refs)

            menu.addSeparator()
            act_all = QAction(self.translator.tr('context_select_all_fields'), None)
            act_all.triggered.connect(lambda: node_item.set_all_checked(True))
            menu.addAction(act_all)
            act_none = QAction(self.translator.tr('context_deselect_all_fields'), None)
            act_none.triggered.connect(lambda: node_item.set_all_checked(False))
            menu.addAction(act_none)
        else:  # Mozart
            act_show_links = QAction(self.translator.tr('context_show_import_links'), None)
            act_show_links.triggered.connect(lambda: self._show_import_links_for(node_item))
            menu.addAction(act_show_links)

            act_fields = QAction(self.translator.tr('context_create_fields_from_table'), None)
            act_fields.triggered.connect(lambda: self.on_create_fields_from_source(node_item))
            menu.addAction(act_fields)

        menu.exec_(screen_pos)

    def _show_link_context_menu(self, link_line, screen_pos):
        menu = QMenu()
        act_edit = QAction(self.translator.tr('context_configure_link'), None)
        act_edit.triggered.connect(lambda: self.on_edit_link(
            link_line.start_item, link_line.end_item,
            link_line.mappings,
            [fi.field.name for fi in link_line.start_item.field_items],
            getattr(link_line.start_item.node, 'refs', {})
        ))
        menu.addAction(act_edit)
        act_del = QAction(self.translator.tr('context_delete_link'), None)
        act_del.triggered.connect(lambda: self.remove_link(link_line))
        menu.addAction(act_del)
        menu.exec_(screen_pos)

    def _show_scene_context_menu(self, screen_pos):
        selected_source = self._get_single_checked(NodeType.SOURCE_TABLE)
        selected_mozart = self._get_single_checked(NodeType.MOZART_ENTITY)

        menu = QMenu()
        if selected_source and selected_mozart:
            act_link = QAction(self.translator.tr('context_link_selected'), None)
            act_link.triggered.connect(lambda: self._link_selected(selected_source, selected_mozart))
            menu.addAction(act_link)
        else:
            hint = self.translator.tr('context_hint_select_one')
            menu.addAction(hint)

        menu.addSeparator()
        act_refresh = QAction(self.translator.tr('context_refresh_links'), None)
        act_refresh.triggered.connect(self.update_all_links)
        menu.addAction(act_refresh)

        menu.exec_(screen_pos)

    def _get_single_checked(self, node_type):
        checked = []
        for ni in self.nodes.values():
            if ni.node.node_type == node_type and ni.is_checked():
                checked.append(ni)
        return checked[0] if len(checked) == 1 else None

    def _link_selected(self, source_node_item, mozart_node_item):
        checked_source_fields = source_node_item.get_checked_fields()
        if not checked_source_fields:
            checked_source_fields = [fi.field.name for fi in source_node_item.field_items]

        target_fields = [fi.field.name for fi in mozart_node_item.field_items]
        if SOURCE_ID_FIELD not in target_fields:
            target_fields.append(SOURCE_ID_FIELD)

        existing_mappings = []
        for link in self.links:
            if (link.link_type == LinkType.IMPORT and
                link.start_item == source_node_item and
                link.end_item == mozart_node_item):
                if link.mappings:
                    existing_mappings = link.mappings
                    break
        if not existing_mappings:
            for d in self.get_import_links_data():
                if (d['source_table'] == source_node_item.node.table_name and
                    d['target_entity_id'] == mozart_node_item.node.entity_id):
                    existing_mappings = d.get('mappings', [])
                    break

        if self.on_edit_link:
            source_refs = getattr(source_node_item.node, 'refs', {})
            self.on_edit_link(source_node_item, mozart_node_item, existing_mappings,
                              checked_source_fields, source_refs)
        else:
            QMessageBox.information(None, self.translator.tr('info'),
                                   self.translator.tr('callback_not_assigned'))

    def _show_import_links_for(self, mozart_node_item):
        entity_name = mozart_node_item.node.name
        relevant_links = []
        for link in self.links:
            if link.link_type == LinkType.IMPORT and link.end_item == mozart_node_item:
                relevant_links.append(link)
        if not relevant_links:
            QMessageBox.information(None, f"{self.translator.tr('import_links_for')} {entity_name}",
                                   self.translator.tr('no_import_links'))
            return

        dlg = QDialog()
        dlg.setWindowTitle(f"{self.translator.tr('import_links_for')} {entity_name}")
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels([
            self.translator.tr('source_table_field'),
            self.translator.tr('mozart_field'),
            self.translator.tr('key_field'),
            self.translator.tr('reference'),
            self.translator.tr('target')
        ])
        table.horizontalHeader().setStretchLastSection(True)

        for link in relevant_links:
            src_table = link.start_item.node.name
            for m in link.mappings:
                row = table.rowCount()
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{src_table}.{m['source_field']}"))
                table.setItem(row, 1, QTableWidgetItem(m['target_field']))
                is_key = "🔑" if m.get('is_source_id') else ""
                table.setItem(row, 2, QTableWidgetItem(is_key))
                is_ref = self.translator.tr('yes') if m.get('is_reference') else ""
                table.setItem(row, 3, QTableWidgetItem(is_ref))
                if m.get('is_reference'):
                    ref_info = f"{m.get('ref_source_table','')}.{m.get('ref_source_key_field','')}"
                else:
                    ref_info = ""
                table.setItem(row, 4, QTableWidgetItem(ref_info))
        layout.addWidget(table)
        dlg.exec_()

    def update_all_links(self):
        for link in self.links:
            link.update_position()

    def get_import_links_data(self):
        data = []
        for link in self.links:
            if link.link_type == LinkType.IMPORT:
                data.append({
                    'source_table': link.start_item.node.table_name,
                    'target_entity_id': link.end_item.node.entity_id,
                    'mappings': link.mappings
                })
        return data

    # Эмиттеры
    def _emit_preview(self, node_item):
        if self.on_preview_table:
            self.on_preview_table(node_item)

    def _emit_create_entity(self, node_item):
        if self.on_create_entity:
            self.on_create_entity(node_item)

    def _emit_create_fields(self, node_item):
        if self.on_create_fields_from_source:
            self.on_create_fields_from_source(node_item)

    def _emit_edit_link(self, link_line):
        if self.on_edit_link:
            source_node_item = link_line.start_item
            checked_fields = source_node_item.get_checked_fields()
            if not checked_fields:
                checked_fields = [fi.field.name for fi in source_node_item.field_items]
            source_refs = getattr(source_node_item.node, 'refs', {})
            self.on_edit_link(link_line.start_item, link_line.end_item,
                              link_line.mappings, checked_fields, source_refs)

    def _emit_set_source_refs(self, node_item):
        if self.on_set_source_refs:
            self.on_set_source_refs(node_item)