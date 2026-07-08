# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/описание.py
"""
Генератор структурированной документации проекта Mozart ERP.
Анализирует все .py файлы и создаёт детальное описание.
Поддерживает: Markdown, JSON, HTML (встроенный конвертер).
"""

import os
import re
import ast
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime


# =============================================================================
# ВСТРОЕННЫЙ КОНВЕРТЕР MARKDOWN -> HTML (без внешних зависимостей)
# =============================================================================

class SimpleMarkdownToHTML:
    """Простой конвертер Markdown в HTML без внешних зависимостей."""

    def convert(self, md_text: str) -> str:
        """Конвертирует Markdown в HTML."""
        lines = md_text.split('\n')
        html_lines = []
        in_code_block = False
        in_list = False
        in_table = False
        table_rows = []
        list_items = []

        for line in lines:
            # Кодовые блоки
            if line.startswith('```'):
                if in_code_block:
                    html_lines.append('</pre>')
                    in_code_block = False
                else:
                    html_lines.append('<pre><code>')
                    in_code_block = True
                continue

            if in_code_block:
                html_lines.append(self._escape_html(line))
                continue

            # Заголовки
            if line.startswith('# '):
                html_lines.append(f'<h1>{self._escape_html(line[2:])}</h1>')
                continue
            elif line.startswith('## '):
                html_lines.append(f'<h2>{self._escape_html(line[3:])}</h2>')
                continue
            elif line.startswith('### '):
                html_lines.append(f'<h3>{self._escape_html(line[4:])}</h3>')
                continue
            elif line.startswith('#### '):
                html_lines.append(f'<h4>{self._escape_html(line[5:])}</h4>')
                continue
            elif line.startswith('##### '):
                html_lines.append(f'<h5>{self._escape_html(line[6:])}</h5>')
                continue

            # Горизонтальная черта
            if line.strip() == '---':
                html_lines.append('<hr>')
                continue

            # Списки
            if line.strip().startswith('- '):
                if not in_list:
                    in_list = True
                    html_lines.append('<ul>')
                list_items.append(f'<li>{self._escape_html(line.strip()[2:])}</li>')
                continue
            else:
                if in_list and list_items:
                    html_lines.extend(list_items)
                    html_lines.append('</ul>')
                    list_items = []
                    in_list = False

            # Строки с обратными кавычками (инлайн код)
            if line.strip():
                line = self._escape_html(line)
                # Инлайн код: `text` -> <code>text</code>
                line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
                # Жирный текст: **text** -> <b>text</b>
                line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
                # Курсив: *text* -> <i>text</i>
                line = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', line)
                html_lines.append(line)
            else:
                html_lines.append('')

        # Закрываем незакрытые списки
        if in_list and list_items:
            html_lines.extend(list_items)
            html_lines.append('</ul>')

        return '\n'.join(html_lines)

    def _escape_html(self, text: str) -> str:
        """Экранирует HTML-спецсимволы."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))


# =============================================================================
# МОДЕЛИ ДАННЫХ ДЛЯ ДОКУМЕНТАЦИИ
# =============================================================================

@dataclass
class Parameter:
    """Параметр функции/метода."""
    name: str
    type_hint: str = "Any"
    default: Optional[str] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type_hint,
            "default": self.default,
            "description": self.description
        }


@dataclass
class FunctionDoc:
    """Документация функции."""
    name: str
    params: List[Parameter] = field(default_factory=list)
    return_type: str = "None"
    description: str = ""
    decorators: List[str] = field(default_factory=list)
    lineno: int = 0
    docstring: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "params": [p.to_dict() for p in self.params],
            "return_type": self.return_type,
            "description": self.description or self.docstring[:200] if self.docstring else "",
            "decorators": self.decorators,
            "line": self.lineno
        }


@dataclass
class ClassDoc:
    """Документация класса."""
    name: str
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionDoc] = field(default_factory=list)
    class_attrs: List[Dict] = field(default_factory=list)
    description: str = ""
    lineno: int = 0
    docstring: str = ""
    is_dataclass: bool = False
    is_mixin: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "bases": self.bases,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": self.class_attrs,
            "description": self.description or self.docstring[:200] if self.docstring else "",
            "line": self.lineno,
            "is_dataclass": self.is_dataclass,
            "is_mixin": self.is_mixin
        }


@dataclass
class ModuleDoc:
    """Документация модуля (файла)."""
    path: str
    name: str
    imports: List[str] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)
    constants: List[Dict] = field(default_factory=list)
    description: str = ""
    docstring: str = ""
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "description": self.description or self.docstring[:200] if self.docstring else "",
            "imports": self.imports,
            "dependencies": self.dependencies,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "constants": self.constants
        }


# =============================================================================
# ПАРСЕР PYTHON ФАЙЛОВ
# =============================================================================

class PythonParser:
    """Парсит Python файлы и извлекает структуру."""

    TYPE_HINT_MAP = {
        'str': 'str',
        'int': 'int',
        'float': 'float',
        'bool': 'bool',
        'list': 'List',
        'dict': 'Dict',
        'tuple': 'Tuple',
        'set': 'Set',
        'None': 'None',
        'Any': 'Any',
        'Optional': 'Optional',
        'Union': 'Union',
    }

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.modules: Dict[str, ModuleDoc] = {}
        self.IGNORE_DIRS = {
            '__pycache__', '.git', '.venv', 'venv', 'env', '.env',
            'dist', 'build', '.mypy_cache', '.pytest_cache', '.tox',
            '.ipynb_checkpoints', '.DS_Store', 'lang_data'
        }

    def parse_file(self, filepath: str) -> Optional[ModuleDoc]:
        """Парсит один Python файл."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  ⚠️ Ошибка чтения {filepath}: {e}")
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"  ⚠️ Синтаксическая ошибка в {filepath}: {e}")
            return None

        rel_path = os.path.relpath(filepath, self.project_root)

        module = ModuleDoc(
            path=rel_path,
            name=os.path.basename(filepath),
            docstring=ast.get_docstring(tree) or ""
        )

        # Парсим импорты
        module.imports = self._parse_imports(tree)

        # Парсим классы
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_doc = self._parse_class(node, content)
                if class_doc:
                    module.classes.append(class_doc)

        # Парсим функции
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_doc = self._parse_function(node)
                if func_doc:
                    module.functions.append(func_doc)

        # Определяем зависимости
        module.dependencies = self._extract_dependencies(module)

        self.modules[rel_path] = module
        return module

    def _parse_imports(self, tree: ast.AST) -> List[str]:
        """Извлекает импорты."""
        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    imports.append(full_name)
        return imports

    def _parse_class(self, node: ast.ClassDef, content: str) -> Optional[ClassDoc]:
        """Парсит класс и его методы."""
        class_doc = ClassDoc(
            name=node.name,
            lineno=node.lineno,
            docstring=ast.get_docstring(node) or "",
            bases=[self._get_base_name(b) for b in node.bases]
        )

        # Определяем, является ли класс датаклассом или миксином
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'dataclass':
                    class_doc.is_dataclass = True
                if decorator.id.endswith('Mixin') or 'Mixin' in decorator.id:
                    class_doc.is_mixin = True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'dataclass':
                    class_doc.is_dataclass = True

        # Парсим атрибуты класса
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                attr_name = self._get_attr_name(item.target)
                attr_type = self._get_type_hint(item.annotation) if item.annotation else "Any"
                class_doc.class_attrs.append({
                    "name": attr_name,
                    "type": attr_type,
                    "default": self._get_expr_value(item.value) if item.value else None
                })
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_doc.class_attrs.append({
                            "name": target.id,
                            "type": "Any",
                            "default": self._get_expr_value(item.value) if item.value else None
                        })

        # Парсим методы
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self._parse_function(item, is_method=True)
                if method:
                    class_doc.methods.append(method)

        if class_doc.docstring:
            class_doc.description = class_doc.docstring

        return class_doc

    def _parse_function(self, node: ast.FunctionDef, is_method: bool = False) -> Optional[FunctionDoc]:
        """Парсит функцию/метод."""
        func = FunctionDoc(
            name=node.name,
            lineno=node.lineno,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_decorator_name(d) for d in node.decorator_list]
        )

        # Парсим параметры
        for arg in node.args.args:
            param = Parameter(
                name=arg.arg,
                type_hint=self._get_type_hint(arg.annotation) if arg.annotation else "Any"
            )
            func.params.append(param)

        # Параметры с дефолтными значениями
        defaults = node.args.defaults
        if defaults:
            offset = len(node.args.args) - len(defaults)
            for i, default in enumerate(defaults):
                idx = offset + i
                if idx < len(func.params):
                    func.params[idx].default = self._get_expr_value(default)

        # Параметры *args и **kwargs
        if node.args.vararg:
            func.params.append(Parameter(
                name=f"*{node.args.vararg.arg}",
                type_hint="List",
                default=None
            ))
        if node.args.kwarg:
            func.params.append(Parameter(
                name=f"**{node.args.kwarg.arg}",
                type_hint="Dict",
                default=None
            ))

        # Возвращаемый тип
        if node.returns:
            func.return_type = self._get_type_hint(node.returns)

        if func.docstring:
            func.description = func.docstring

        return func

    def _get_base_name(self, node: ast.AST) -> str:
        """Получает имя базового класса."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return "object"

    def _get_type_hint(self, node: ast.AST) -> str:
        """Извлекает строковое представление типа."""
        if isinstance(node, ast.Name):
            return self.TYPE_HINT_MAP.get(node.id, node.id)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_type_hint(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            value = self._get_type_hint(node.value)
            slice_val = self._get_type_hint(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Tuple):
            elems = [self._get_type_hint(e) for e in node.elts]
            return f"Tuple[{', '.join(elems)}]"
        elif isinstance(node, ast.List):
            elems = [self._get_type_hint(e) for e in node.elts]
            return f"List[{', '.join(elems)}]"
        elif isinstance(node, ast.Index):
            return self._get_type_hint(node.value)
        return "Any"

    def _get_expr_value(self, node: ast.AST) -> Optional[str]:
        """Извлекает строковое представление значения."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            values = [self._get_expr_value(e) for e in node.elts]
            return f"[{', '.join(v for v in values if v)}]"
        elif isinstance(node, ast.Dict):
            keys = [self._get_expr_value(k) for k in node.keys]
            values = [self._get_expr_value(v) for v in node.values]
            pairs = [f"{k}: {v}" for k, v in zip(keys, values) if k]
            return f"{{{', '.join(pairs)}}}"
        elif isinstance(node, ast.Call):
            return f"{self._get_expr_value(node.func)}(...)"
        return "..."

    def _get_decorator_name(self, node: ast.AST) -> str:
        """Извлекает имя декоратора."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        return "..."

    def _get_attr_name(self, node: ast.AST) -> str:
        """Извлекает имя атрибута."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        return "..."

    def _extract_dependencies(self, module: ModuleDoc) -> List[str]:
        """Извлекает зависимости модуля."""
        deps = set()
        for imp in module.imports:
            parts = imp.split('.')
            if len(parts) >= 1:
                deps.add(parts[0])
        for cls in module.classes:
            for method in cls.methods:
                for param in method.params:
                    if param.type_hint in ('QWidget', 'QMainWindow', 'QDialog'):
                        deps.add('PySide6')
                    elif param.type_hint in ('DatabaseService',):
                        deps.add('database')
        return sorted(deps)

    def parse_project(self, root_dir: Optional[str] = None) -> Dict[str, ModuleDoc]:
        """Рекурсивно парсит все Python файлы в проекте."""
        root = root_dir or self.project_root
        if not os.path.exists(root):
            raise FileNotFoundError(f"Директория не найдена: {root}")

        print(f"🔍 Сканирование: {root}")

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in self.IGNORE_DIRS]

            for filename in filenames:
                if filename.endswith('.py'):
                    filepath = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(filepath, root)
                    print(f"  📄 {rel_path}")
                    self.parse_file(filepath)

        return self.modules


# =============================================================================
# ГЕНЕРАТОР ДОКУМЕНТАЦИИ
# =============================================================================

class DocumentationGenerator:
    """Генерирует структурированную документацию в разных форматах."""

    def __init__(self, modules: Dict[str, ModuleDoc], project_root: str):
        self.modules = modules
        self.project_root = project_root
        self.md_converter = SimpleMarkdownToHTML()

    def generate_markdown(self, output_file: str) -> None:
        """Генерирует единый Markdown-файл с полной документацией."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 🎵 Mozart ERP — Документация проекта\n\n")
            f.write(f"*Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"*Всего файлов: {len(self.modules)}*\n\n")

            # Оглавление
            f.write("## 📑 Содержание\n\n")
            modules_by_dir = {}
            for path, module in self.modules.items():
                dirname = os.path.dirname(path)
                if dirname not in modules_by_dir:
                    modules_by_dir[dirname] = []
                modules_by_dir[dirname].append((path, module))

            for dirname in sorted(modules_by_dir.keys()):
                display_dir = dirname or "Корень проекта"
                f.write(f"- [{display_dir}](#{self._slug(display_dir)})\n")
                for path, module in sorted(modules_by_dir[dirname], key=lambda x: x[0]):
                    f.write(f"  - [`{os.path.basename(path)}`](#{self._slug(path)})\n")
            f.write("\n---\n\n")

            # Детальное описание каждого модуля
            for dirname in sorted(modules_by_dir.keys()):
                display_dir = dirname or "Корень проекта"
                f.write(f"## 📁 {display_dir}\n\n")

                for path, module in sorted(modules_by_dir[dirname], key=lambda x: x[0]):
                    self._write_module_markdown(f, module)

    def _write_module_markdown(self, f, module: ModuleDoc):
        """Записывает описание одного модуля в Markdown."""
        f.write(f"### 📄 `{module.name}`\n\n")
        f.write(f"**Путь:** `{module.path}`\n\n")

        if module.description:
            f.write(f"**Назначение:** {module.description}\n\n")
        elif module.docstring:
            f.write(f"**Назначение:** {module.docstring[:300]}\n\n")

        if module.imports:
            f.write("**Импорты:**\n")
            for imp in module.imports[:10]:
                f.write(f"- `{imp}`\n")
            if len(module.imports) > 10:
                f.write(f"- ... и ещё {len(module.imports) - 10}\n")
            f.write("\n")

        if module.dependencies:
            f.write(f"**Зависимости:** {', '.join(module.dependencies)}\n\n")

        if module.classes:
            f.write(f"#### 🏗️ Классы ({len(module.classes)})\n\n")
            for cls in module.classes:
                self._write_class_markdown(f, cls)

        if module.functions:
            f.write(f"#### 🔧 Функции ({len(module.functions)})\n\n")
            for func in module.functions:
                self._write_function_markdown(f, func)

        if module.constants:
            f.write(f"#### 📊 Константы ({len(module.constants)})\n\n")
            for const in module.constants:
                f.write(f"- **{const.get('name')}** = `{const.get('default')}`\n")
            f.write("\n")

        f.write("---\n\n")

    def _write_class_markdown(self, f, cls: ClassDoc):
        """Записывает описание класса в Markdown."""
        f.write(f"##### `{cls.name}`\n\n")

        if cls.bases and cls.bases != ['object']:
            f.write(f"**Наследует:** {', '.join(cls.bases)}\n\n")

        if cls.is_dataclass:
            f.write("**Датакласс**\n\n")

        if cls.is_mixin:
            f.write("**Миксин**\n\n")

        if cls.description:
            f.write(f"**Описание:** {cls.description}\n\n")

        if cls.class_attrs:
            f.write("**Атрибуты класса:**\n\n")
            f.write("| Имя | Тип | По умолчанию |\n")
            f.write("|-----|-----|-------------|\n")
            for attr in cls.class_attrs:
                default = attr.get('default', '')
                f.write(f"| `{attr.get('name')}` | `{attr.get('type', 'Any')}` | `{default}` |\n")
            f.write("\n")

        if cls.methods:
            f.write("**Методы:**\n\n")
            for method in cls.methods:
                self._write_function_markdown(f, method, is_method=True)

    def _write_function_markdown(self, f, func: FunctionDoc, is_method: bool = False):
        """Записывает описание функции/метода в Markdown."""
        prefix = "`" if not is_method else ""
        f.write(f"- **{prefix}{func.name}**\n\n")

        if func.decorators:
            f.write(f"  *Декораторы:* {', '.join(func.decorators)}\n")

        if func.params:
            f.write("  *Параметры:*\n")
            for param in func.params:
                default_str = f" = {param.default}" if param.default else ""
                f.write(f"    - `{param.name}`: `{param.type_hint}`{default_str}\n")

        if func.return_type != "None":
            f.write(f"  *Возвращает:* `{func.return_type}`\n")

        if func.description:
            desc = func.description[:200]
            if len(func.description) > 200:
                desc += "..."
            f.write(f"  *Описание:* {desc}\n")

        f.write("\n")

    def _slug(self, text: str) -> str:
        """Создаёт URL-безопасный якорь."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9_\-\s]', '', text)
        slug = slug.lower().replace(' ', '-')
        return slug

    def generate_json(self, output_file: str) -> None:
        """Генерирует JSON-документацию."""
        data = {
            "project_root": self.project_root,
            "generated_at": datetime.now().isoformat(),
            "total_modules": len(self.modules),
            "modules": {
                path: module.to_dict()
                for path, module in self.modules.items()
            }
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_html(self, output_file: str) -> None:
        """Генерирует HTML-документацию с использованием встроенного конвертера."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            self.generate_markdown(tmp.name)
            tmp_path = tmp.name

        try:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_body = self.md_converter.convert(md_content)

            full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mozart ERP — Документация проекта</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 30px;
            background: #fafafa;
            color: #1a1a2e;
            line-height: 1.6;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #16213e;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 8px;
        }}
        h1 {{ color: #0f3460; font-size: 2.2em; border-bottom: 3px solid #0f3460; }}
        h2 {{ color: #1a1a2e; font-size: 1.8em; }}
        h3 {{ color: #16213e; font-size: 1.4em; border-bottom: 1px solid #ddd; }}
        h4 {{ color: #2c3e50; font-size: 1.2em; border-bottom: none; }}
        h5 {{ color: #34495e; font-size: 1.1em; }}
        code {{
            background: #eef2f7;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            color: #c0392b;
        }}
        pre {{
            background: #1a1a2e;
            color: #e8e8e8;
            padding: 15px 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.85em;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
        }}
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        th, td {{
            border: 1px solid #e0e0e0;
            padding: 10px 14px;
            text-align: left;
        }}
        th {{
            background: #16213e;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #eef2f7;
        }}
        hr {{
            border: none;
            border-top: 2px solid #0f3460;
            margin: 40px 0;
        }}
        ul, ol {{
            padding-left: 25px;
        }}
        li {{
            margin: 4px 0;
        }}
        a {{
            color: #0f3460;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 10px 15px; }}
            table {{ font-size: 0.85em; }}
            th, td {{ padding: 6px 8px; }}
        }}
        .toc {{
            background: white;
            padding: 20px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 30px;
        }}
        .toc ul {{
            columns: 2;
            list-style: none;
            padding-left: 10px;
        }}
        .toc li {{
            padding: 2px 0;
        }}
        @media (max-width: 600px) {{
            .toc ul {{ columns: 1; }}
        }}
        .module-path {{
            font-size: 0.85em;
            color: #7f8c8d;
            background: #f0f0f0;
            padding: 2px 8px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_html)

            print(f"✅ HTML создан: {output_file}")

        except Exception as e:
            print(f"⚠️ Ошибка при генерации HTML: {e}")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Ошибка генерации</title></head>
<body>
<h1>⚠️ Ошибка при генерации HTML</h1>
<p><b>Причина:</b> {e}</p>
<p>Пожалуйста, откройте Markdown-файл: <code>Документация_проекта.md</code></p>
</body>
</html>""")

        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass


# =============================================================================
# АНАЛИЗАТОР СТРУКТУРЫ ПРОЕКТА
# =============================================================================

class ProjectAnalyzer:
    """Анализирует структуру проекта и строит диаграммы."""

    def __init__(self, modules: Dict[str, ModuleDoc]):
        self.modules = modules

    def get_statistics(self) -> Dict:
        """Собирает статистику по проекту."""
        stats = {
            "total_files": len(self.modules),
            "total_classes": 0,
            "total_methods": 0,
            "total_functions": 0,
            "total_imports": 0,
            "classes_by_module": {},
            "dependencies": set(),
            "most_complex": []
        }

        for path, module in self.modules.items():
            stats["total_classes"] += len(module.classes)
            stats["total_imports"] += len(module.imports)
            stats["classes_by_module"][path] = len(module.classes)

            for cls in module.classes:
                stats["total_methods"] += len(cls.methods)

            stats["total_functions"] += len(module.functions)

            for dep in module.dependencies:
                stats["dependencies"].add(dep)

        stats["most_complex"] = sorted(
            stats["classes_by_module"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return stats

    def generate_mermaid(self) -> str:
        """Генерирует Mermaid-диаграмму зависимостей."""
        lines = ["graph TD"]
        for path, module in self.modules.items():
            if not module.dependencies:
                continue
            node_id = module.name.replace('.py', '')
            for dep in module.dependencies:
                if dep in ('PySide6', 'database', 'controls', 'tabs', 'widgets'):
                    lines.append(f"    {node_id} --> {dep}")
        return "\n".join(lines)


# =============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =============================================================================

def main():
    """Главная функция генерации документации."""
    project_root = "/home/sergey/Documents/configurate"
    output_dir = os.path.join(project_root, "docs")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("🎵 ГЕНЕРАТОР ДОКУМЕНТАЦИИ MOZART ERP")
    print("=" * 70)

    parser = PythonParser(project_root)
    modules = parser.parse_project()

    if not modules:
        print("❌ Не найден ни один Python файл!")
        return

    print(f"\n✅ Обработано файлов: {len(modules)}")

    generator = DocumentationGenerator(modules, project_root)

    md_file = os.path.join(output_dir, "Документация_проекта.md")
    generator.generate_markdown(md_file)
    print(f"✅ Markdown: {md_file}")

    json_file = os.path.join(output_dir, "документация.json")
    generator.generate_json(json_file)
    print(f"✅ JSON: {json_file}")

    html_file = os.path.join(output_dir, "Документация_проекта.html")
    generator.generate_html(html_file)
    print(f"✅ HTML: {html_file}")

    analyzer = ProjectAnalyzer(modules)
    stats = analyzer.get_statistics()

    print("\n" + "=" * 70)
    print("📊 СТАТИСТИКА ПРОЕКТА")
    print("=" * 70)
    print(f"  Всего файлов:    {stats['total_files']}")
    print(f"  Всего классов:   {stats['total_classes']}")
    print(f"  Всего методов:   {stats['total_methods']}")
    print(f"  Всего функций:   {stats['total_functions']}")
    print(f"  Всего импортов:  {stats['total_imports']}")
    print(f"  Зависимости:     {', '.join(sorted(stats['dependencies']))}")
    print("\n  🔥 Самые сложные модули (по количеству классов):")
    for path, count in stats["most_complex"]:
        print(f"    - {path}: {count} классов")

    mermaid = analyzer.generate_mermaid()
    mermaid_file = os.path.join(output_dir, "зависимости.mermaid")
    with open(mermaid_file, 'w', encoding='utf-8') as f:
        f.write(mermaid)
    print(f"\n✅ Mermaid-диаграмма: {mermaid_file}")

    print("\n" + "=" * 70)
    print("✅ ДОКУМЕНТАЦИЯ СОЗДАНА УСПЕШНО!")
    print("=" * 70)


if __name__ == "__main__":
    main()