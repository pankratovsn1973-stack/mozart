# mozart_import/core/import_orchestrator.py
# -*- coding: utf-8 -*-

from collections import deque
from typing import Dict, List, Optional, Any, Callable
from database import DatabaseService
from .models import ImportProfile, MatchedEntity, MatchedField
from .import_engine import ImportEngine


class ImportOrchestrator:
    """
    Управляет порядком импорта таблиц источника на основе их зависимостей.
    Сначала загружаются таблицы без ссылок на другие таблицы (корневые),
    затем зависимые.
    Поддерживает обратную связь по прогрессу через callback.
    """

    def __init__(self, db: DatabaseService, connector, profile: ImportProfile):
        self.db = db
        self.connector = connector
        self.profile = profile
        self.engine = ImportEngine(db, connector, profile)
        # Кэш сопоставлений (source_table_name, source_id) -> instance_id
        self.instance_cache: Dict[str, Dict[str, int]] = {}
        # Список ошибок
        self.errors: List[str] = []
        # Текущий прогресс
        self._current_table_index = 0
        self._total_tables = 0

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Строит граф зависимостей: ключ – имя таблицы, которая зависит от списка целевых таблиц.
        Возвращает словарь {таблица: [таблицы_от_которых_зависит]}
        """
        tables = set()
        for link in self.profile.import_links:
            tables.add(link['source_table'])

        graph = {t: [] for t in tables}
        for ref in self.profile.source_references:
            src_table = ref['source_table']
            dst_table = ref['ref_table']
            if src_table in graph and dst_table in graph:
                graph[src_table].append(dst_table)
        return graph

    def _order_tables(self, graph: Dict[str, List[str]]) -> List[str]:
        """Возвращает топологически отсортированный список таблиц."""
        in_degree = {t: 0 for t in graph}
        for src, deps in graph.items():
            for dep in deps:
                in_degree[src] += 1

        queue = deque([t for t, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for src, deps in graph.items():
                if current in deps:
                    in_degree[src] -= 1
                    if in_degree[src] == 0:
                        queue.append(src)

        if len(order) != len(graph):
            remaining = set(graph.keys()) - set(order)
            raise ValueError(f"Циклическая зависимость между таблицами: {', '.join(remaining)}")
        return order

    def _get_total_records(self, table_name: str) -> int:
        """Возвращает примерное количество записей в таблице источника."""
        try:
            return self.connector.get_row_count(table_name) or 0
        except Exception:
            return 0

    def _get_entity_name(self, entity_id: int) -> str:
        """Получает имя сущности по ID из БД."""
        if not entity_id:
            return ""
        try:
            res = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (entity_id,))
            if res:
                return res[0][0]
        except Exception:
            pass
        return f"Entity_{entity_id}"

    def run(self, progress_callback: Optional[Callable] = None, progress_dialog=None) -> Dict[str, int]:
        """
        Выполняет импорт всех таблиц в правильном порядке.
        progress_callback: функция, принимающая (event, **kwargs)
        progress_dialog: объект диалога для обновления UI
        """
        graph = self._build_dependency_graph()
        try:
            ordered_tables = self._order_tables(graph)
        except ValueError as e:
            self.errors.append(str(e))
            return {'inserted': 0, 'updated': 0, 'errors': len(self.errors), 'skipped': 0}

        table_links = {}
        for link in self.profile.import_links:
            table_links[link['source_table']] = link

        total_stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        self._total_tables = len(ordered_tables)

        for self._current_table_index, table_name in enumerate(ordered_tables):
            link = table_links.get(table_name)
            if not link:
                continue

            # Получаем количество записей
            total_records = self._get_total_records(table_name)

            # Уведомляем о начале импорта таблицы
            if progress_callback:
                #print(f"[DEBUG] Вызов progress_callback: table_start для {table_name}")
                progress_callback('table_start', table_name=table_name, total_records=total_records)
            if progress_dialog and hasattr(progress_dialog, 'start_table'):
                progress_dialog.start_table(table_name, total_records)

            # Получаем информацию о целевой сущности
            entity_id = link['target_entity_id']
            entity_name = link.get('target_entity_name', '')
            if not entity_name:
                entity_name = self._get_entity_name(entity_id)

            # Собираем маппинги
            matched_fields = []
            source_id_field = None
            ref_rules = []

            for m in link.get('mappings', []):
                mf = MatchedField(
                    source_field=m['source_field'],
                    target_field=m['target_field'],
                    is_reference=m.get('is_reference', False),
                )
                matched_fields.append(mf)
                if m.get('is_source_id'):
                    source_id_field = m['source_field']

                if m.get('is_reference'):
                    ref_src_table = m.get('ref_source_table', '')
                    ref_src_key_field = m.get('ref_source_key_field', '')
                    target_entity = None
                    for lnk in self.profile.import_links:
                        if lnk['source_table'] == ref_src_table:
                            target_entity = lnk['target_entity_id']
                            break
                    if target_entity:
                        ref_rules.append({
                            'target_field': m['target_field'],
                            'ref_entity_id': target_entity,
                            'ref_key_field': ref_src_key_field
                        })

            entity = MatchedEntity(
                source_table=table_name,
                target_entity_id=entity_id,
                target_entity_name=entity_name,
                confidence=1.0,
                fields=matched_fields,
                source_id_field=source_id_field
            )

            try:
                # Сохраняем оригинальный метод iter_records
                original_iter = self.connector.iter_records
                records_processed = [0]  # список для изменяемой переменной в замыкании

                def iter_with_progress(tbl_name, batch_size=1000):
                    """Обёртка для отслеживания прогресса по записям."""
                    for batch in original_iter(tbl_name, batch_size):
                        records_processed[0] += len(batch)
                        if progress_callback:
                            progress_callback('table_update', table_name=table_name,
                                              processed=records_processed[0], total=total_records)
                        if progress_dialog and hasattr(progress_dialog, 'update_table_progress'):
                            progress_dialog.update_table_progress(records_processed[0], total_records)
                        yield batch

                # Временно подменяем метод
                self.connector.iter_records = iter_with_progress

                # Выполняем импорт
                stats, sourceid_mapping = self.engine.import_single_entity(
                    entity, ref_rules, self.instance_cache
                )

                # Восстанавливаем оригинальный метод
                self.connector.iter_records = original_iter

                # Обновляем общую статистику
                total_stats['inserted'] += stats['inserted']
                total_stats['updated'] += stats['updated']
                total_stats['errors'] += stats['errors']
                total_stats['skipped'] += stats.get('skipped', 0)

                # Сохраняем кэш сопоставлений
                self.instance_cache[table_name] = sourceid_mapping

                # Уведомляем о завершении таблицы
                if progress_callback:
                    progress_callback('table_finish', table_name=table_name,
                                      inserted=stats['inserted'], updated=stats['updated'],
                                      errors=stats['errors'], skipped=stats.get('skipped', 0))
                if progress_dialog and hasattr(progress_dialog, 'finish_table'):
                    progress_dialog.finish_table(stats['inserted'], stats['updated'],
                                                 stats['errors'], stats.get('skipped', 0))

            except Exception as e:
                self.errors.append(f"Ошибка импорта {table_name}: {str(e)}")
                total_stats['errors'] += 1
                # Восстанавливаем оригинальный метод при ошибке
                if hasattr(self.connector, 'iter_records'):
                    self.connector.iter_records = original_iter
                if progress_callback:
                    progress_callback('table_finish', table_name=table_name,
                                      inserted=0, updated=0, errors=1, skipped=0)

        # Уведомляем о завершении всего импорта
        if progress_callback:
            progress_callback('all_finish', stats=total_stats)
        if progress_dialog and hasattr(progress_dialog, 'finish_all'):
            progress_dialog.finish_all()

        return total_stats

    def get_progress(self) -> Dict[str, Any]:
        """Возвращает текущий прогресс импорта."""
        return {
            'current_table': self._current_table_index,
            'total_tables': self._total_tables,
            'errors': self.errors.copy()
        }