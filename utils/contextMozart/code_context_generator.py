# utils/contextMozart/code_context_generator.py
# -*- coding: utf-8 -*-
"""
Генератор карты Python-проекта для ИИ-контекста.

Назначение:
    Обходит дерево проекта, парсит каждый .py файл через ast,
    собирает классы, функции, методы, сигналы, свойства, импорты,
    строит обратные связи и генерирует два файла:
      - Mozart_context.md   — читаемая карта (для ИИ)
      - Mozart_context.json — машинная карта (для автоматизации)

Запуск:
    python -m utils.contextMozart.code_context_generator
    python utils/contextMozart/code_context_generator.py --root /path --output /path
    python utils/contextMozart/code_context_generator.py --files a.py b.py
"""

import ast
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Any, Optional


# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

DEFAULT_EXCLUDE = {
    '.venv', 'venv', 'env', '.env',
    '__pycache__', '.git', '.svn', '.hg',
    '.idea', '.vscode', 'node_modules',
    'build', 'dist', '.pytest_cache', '.mypy_cache', '.tox',
    'backups', 'music_pool', 'forms', 'output',
    'utils/analitik_mozart',   # отдельный подпроект
    'lang_data',
}

DEFAULT_ROOT = "/home/sergey/Documents/configurate"
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output"
)


class ContextConfig:
    """Настройки генератора."""

    def __init__(self, root: str, output_dir: str,
                 exclude: Optional[set] = None,
                 include_analitik: bool = False,
                 max_value_len: int = 50,
                 only_files: Optional[list] = None):
        self.root = os.path.abspath(root)
        self.output_dir = os.path.abspath(output_dir)
        self.exclude = set(exclude or DEFAULT_EXCLUDE)

        if not include_analitik:
            self.exclude.add('utils/analitik_mozart')

        self.max_value_len = max_value_len

        # Список абсолютных путей .py-файлов; если задан — сканируются только они
        self.only_files = (
            [os.path.abspath(p) for p in only_files]
            if only_files else None
        )

    def is_excluded(self, rel_path: str) -> bool:
        """Проверяет, входит ли путь в список исключений."""
        rel_norm = rel_path.replace(os.sep, '/')
        for ex in self.exclude:
            if rel_norm == ex or rel_norm.startswith(ex + '/'):
                return True
            if any(part == ex for part in rel_norm.split('/')):
                return True
        return False


# ============================================================
# СКАНЕР ФАЙЛОВ
# ============================================================

class FileScanner:
    """Обходит дерево проекта и собирает .py файлы."""

    def __init__(self, config: ContextConfig):
        self.config = config

    def scan(self) -> list:
        # Режим "только выбранные файлы"
        if self.config.only_files is not None:
            result = []
            for full in self.config.only_files:
                if not os.path.isfile(full) or not full.endswith('.py'):
                    continue
                try:
                    rel = os.path.relpath(full, self.config.root).replace(os.sep, '/')
                except ValueError:
                    rel = full.replace(os.sep, '/')
                if self.config.is_excluded(rel):
                    continue
                result.append(rel)
            result.sort()
            return result

        # Режим "весь проект"
        result = []
        for dirpath, dirnames, filenames in os.walk(self.config.root):
            rel_dir = os.path.relpath(dirpath, self.config.root)
            if rel_dir == '.':
                rel_dir = ''

            dirnames[:] = [
                d for d in dirnames
                if not self.config.is_excluded(
                    (rel_dir + '/' + d).lstrip('/')
                )
            ]

            for fname in filenames:
                if not fname.endswith('.py'):
                    continue
                rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
                rel_path = rel_path.replace(os.sep, '/')
                if self.config.is_excluded(rel_path):
                    continue
                result.append(rel_path)

        result.sort()
        return result


# ============================================================
# ПАРСЕР PYTHON-ФАЙЛА
# ============================================================

class PythonFileParser:
    """Парсит один .py файл через ast."""

    def __init__(self, config: ContextConfig):
        self.config = config

    def parse(self, rel_path: str) -> dict:
        """Парсит файл и возвращает словарь-карточку."""
        full_path = os.path.join(self.config.root, rel_path)

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except UnicodeDecodeError:
            try:
                with open(full_path, 'r', encoding='cp1251') as f:
                    source = f.read()
            except Exception as e:
                return self._error_card(rel_path, f"Ошибка кодировки: {e}")
        except Exception as e:
            return self._error_card(rel_path, f"Ошибка чтения: {e}")

        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as e:
            return self._error_card(rel_path, f"Ошибка синтаксиса (строка {e.lineno}): {e.msg}")

        card = {
            'path': rel_path,
            'role': self._get_module_role(tree),
            'lines': len(source.splitlines()),
            'classes': [],
            'functions': [],
            'globals': [],
            'imports': [],
            'error': None,
        }

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                card['classes'].append(self._parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                card['functions'].append(self._parse_function(node))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    card['imports'].append({'type': 'import', 'name': alias.name})
            elif isinstance(node, ast.ImportFrom):
                card['imports'].append({
                    'type': 'from',
                    'module': node.module or '',
                    'names': [a.name for a in node.names],
                })
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        val = self._get_short_value(node.value)
                        card['globals'].append({'name': target.id, 'value': val})
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    name = node.target.id
                    if name.isupper() or name.startswith('DEFAULT_'):
                        val = self._get_short_value(node.value)
                        card['globals'].append({'name': name, 'value': val})

        return card

    def _error_card(self, rel_path: str, error: str) -> dict:
        return {
            'path': rel_path, 'role': '', 'lines': 0,
            'classes': [], 'functions': [], 'globals': [],
            'imports': [], 'error': error,
        }

    def _get_module_role(self, tree: ast.Module) -> str:
        """Извлекает docstring модуля как «роль»."""
        doc = ast.get_docstring(tree)
        if not doc:
            return ''
        for line in doc.strip().splitlines():
            line = line.strip()
            if line:
                return line
        return ''

    def _get_short_value(self, node: Optional[ast.AST]) -> str:
        """Возвращает строковое представление значения (обрезанное)."""
        if node is None:
            return ''
        try:
            if isinstance(node, ast.Constant):
                val = repr(node.value)
            elif isinstance(node, ast.List):
                val = f"list[{len(node.elts)}]"
            elif isinstance(node, ast.Dict):
                val = f"dict[{len(node.keys)}]"
            elif isinstance(node, ast.Set):
                val = f"set[{len(node.elts)}]"
            elif isinstance(node, ast.Tuple):
                val = f"tuple[{len(node.elts)}]"
            elif isinstance(node, ast.Call):
                val = f"call({self._get_call_name(node)})"
            else:
                val = type(node).__name__
        except Exception:
            return '?'

        if len(val) > self.config.max_value_len:
            val = val[:self.config.max_value_len] + '…'
        return val

    def _get_call_name(self, node: ast.Call) -> str:
        """Извлекает имя вызываемой функции."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return '?'

    # --------------------------------------------------------
    # ПАРСИНГ КЛАССА
    # --------------------------------------------------------

    def _parse_class(self, node: ast.ClassDef) -> dict:
        bases = [self._get_base_name(b) for b in node.bases]
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        methods = []
        properties = []
        signals = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decos = [self._get_decorator_name(d) for d in item.decorator_list]
                if 'property' in decos:
                    properties.append(self._parse_property(item, decos))
                else:
                    methods.append(self._parse_method(item, decos))
            elif isinstance(item, ast.Assign):
                # Сигналы PySide: value_changed = Signal(...)
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(item.value, ast.Call):
                            call_name = self._get_call_name(item.value)
                            if call_name == 'Signal':
                                signals.append(target.id)

        return {
            'name': node.name,
            'bases': bases,
            'decorators': decorators,
            'docstring': self._short_doc(ast.get_docstring(node)),
            'methods': methods,
            'properties': properties,
            'signals': signals,
            'is_big': len(methods) > 15,
        }

    def _parse_method(self, node: ast.FunctionDef, decorators: list) -> dict:
        method_type = 'instance'
        if 'classmethod' in decorators:
            method_type = 'classmethod'
        elif 'staticmethod' in decorators:
            method_type = 'staticmethod'
        elif isinstance(node, ast.AsyncFunctionDef):
            method_type = 'async'

        return {
            'name': node.name,
            'params': self._parse_params(node.args),
            'returns': self._get_annotation(node.returns),
            'decorators': [d for d in decorators
                           if d not in ('property', 'classmethod', 'staticmethod')],
            'method_type': method_type,
            'docstring': self._short_doc(ast.get_docstring(node)),
            'is_private': node.name.startswith('_') and not node.name.startswith('__'),
        }

    def _parse_property(self, node: ast.FunctionDef, decorators: list) -> dict:
        return {
            'name': node.name,
            'returns': self._get_annotation(node.returns),
            'docstring': self._short_doc(ast.get_docstring(node)),
            'is_readonly': True,
        }

    def _parse_params(self, args: ast.arguments) -> list:
        """Парсит параметры функции/метода."""
        result = []

        defaults = args.defaults
        num_args = len(args.args)
        default_offset = num_args - len(defaults)

        for i, arg in enumerate(args.args):
            if arg.arg in ('self', 'cls'):
                continue
            param = {
                'name': arg.arg,
                'type': self._get_annotation(arg.annotation),
                'default': None,
            }
            if i >= default_offset:
                d_idx = i - default_offset
                param['default'] = self._get_short_value(defaults[d_idx])
            result.append(param)

        if args.vararg:
            result.append({
                'name': '*' + args.vararg.arg,
                'type': 'tuple',
                'default': None,
            })
        if args.kwarg:
            result.append({
                'name': '**' + args.kwarg.arg,
                'type': 'dict',
                'default': None,
            })

        return result

    def _get_base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._get_base_name(node.value) + '.' + node.attr
        if isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return '?'

    def _get_decorator_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return '?'

    def _get_annotation(self, node: Optional[ast.AST]) -> str:
        """Строковое представление аннотации типа."""
        if node is None:
            return ''
        try:
            return ast.unparse(node)
        except Exception:
            return '?'

    def _short_doc(self, doc: Optional[str]) -> str:
        """Первая строка docstring."""
        if not doc:
            return ''
        for line in doc.strip().splitlines():
            line = line.strip()
            if line:
                return line
        return ''

    # --------------------------------------------------------
    # ПАРСИНГ ФУНКЦИИ (модульного уровня)
    # --------------------------------------------------------

    def _parse_function(self, node: ast.FunctionDef) -> dict:
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        is_async = isinstance(node, ast.AsyncFunctionDef)
        return {
            'name': node.name,
            'params': self._parse_params(node.args),
            'returns': self._get_annotation(node.returns),
            'decorators': decorators,
            'docstring': self._short_doc(ast.get_docstring(node)),
            'is_async': is_async,
        }


# ============================================================
# ЛИНКЕР ОБРАТНЫХ СВЯЗЕЙ
# ============================================================

class ReferenceLinker:
    """Строит обратные связи: кто импортирует, кто наследует."""

    def __init__(self, config: ContextConfig, cards: list):
        self.config = config
        self.cards = cards
        self.by_path = {c['path']: c for c in cards}
        self.by_module = {}       # module_name -> path
        self.by_class = {}        # class_name -> [(path, cls_dict)]
        self.importers = {}       # path -> set(path) — кто импортирует
        self.subclasses = {}      # class_name -> set((path, class_name))

        self._build_index()

    def _build_index(self):
        for card in self.cards:
            for cls in card['classes']:
                self.by_class.setdefault(cls['name'], []).append((card['path'], cls))

        for card in self.cards:
            mod = card['path'][:-3].replace('/', '.')
            self.by_module[mod] = card['path']
            short = card['path'][:-3].split('/')[-1]
            self.by_module.setdefault(short, card['path'])

    def link(self):
        """Заполняет importers и subclasses."""
        for card in self.cards:
            for imp in card['imports']:
                if imp['type'] == 'from':
                    target_path = self.by_module.get(imp['module'])
                    if target_path:
                        self.importers.setdefault(target_path, set()).add(card['path'])
                elif imp['type'] == 'import':
                    target_path = self.by_module.get(imp['name'])
                    if target_path:
                        self.importers.setdefault(target_path, set()).add(card['path'])

            for cls in card['classes']:
                for base in cls['bases']:
                    base_short = base.split('.')[-1]
                    if base_short in self.by_class:
                        for (base_path, _) in self.by_class[base_short]:
                            self.subclasses.setdefault(base_short, set()).add(
                                (card['path'], cls['name'])
                            )

    def get_importers(self, path: str) -> list:
        return sorted(self.importers.get(path, set()))

    def get_subclasses(self, class_name: str) -> list:
        return sorted(self.subclasses.get(class_name, set()))


# ============================================================
# РЕНДЕРЕР MARKDOWN
# ============================================================

class MarkdownRenderer:
    """Рендерит карту проекта в .md."""

    def __init__(self, config: ContextConfig, cards: list, linker: ReferenceLinker):
        self.config = config
        self.cards = cards
        self.linker = linker

    def render(self) -> str:
        lines = []
        lines.append(self._header())
        lines.append(self._stats())
        lines.append(self._toc())
        lines.append(self._file_table())
        lines.append(self._detailed_cards())
        lines.append(self._footer())
        return '\n'.join(lines)

    def _header(self) -> str:
        return (
            f"# Контекст проекта Mozart ERP\n\n"
            f"- **Корень:** `{self.config.root}`\n"
            f"- **Сгенерирован:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **Файлов:** {len(self.cards)}\n"
        )

    def _stats(self) -> str:
        total_classes = sum(len(c['classes']) for c in self.cards)
        total_methods = sum(
            len(cls['methods']) + len(cls['properties'])
            for c in self.cards for cls in c['classes']
        )
        total_functions = sum(len(c['functions']) for c in self.cards)
        total_lines = sum(c['lines'] for c in self.cards)

        return (
            "\n## Сводная статистика\n\n"
            f"| Показатель | Значение |\n"
            f"|------------|----------|\n"
            f"| Файлов | {len(self.cards)} |\n"
            f"| Классов | {total_classes} |\n"
            f"| Методов/свойств | {total_methods} |\n"
            f"| Функций | {total_functions} |\n"
            f"| Строк кода | {total_lines:,} |\n"
        )

    def _toc(self) -> str:
        lines = ["\n## Оглавление\n"]
        for card in self.cards:
            anchor = self._anchor(card['path'])
            role = card['role'] or '—'
            lines.append(f"- [`{card['path']}`](#{anchor}) — {role}")
        return '\n'.join(lines)

    def _file_table(self) -> str:
        lines = [
            "\n## Сводная таблица файлов\n",
            "| Файл | Строк | Классов | Функций | Роль |",
            "|------|-------|---------|---------|------|",
        ]
        for card in self.cards:
            role = (card['role'] or '—').replace('|', '\\|')
            if len(role) > 80:
                role = role[:77] + '…'
            lines.append(
                f"| `{card['path']}` | {card['lines']} | "
                f"{len(card['classes'])} | {len(card['functions'])} | {role} |"
            )
        return '\n'.join(lines)

    def _detailed_cards(self) -> str:
        lines = ["\n---\n\n## Детальные карточки файлов\n"]
        for card in self.cards:
            lines.append(self._render_card(card))
        return '\n'.join(lines)

    def _render_card(self, card: dict) -> str:
        lines = []
        anchor = self._anchor(card['path'])
        lines.append(f"\n### <a id=\"{anchor}\"></a>`{card['path']}`\n")

        if card.get('error'):
            lines.append(f"> ⚠️ **Ошибка:** {card['error']}\n")
            return '\n'.join(lines)

        if card['role']:
            lines.append(f"**Роль:** {card['role']}")
        lines.append(f"**Строк:** {card['lines']}")

        if card['imports']:
            imp_strs = []
            for imp in card['imports']:
                if imp['type'] == 'from':
                    names = ', '.join(imp['names'][:5])
                    if len(imp['names']) > 5:
                        names += f" (+{len(imp['names']) - 5})"
                    imp_strs.append(f"from `{imp['module']}` import {names}")
                else:
                    imp_strs.append(f"import `{imp['name']}`")
            lines.append("**Импорты:** " + "; ".join(imp_strs[:10]))
            if len(imp_strs) > 10:
                lines.append(f"  _… и ещё {len(imp_strs) - 10}_")

        importers = self.linker.get_importers(card['path'])
        if importers:
            lines.append("**Импортируется в:** " +
                         ", ".join(f"`{p}`" for p in importers[:5]))
            if len(importers) > 5:
                lines.append(f"  _… и ещё {len(importers) - 5}_")

        if card['globals']:
            g_strs = [f"`{g['name']}`" + (f" = {g['value']}" if g['value'] else '')
                      for g in card['globals']]
            lines.append("**Глобальные константы:** " + ", ".join(g_strs))

        if card['classes']:
            lines.append("\n**Классы:**\n")
            for cls in card['classes']:
                lines.append(self._render_class(cls))

        if card['functions']:
            lines.append("\n**Функции модуля:**\n")
            for fn in card['functions']:
                lines.append(self._render_function(fn))

        lines.append("")
        return '\n'.join(lines)

    def _render_class(self, cls: dict) -> str:
        lines = []
        flag = " ⚠️ _большой класс_" if cls.get('is_big') else ''
        bases = f" ({', '.join(cls['bases'])})" if cls['bases'] else ''
        lines.append(f"- **`class {cls['name']}`**{bases}{flag}")
        if cls['docstring']:
            lines.append(f"  - _{cls['docstring']}_")

        subs = self.linker.get_subclasses(cls['name'])
        if subs:
            subs_str = ", ".join(f"`{p.split('/')[-1]}::{n}`" for p, n in subs[:5])
            lines.append(f"  - **Наследники:** {subs_str}")
            if len(subs) > 5:
                lines.append(f"    _… и ещё {len(subs) - 5}_")

        if cls['signals']:
            lines.append("  - **Сигналы:** " +
                         ", ".join(f"`{s}`" for s in cls['signals']))

        if cls['properties']:
            lines.append("  - **Свойства (@property):**")
            for prop in cls['properties']:
                ret = f" -> `{prop['returns']}`" if prop['returns'] else ''
                doc = f" — {prop['docstring']}" if prop['docstring'] else ''
                lines.append(f"    - `{prop['name']}`{ret}{doc}")

        public = [m for m in cls['methods'] if not m.get('is_private')]
        private = [m for m in cls['methods'] if m.get('is_private')]

        if public:
            lines.append("  - **Методы:**")
            for m in public:
                lines.append("    - " + self._render_method_line(m))

        if private:
            lines.append(f"  - **Приватные методы:** ({len(private)} шт.)")
            for m in private:
                doc = f" — {m['docstring']}" if m['docstring'] else ''
                lines.append(f"    - `{m['name']}()`{doc}")

        return '\n'.join(lines)

    def _render_method_line(self, m: dict) -> str:
        params = self._params_str(m['params'])
        ret = f" -> `{m['returns']}`" if m['returns'] else ''
        mt = m.get('method_type', 'instance')
        prefix = {
            'classmethod': '[class] ',
            'staticmethod': '[static] ',
            'async': '[async] ',
        }.get(mt, '')
        doc = f" — {m['docstring']}" if m['docstring'] else ''
        return f"`{prefix}{m['name']}({params})`{ret}{doc}"

    def _render_function(self, fn: dict) -> str:
        params = self._params_str(fn['params'])
        ret = f" -> `{fn['returns']}`" if fn['returns'] else ''
        prefix = '[async] ' if fn.get('is_async') else ''
        doc = f" — {fn['docstring']}" if fn['docstring'] else ''
        return f"- `{prefix}{fn['name']}({params})`{ret}{doc}"

    def _params_str(self, params: list) -> str:
        parts = []
        for p in params:
            s = p['name']
            if p.get('type'):
                s += f": {p['type']}"
            if p.get('default') is not None:
                s += f" = {p['default']}"
            parts.append(s)
        return ', '.join(parts)

    def _anchor(self, path: str) -> str:
        return (path.replace('/', '-')
                    .replace('.', '-')
                    .replace('_', '-')
                    .lower())

    def _footer(self) -> str:
        return (
            "\n---\n\n"
            "_Конец карты проекта. Для получения деталей по конкретному файлу — "
            "запросите его полный исходник._\n"
        )


# ============================================================
# РЕНДЕРЕР JSON
# ============================================================

class JsonRenderer:
    """Рендерит карту проекта в .json (машинный формат)."""

    def __init__(self, config: ContextConfig, cards: list, linker: ReferenceLinker):
        self.config = config
        self.cards = cards
        self.linker = linker

    def render(self) -> dict:
        files = []
        for card in self.cards:
            fc = dict(card)
            fc['imported_by'] = self.linker.get_importers(card['path'])
            classes = []
            for cls in card['classes']:
                cc = dict(cls)
                cc['subclasses'] = [
                    {'path': p, 'class': n}
                    for p, n in self.linker.get_subclasses(cls['name'])
                ]
                classes.append(cc)
            fc['classes'] = classes
            files.append(fc)

        return {
            'project': {
                'root': self.config.root,
                'generated_at': datetime.now().isoformat(),
                'total_files': len(self.cards),
                'total_lines': sum(c['lines'] for c in self.cards),
            },
            'files': files,
        }


# ============================================================
# CLI
# ============================================================

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Генератор карты Python-проекта для ИИ-контекста.",
    )
    parser.add_argument('--root', default=DEFAULT_ROOT, help='Корень проекта')
    parser.add_argument('--output', default=DEFAULT_OUTPUT_DIR,
                        help='Каталог для выходных файлов')
    parser.add_argument('--include-analitik', action='store_true',
                        help='Включить utils/analitik_mozart в сканирование')
    parser.add_argument('--exclude', action='append', default=[],
                        help='Дополнительные исключения (можно несколько раз)')
    parser.add_argument('--files', action='append', default=[],
                        help='Сканировать только указанные файлы (можно несколько раз)')
    parser.add_argument('--format', choices=['md', 'json', 'both'], default='both',
                        help='Формат вывода')
    args = parser.parse_args(argv)

    exclude = set(DEFAULT_EXCLUDE) | set(args.exclude)
    config = ContextConfig(
        root=args.root,
        output_dir=args.output,
        exclude=exclude,
        include_analitik=args.include_analitik,
        only_files=args.files if args.files else None,
    )

    print(f"[contextMozart] Корень: {config.root}")
    print(f"[contextMozart] Исключено: {sorted(config.exclude)}")

    scanner = FileScanner(config)
    files = scanner.scan()
    print(f"[contextMozart] Найдено .py файлов: {len(files)}")

    parser_obj = PythonFileParser(config)
    cards = []
    errors = 0
    for i, rel in enumerate(files, 1):
        if i % 20 == 0 or i == len(files):
            print(f"[contextMozart] Парсинг {i}/{len(files)}: {rel}", end='\r')
        card = parser_obj.parse(rel)
        if card.get('error'):
            errors += 1
        cards.append(card)
    print()

    if errors:
        print(f"[contextMozart] ⚠️ Ошибок парсинга: {errors}")

    print("[contextMozart] Построение обратных связей...")
    linker = ReferenceLinker(config, cards)
    linker.link()

    os.makedirs(config.output_dir, exist_ok=True)

    if args.format in ('md', 'both'):
        md_path = os.path.join(config.output_dir, 'Mozart_context.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(MarkdownRenderer(config, cards, linker).render())
        size = os.path.getsize(md_path)
        print(f"[contextMozart] ✅ Markdown: {md_path} ({size / 1024:.1f} KB)")

    if args.format in ('json', 'both'):
        json_path = os.path.join(config.output_dir, 'Mozart_context.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(
                JsonRenderer(config, cards, linker).render(),
                f, ensure_ascii=False, indent=2
            )
        size = os.path.getsize(json_path)
        print(f"[contextMozart] ✅ JSON: {json_path} ({size / 1024:.1f} KB)")

    print("[contextMozart] Готово.")
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())