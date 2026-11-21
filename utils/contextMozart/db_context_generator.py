# utils/contextMozart/db_context_generator.py
# -*- coding: utf-8 -*-
"""
Генератор карты БД Mozart ERP для ИИ-контекста.

Собирает из PostgreSQL:
    - meta.entitytypes + meta.fields     — типы сущностей и их поля
    - meta.entity_classes                — классы сущностей
    - meta.composition_roles             — роли вложений
    - meta.entity_composition            — связи мастер-деталь
    - class_erp.mozartclasses + class_version — low-code классы
    - class_erp.class_property_bridge    — мосты свойств
    - meta.forms + meta.form_elements    — формы и их элементы
    - lang.translations (сводка)         — переводы

Рендерит в Mozart_db_context.md — читаемую карту БД.

Запуск:
    python utils/contextMozart/db_context_generator.py
    python utils/contextMozart/db_context_generator.py --output /path/Mozart_db_context.md
    python utils/contextMozart/db_context_generator.py --host localhost --port 5432 --db mozart_erp --user postgres --pass SQLSerIra
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_OK = True
except ImportError:
    PSYCOPG2_OK = False


# ============================================================
# КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ
# ============================================================

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output"
)
DEFAULT_OUTPUT = os.path.join(DEFAULT_OUTPUT_DIR, "Mozart_db_context.md")

DEFAULT_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "mozart_erp",
    "user": "postgres",
    "password": "",
}


# ============================================================
# ЗАГРУЗКА КОНФИГА ИЗ db.mzt
# ============================================================

def load_db_config_from_mzt(root: str) -> dict:
    """Пытается прочитать db.mzt из корня проекта."""
    candidates = [
        os.path.join(root, 'db.mzt'),
        os.path.join(root, '..', 'db.mzt'),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            db = data.get('db', {})
            return {
                'host': db.get('host', DEFAULT_DB['host']),
                'port': int(db.get('port', DEFAULT_DB['port'])),
                'dbname': db.get('name', DEFAULT_DB['dbname']),
                'user': db.get('user', DEFAULT_DB['user']),
                'password': db.get('pass', ''),
            }
        except Exception:
            continue
    return dict(DEFAULT_DB)


# ============================================================
# СБОРЩИК ДАННЫХ
# ============================================================

class DbContextCollector:
    """Собирает метаданные из PostgreSQL."""

    def __init__(self, config: dict):
        self.config = config
        self.conn = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                dbname=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                connect_timeout=5,
            )
            return True
        except Exception as e:
            print(f"[db_context] Ошибка подключения: {e}")
            return False

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def _query(self, sql: str, params=None) -> list:
        if not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                if cur.description:
                    return [dict(r) for r in cur.fetchall()]
                return []
        except Exception as e:
            print(f"[db_context] SQL Error: {e}")
            self.conn.rollback()
            return []

    # --------------------------------------------------------
    # СБОР ДАННЫХ
    # --------------------------------------------------------

    def collect_all(self) -> dict:
        return {
            'entity_classes': self._collect_entity_classes(),
            'entitytypes': self._collect_entitytypes(),
            'fields': self._collect_fields(),
            'composition_roles': self._collect_composition_roles(),
            'compositions': self._collect_compositions(),
            'mozartclasses': self._collect_mozartclasses(),
            'class_versions': self._collect_class_versions(),
            'property_bridges': self._collect_property_bridges(),
            'forms': self._collect_forms(),
            'form_elements': self._collect_form_elements(),
            'translations': self._collect_translations_summary(),
        }

    def _collect_entity_classes(self) -> list:
        return self._query("""
            SELECT id, calias, cname, mcomment
            FROM meta.entity_classes
            ORDER BY id
        """)

    def _collect_entitytypes(self) -> list:
        return self._query("""
            SELECT et.id, et.cname, et.calias, et.cbaseclass,
                   et.class_id, ec.calias AS class_alias, ec.cname AS class_name,
                   et.lisversioned, et.status_id, et.is_system, et.mcomment
            FROM meta.entitytypes et
            LEFT JOIN meta.entity_classes ec ON et.class_id = ec.id
            ORDER BY et.cname
        """)

    def _collect_fields(self) -> list:
        return self._query("""
            SELECT f.id, f.entitytypeid, f.cfieldname, f.calias,
                   f.cfieldtype, f.nlength, f.ndecimals,
                   f.lisindexed, f.lisrequired, f.isortorder,
                   f.ref_entitytypeid, f.is_system, f.status_id
            FROM meta.fields f
            ORDER BY f.entitytypeid, f.isortorder, f.id
        """)

    def _collect_composition_roles(self) -> list:
        return self._query("""
            SELECT id, calias, cname, mcomment
            FROM meta.composition_roles
            ORDER BY id
        """)

    def _collect_compositions(self) -> list:
        return self._query("""
            SELECT c.id, c.parent_entityid, c.child_entityid,
                   c.role_id, c.c_link_fieldname, c.isortorder,
                   p.cname AS parent_name, ch.cname AS child_name,
                   r.cname AS role_name
            FROM meta.entity_composition c
            LEFT JOIN meta.entitytypes p ON c.parent_entityid = p.id
            LEFT JOIN meta.entitytypes ch ON c.child_entityid = ch.id
            LEFT JOIN meta.composition_roles r ON c.role_id = r.id
            ORDER BY c.id
        """)

    def _collect_mozartclasses(self) -> list:
        return self._query("""
            SELECT id, c_name, category_id, is_class,
                   owner_class_id, dt_start, dt_end
            FROM class_erp.mozartclasses
            WHERE dt_end IS NULL
            ORDER BY c_name
        """)

    def _collect_class_versions(self) -> list:
        return self._query("""
            SELECT cv.id, cv.id_mozart_class, mc.c_name AS class_name,
                   cv.c_base_class, cv.c_base_source,
                   cv.i_base_class, cv.c_execution_env, cv.is_preload,
                   cv.status_id, cv.is_visible,
                   cv.donor_object_id, cv.first_ancestor_class_id,
                   cv.c_base_library,
                   cv.txt_properties
            FROM class_erp.class_version cv
            LEFT JOIN class_erp.mozartclasses mc ON cv.id_mozart_class = mc.id
            WHERE cv.dt_end IS NULL
            ORDER BY mc.c_name
        """)

    def _collect_property_bridges(self) -> list:
        return self._query("""
            SELECT id, c_base_class, property_key, ui_label_ru,
                   editor_type, qt_target, translation_strategy,
                   isdefaultepr
            FROM class_erp.class_property_bridge
            ORDER BY c_base_class, property_key
        """)

    def _collect_forms(self) -> list:
        return self._query("""
            SELECT f.id, f.cname, f.calias, f.ientitytypeid,
                   et.cname AS entity_name
            FROM meta.forms f
            LEFT JOIN meta.entitytypes et ON f.ientitytypeid = et.id
            ORDER BY f.cname
        """)

    def _collect_form_elements(self) -> list:
        return self._query("""
            SELECT fe.id, fe.formid, fe.parentid, fe.calias,
                   fe.cclass, fe.cdatasource, fe.isortorder, fe.lisactive
            FROM meta.form_elements fe
            ORDER BY fe.formid, fe.isortorder, fe.id
        """)

    def _collect_translations_summary(self) -> list:
        """Сводка по ключам переводов: сколько языков, какие."""
        return self._query("""
            SELECT label_key,
                   COUNT(*) AS lang_count,
                   array_agg(language ORDER BY language) AS languages
            FROM lang.translations
            GROUP BY label_key
            ORDER BY label_key
        """)


# ============================================================
# РЕНДЕРЕР MARKDOWN
# ============================================================

class DbMarkdownRenderer:
    """Рендерит карту БД в .md."""

    def __init__(self, config: dict, data: dict):
        self.config = config
        self.data = data

    def render(self) -> str:
        lines = []
        lines.append(self._header())
        lines.append(self._stats())
        lines.append(self._entity_classes())
        lines.append(self._entitytypes())
        lines.append(self._fields())
        lines.append(self._composition_roles())
        lines.append(self._compositions())
        lines.append(self._mozartclasses())
        lines.append(self._class_versions())
        lines.append(self._property_bridges())
        lines.append(self._forms())
        lines.append(self._form_elements())
        lines.append(self._translations())
        lines.append(self._footer())
        return '\n'.join(lines)

    def _header(self) -> str:
        return (
            f"# Карта БД Mozart ERP\n\n"
            f"- **Хост:** `{self.config['host']}:{self.config['port']}`\n"
            f"- **БД:** `{self.config['dbname']}`\n"
            f"- **Сгенерирован:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    def _stats(self) -> str:
        d = self.data
        return (
            "\n## Сводная статистика\n\n"
            f"| Показатель | Значение |\n"
            f"|------------|----------|\n"
            f"| Классы сущностей | {len(d['entity_classes'])} |\n"
            f"| Типы сущностей | {len(d['entitytypes'])} |\n"
            f"| Поля | {len(d['fields'])} |\n"
            f"| Роли вложений | {len(d['composition_roles'])} |\n"
            f"| Связи мастер-деталь | {len(d['compositions'])} |\n"
            f"| Low-code классы | {len(d['mozartclasses'])} |\n"
            f"| Версии классов | {len(d['class_versions'])} |\n"
            f"| Мосты свойств | {len(d['property_bridges'])} |\n"
            f"| Формы | {len(d['forms'])} |\n"
            f"| Элементы форм | {len(d['form_elements'])} |\n"
            f"| Ключей переводов | {len(d['translations'])} |\n"
        )

    def _entity_classes(self) -> str:
        rows = self.data['entity_classes']
        lines = ["\n## Классы сущностей (`meta.entity_classes`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Alias | Название | Описание |")
        lines.append("|----|-------|----------|----------|")
        for r in rows:
            desc = (r.get('mcomment') or '').replace('|', '\\|')
            lines.append(
                f"| {r['id']} | `{r['calias']}` | {r['cname']} | {desc} |"
            )
        return '\n'.join(lines)

    def _entitytypes(self) -> str:
        rows = self.data['entitytypes']
        lines = ["\n## Типы сущностей (`meta.entitytypes`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Alias | Название | Базовый класс | Класс | Версионная | Системная |")
        lines.append("|----|-------|----------|---------------|-------|------------|-----------|")
        for r in rows:
            cls_name = r.get('class_name') or '—'
            versioned = '✅' if r.get('lisversioned') else ''
            system = '✅' if r.get('is_system') else ''
            lines.append(
                f"| {r['id']} | `{r['calias']}` | {r['cname']} | "
                f"{r.get('cbaseclass') or '—'} | {cls_name} | {versioned} | {system} |"
            )
        return '\n'.join(lines)

    def _fields(self) -> str:
        rows = self.data['fields']
        lines = ["\n## Поля сущностей (`meta.fields`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])

        # Группируем по entitytypeid
        by_entity = {}
        for f in rows:
            by_entity.setdefault(f['entitytypeid'], []).append(f)

        # Индекс имён сущностей
        et_names = {r['id']: r['cname'] for r in self.data['entitytypes']}

        for eid, fields in by_entity.items():
            et_name = et_names.get(eid, f"entitytypeid={eid}")
            lines.append(f"\n### {et_name} (id={eid})\n")
            lines.append("| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |")
            lines.append("|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|")
            for f in fields:
                idx = '✅' if f.get('lisindexed') else ''
                req = '✅' if f.get('lisrequired') else ''
                sys = '✅' if f.get('is_system') else ''
                ref = f.get('ref_entitytypeid') or ''
                lines.append(
                    f"| {f['id']} | `{f['cfieldname']}` | {f.get('calias') or ''} | "
                    f"{f['cfieldtype']} | {f.get('nlength') or ''} | "
                    f"{f.get('ndecimals') or ''} | {idx} | {req} | {ref} | {sys} |"
                )
        return '\n'.join(lines)

    def _composition_roles(self) -> str:
        rows = self.data['composition_roles']
        lines = ["\n## Роли вложений (`meta.composition_roles`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Alias | Название | Описание |")
        lines.append("|----|-------|----------|----------|")
        for r in rows:
            desc = (r.get('mcomment') or '').replace('|', '\\|')
            lines.append(
                f"| {r['id']} | `{r['calias']}` | {r['cname']} | {desc} |"
            )
        return '\n'.join(lines)

    def _compositions(self) -> str:
        rows = self.data['compositions']
        lines = ["\n## Связи мастер-деталь (`meta.entity_composition`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Мастер | Деталь | Роль | Поле связи | Порядок |")
        lines.append("|----|--------|--------|------|------------|---------|")
        for r in rows:
            lines.append(
                f"| {r['id']} | {r.get('parent_name') or r['parent_entityid']} | "
                f"{r.get('child_name') or r['child_entityid']} | "
                f"{r.get('role_name') or r['role_id']} | "
                f"`{r.get('c_link_fieldname') or ''}` | {r.get('isortorder') or ''} |"
            )
        return '\n'.join(lines)

    def _mozartclasses(self) -> str:
        rows = self.data['mozartclasses']
        lines = ["\n## Low-code классы (`class_erp.mozartclasses`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Имя | Категория | Класс | Владелец |")
        lines.append("|----|-----|-----------|-------|----------|")
        for r in rows:
            is_class = '✅' if r.get('is_class') else 'подобъект'
            owner = r.get('owner_class_id') or ''
            lines.append(
                f"| {r['id']} | `{r['c_name']}` | {r.get('category_id') or ''} | "
                f"{is_class} | {owner} |"
            )
        return '\n'.join(lines)

    def _class_versions(self) -> str:
        rows = self.data['class_versions']
        lines = ["\n## Версии low-code классов (`class_erp.class_version`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Класс | Базовый Qt | Источник | Env | Preload | Статус | Видимый | Библиотека |")
        lines.append("|----|-------|------------|----------|-----|---------|--------|---------|------------|")
        for r in rows:
            preload = '⚡' if r.get('is_preload') else ''
            visible = '👁️' if r.get('is_visible') else ''
            lib = r.get('c_base_library') or ''
            lines.append(
                f"| {r['id']} | `{r.get('class_name') or ''}` | "
                f"`{r.get('c_base_class') or ''}` | {r.get('c_base_source') or ''} | "
                f"{r.get('c_execution_env') or ''} | {preload} | "
                f"{r.get('status_id') or ''} | {visible} | {lib} |"
            )
        return '\n'.join(lines)

    def _property_bridges(self) -> str:
        rows = self.data['property_bridges']
        lines = ["\n## Мосты свойств (`class_erp.class_property_bridge`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])

        # Группируем по c_base_class
        by_class = {}
        for r in rows:
            by_class.setdefault(r['c_base_class'], []).append(r)

        for base_class, props in sorted(by_class.items()):
            lines.append(f"\n### `{base_class}` ({len(props)} свойств)\n")
            lines.append("| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |")
            lines.append("|----|------|----------|----------|-----------|-----------|------------|")
            for r in props:
                default = '✅' if r.get('isdefaultepr') else ''
                lines.append(
                    f"| {r['id']} | `{r['property_key']}` | {r.get('ui_label_ru') or ''} | "
                    f"{r.get('editor_type') or ''} | {r.get('qt_target') or ''} | "
                    f"{r.get('translation_strategy') or ''} | {default} |"
                )
        return '\n'.join(lines)

    def _forms(self) -> str:
        rows = self.data['forms']
        lines = ["\n## Формы (`meta.forms`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append("| ID | Alias | Название | Сущность |")
        lines.append("|----|-------|----------|----------|")
        for r in rows:
            lines.append(
                f"| {r['id']} | `{r.get('calias') or ''}` | {r.get('cname') or ''} | "
                f"{r.get('entity_name') or ''} |"
            )
        return '\n'.join(lines)

    def _form_elements(self) -> str:
        rows = self.data['form_elements']
        lines = ["\n## Элементы форм (`meta.form_elements`)\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])

        by_form = {}
        for r in rows:
            by_form.setdefault(r['formid'], []).append(r)

        form_names = {r['id']: r.get('cname') or f"form_{r['id']}" for r in self.data['forms']}

        for fid, elems in by_form.items():
            fname = form_names.get(fid, f"formid={fid}")
            lines.append(f"\n### {fname} (id={fid}, {len(elems)} элементов)\n")
            lines.append("| ID | Parent | Alias | Класс | Источник | Порядок | Активен |")
            lines.append("|----|--------|-------|-------|----------|---------|---------|")
            for e in elems:
                active = '✅' if e.get('lisactive') else ''
                lines.append(
                    f"| {e['id']} | {e.get('parentid') or ''} | `{e.get('calias') or ''}` | "
                    f"{e.get('cclass') or ''} | {e.get('cdatasource') or ''} | "
                    f"{e.get('isortorder') or ''} | {active} |"
                )
        return '\n'.join(lines)

    def _translations(self) -> str:
        rows = self.data['translations']
        lines = ["\n## Переводы (`lang.translations`) — сводка по ключам\n"]
        if not rows:
            return '\n'.join(lines + ["_Нет данных._\n"])
        lines.append(f"Всего ключей: **{len(rows)}**\n")
        lines.append("| Ключ | Языков | Языки |")
        lines.append("|------|--------|-------|")
        for r in rows[:200]:
            langs = ', '.join(r.get('languages') or [])
            lines.append(f"| `{r['label_key']}` | {r['lang_count']} | {langs} |")
        if len(rows) > 200:
            lines.append(f"\n_… и ещё {len(rows) - 200} ключей._")
        return '\n'.join(lines)

    def _footer(self) -> str:
        return (
            "\n---\n\n"
            "_Конец карты БД. Для получения деталей по конкретной таблице — "
            "запросите SQL-дамп или конкретные строки._\n"
        )


# ============================================================
# CLI
# ============================================================

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Генератор карты БД Mozart ERP для ИИ-контекста.",
    )
    parser.add_argument('--root', default="/home/sergey/Documents/configurate",
                        help='Корень проекта (для поиска db.mzt)')
    parser.add_argument('--output', default=DEFAULT_OUTPUT,
                        help='Путь к выходному .md файлу')
    parser.add_argument('--host', default=None)
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--db', default=None, dest='dbname')
    parser.add_argument('--user', default=None)
    parser.add_argument('--pass', default=None, dest='password')
    args = parser.parse_args(argv)

    if not PSYCOPG2_OK:
        print("[db_context] ❌ psycopg2 не установлен. Установите: pip install psycopg2-binary")
        return 2

    # Конфиг: CLI > db.mzt > DEFAULT
    config = load_db_config_from_mzt(args.root)
    if args.host:
        config['host'] = args.host
    if args.port:
        config['port'] = args.port
    if args.dbname:
        config['dbname'] = args.dbname
    if args.user:
        config['user'] = args.user
    if args.password is not None:
        config['password'] = args.password

    print(f"[db_context] Подключение к {config['host']}:{config['port']}/{config['dbname']}...")
    collector = DbContextCollector(config)
    if not collector.connect():
        return 1

    try:
        print("[db_context] Сбор данных...")
        data = collector.collect_all()

        print("[db_context] Рендеринг Markdown...")
        renderer = DbMarkdownRenderer(config, data)
        md = renderer.render()

        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(md)

        size = os.path.getsize(args.output)
        print(f"[db_context] ✅ {args.output} ({size / 1024:.1f} KB)")

        return 0
    finally:
        collector.close()


if __name__ == '__main__':
    sys.exit(main())