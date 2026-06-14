# mozart_import/designer/scene_profile_adapter.py
# -*- coding: utf-8 -*-

from typing import Optional
from database import DatabaseService
from ..core.models import ImportProfile, SourceType, FileFormat, NodeType, LinkType


class SceneProfileAdapter:
    @staticmethod
    def _get_entity_name(db: DatabaseService, entity_id: int) -> str:
        """Возвращает cname сущности по её ID, или пустую строку, если не найдено."""
        if not entity_id:
            return ''
        try:
            rows = db.execute_query("SELECT cname FROM meta.entitytypes WHERE id = %s", (entity_id,))
            return rows[0][0] if rows else ''
        except Exception:
            return f"Entity_{entity_id}"

    @staticmethod
    def scene_to_profile(scene, connector, db: DatabaseService, editing_profile_id: Optional[int] = None) -> ImportProfile:
        """Преобразует сцену в объект ImportProfile с гарантированным заполнением имени целевой сущности."""
        # Параметры подключения
        src_type = SourceType.FILE
        file_format = None
        db_type = None
        db_host = None
        db_port = None
        db_name = None
        db_user = None
        db_pass = None

        if hasattr(connector, 'file_format'):
            src_type = SourceType.FILE
            file_format = connector.file_format.value if isinstance(connector.file_format, FileFormat) else str(connector.file_format)
        elif hasattr(connector, 'db_type'):
            src_type = SourceType.DATABASE
            db_type = connector.db_type
            db_host = connector.host
            db_port = int(connector.port) if connector.port else None
            db_name = connector.database
            db_user = connector.user
            db_pass = connector.password
        else:
            src_type = SourceType.URL

        # Таблицы источника
        source_tables = []
        for node_item in scene.nodes.values():
            if node_item.node.node_type != NodeType.SOURCE_TABLE:
                continue
            row_count = None
            try:
                row_count = connector.get_row_count(node_item.node.table_name)
            except Exception:
                pass
            sample_rows = []
            try:
                sample = connector.get_table_sample(node_item.node.table_name, limit=5)
                sample_rows = sample
            except Exception:
                pass
            source_tables.append({
                'name': node_item.node.table_name,
                'row_count': row_count,
                'sample_rows': sample_rows
            })

        # Группируем связи импорта по (source_table, target_entity_id)
        links_by_target = {}
        for link in scene.links:
            if link.link_type != LinkType.IMPORT:
                continue
            start_node = link.start_item.node
            end_node = link.end_item.node
            if end_node.entity_id is None:
                continue

            refs = getattr(start_node, 'refs', {})
            key = (start_node.table_name, end_node.entity_id)

            if key not in links_by_target:
                # Получаем имя сущности: сначала из end_node.name, если пусто – из БД
                entity_name = end_node.name
                if not entity_name and end_node.entity_id:
                    entity_name = SceneProfileAdapter._get_entity_name(db, end_node.entity_id)
                if not entity_name:
                    entity_name = f"Entity_{end_node.entity_id}"

                links_by_target[key] = {
                    'source_table': start_node.table_name,
                    'target_entity_id': end_node.entity_id,
                    'target_entity_name': entity_name,  # <-- ЭТА СТРОКА ВАЖНА!
                    'mappings': []
                }

            # Обрабатываем маппинги линии
            if link.mappings:
                for m in link.mappings:
                    src_field = m.get('source_field')
                    ref_info = refs.get(src_field, {})
                    enriched = {
                        'source_field': src_field,
                        'target_field': m.get('target_field'),
                        'is_source_id': m.get('is_source_id', False),
                        'is_reference': ref_info.get('is_ref', False),
                        'ref_source_table': ref_info.get('ref_table', ''),
                        'ref_source_key_field': ref_info.get('ref_field', '')
                    }
                    if not any(ex['source_field'] == enriched['source_field'] and ex['target_field'] == enriched['target_field']
                               for ex in links_by_target[key]['mappings']):
                        links_by_target[key]['mappings'].append(enriched)
            else:
                # Одиночный маппинг
                src_field = link.start_field_item.field.name
                tgt_field = link.end_field_item.field.name
                ref_info = refs.get(src_field, {})
                mapping = {
                    'source_field': src_field,
                    'target_field': tgt_field,
                    'is_source_id': (tgt_field == 'sourceid'),
                    'is_reference': ref_info.get('is_ref', False),
                    'ref_source_table': ref_info.get('ref_table', ''),
                    'ref_source_key_field': ref_info.get('ref_field', '')
                }
                if not any(ex['source_field'] == mapping['source_field'] and ex['target_field'] == mapping['target_field']
                           for ex in links_by_target[key]['mappings']):
                    links_by_target[key]['mappings'].append(mapping)

        # Автоматическое добавление ключевой пары (sourceid) если отсутствует
        for key, entry in links_by_target.items():
            source_id_mapping = next((m for m in entry['mappings'] if m.get('is_source_id')), None)
            if source_id_mapping:
                continue

            source_table_name = entry['source_table']
            source_node = None
            for ni in scene.nodes.values():
                if (ni.node.node_type == NodeType.SOURCE_TABLE and
                        ni.node.table_name == source_table_name):
                    source_node = ni
                    break

            key_field = None
            refs_of_node = getattr(source_node.node, 'refs', {}) if source_node else {}
            for fname, rinfo in refs_of_node.items():
                if not rinfo.get('is_ref'):
                    key_field = fname
                    break
            if not key_field and source_node:
                key_field = source_node.node.fields[0].name if source_node.node.fields else None

            if key_field:
                entry['mappings'].append({
                    'source_field': key_field,
                    'target_field': 'sourceid',
                    'is_source_id': True,
                    'is_reference': False,
                    'ref_source_table': '',
                    'ref_source_key_field': ''
                })

        target_entities = []
        import_links = []
        for key, entry in links_by_target.items():
            target_entities.append({'id': entry['target_entity_id'], 'name': entry['target_entity_name']})
            import_links.append({
                'source_table': entry['source_table'],
                'target_entity_id': entry['target_entity_id'],
                'target_entity_name': entry['target_entity_name'],  # <-- ЭТА СТРОКА ВАЖНА!
                'mappings': entry['mappings']
            })

        # FK связи источника
        source_fk_links = []
        for link in scene.links:
            if link.link_type == LinkType.FK_SOURCE:
                source_fk_links.append({
                    'source_table': link.start_item.node.table_name,
                    'source_field': link.start_field_item.field.name,
                    'target_table': link.end_item.node.table_name,
                    'target_field': link.end_field_item.field.name
                })

        # Сбор ручных настроек ссылок источника (source_references)
        source_references = []
        for node_item in scene.nodes.values():
            if node_item.node.node_type != NodeType.SOURCE_TABLE:
                continue
            refs = getattr(node_item.node, 'refs', {})
            for field_name, ref_info in refs.items():
                if ref_info.get('is_ref'):
                    source_references.append({
                        'source_table': node_item.node.table_name,
                        'source_field': field_name,
                        'ref_table': ref_info['ref_table'],
                        'ref_field': ref_info['ref_field']
                    })

        return ImportProfile(
            id=editing_profile_id,
            name=connector.source_path,
            source_type=src_type,
            source_path=connector.source_path,
            source_tables=source_tables,
            target_entities=target_entities,
            import_links=import_links,
            source_fk_links=source_fk_links,
            source_references=source_references,
            file_format=file_format,
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_pass=db_pass
        )

    @staticmethod
    def restore_scene(scene, profile: ImportProfile, mozart_entities=None):
        """Восстанавливает связи импорта и внутренние ссылки источника на сцене."""
        # Восстанавливаем refs для всех узлов источника из profile.source_references
        for ref in profile.source_references:
            for nitem in scene.nodes.values():
                if (nitem.node.node_type == NodeType.SOURCE_TABLE and
                        nitem.node.table_name == ref['source_table']):
                    refs = getattr(nitem.node, 'refs', {})
                    refs[ref['source_field']] = {
                        'is_ref': True,
                        'ref_table': ref['ref_table'],
                        'ref_field': ref['ref_field']
                    }
                    nitem.node.refs = refs
                    break

        # Восстанавливаем связи импорта
        for link_data in profile.import_links:
            source_table = link_data['source_table']
            target_entity_id = link_data['target_entity_id']
            source_node = None
            target_node = None
            for nitem in scene.nodes.values():
                if nitem.node.node_type == NodeType.SOURCE_TABLE and nitem.node.table_name == source_table:
                    source_node = nitem
                elif nitem.node.node_type == NodeType.MOZART_ENTITY and nitem.node.entity_id == target_entity_id:
                    target_node = nitem
            if not source_node or not target_node:
                continue

            mappings = link_data.get('mappings', [])
            # Удаляем старые линии между этими узлами
            for link in scene.links[:]:
                if link.link_type == LinkType.IMPORT and link.start_item == source_node and link.end_item == target_node:
                    scene.removeItem(link)
                    scene.links.remove(link)

            # Создаём новую линию и принудительно записываем маппинги
            if mappings:
                link = scene.add_link(source_node, target_node, LinkType.IMPORT, mappings=mappings)
                if link:
                    link.mappings = mappings
            else:
                link = scene.add_link(source_node, target_node, LinkType.IMPORT)

        scene.update_all_links()