# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_core/parser.py
"""
AST-парсер Python файлов для Аналитика Моцарт.
Версия: 3.5 — с отладкой и end_line
"""

import ast
import hashlib
import tokenize
import io
from typing import List, Dict, Optional, Any


class PythonParser:
    """Полный парсер Python файлов с сохранением порядка."""

    def __init__(self):
        self.file_path = None
        self.content = None
        self.tree = None
        self.lines = []
        self.comments = {}
        self.debug = True  # Включить отладку

    def parse_file(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """Парсит файл и возвращает структуру."""
        self.file_path = file_path

        if content is None:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        self.content = content
        self.lines = content.splitlines()

        if self.debug:
            print(f"\n📄 ПАРСИНГ: {os.path.basename(file_path)}")
            print(f"   Строк в файле: {len(self.lines)}")

        try:
            self.tree = ast.parse(content)
        except SyntaxError as e:
            if self.debug:
                print(f"   ❌ Ошибка синтаксиса: {e}")
            return {
                'file_path': file_path,
                'full_text': content,
                'error': str(e),
                'header': '',
                'imports': [],
                'global_variables': [],
                'procedures': [],
                'classes': []
            }

        self._extract_comments(content)

        if self.debug:
            # Выводим структуру AST
            print(f"   Узлов верхнего уровня: {len(self.tree.body)}")
            for node in self.tree.body:
                node_type = type(node).__name__
                if hasattr(node, 'name'):
                    print(f"     - {node_type}: {node.name} (строка {node.lineno})")
                else:
                    print(f"     - {node_type} (строка {node.lineno})")

        result = {
            'file_path': file_path,
            'hash_md5': hashlib.md5(content.encode('utf-8')).hexdigest(),
            'size_bytes': len(content.encode('utf-8')),
            'full_text': content,
            'header': self._parse_header(),
            'imports': self._parse_imports(),
            'global_variables': self._parse_global_variables(),
            'procedures': self._parse_procedures(),
            'classes': self._parse_classes(),
            'comments': self.comments,
        }

        if self.debug:
            print(f"   📊 Найдено:")
            print(f"      - Импортов: {len(result['imports'])}")
            print(f"      - Глобальных переменных: {len(result['global_variables'])}")
            print(f"      - Процедур: {len(result['procedures'])}")
            print(f"      - Классов: {len(result['classes'])}")

        return result

    # ================================================================
    # КОММЕНТАРИИ
    # ================================================================

    def _extract_comments(self, content: str):
        """Извлекает все комментарии из файла."""
        self.comments = {}
        try:
            tokens = tokenize.generate_tokens(io.StringIO(content).readline)
            for tok_type, tok_text, (srow, _), (erow, _), _ in tokens:
                if tok_type == tokenize.COMMENT:
                    if srow not in self.comments:
                        self.comments[srow] = []
                    self.comments[srow].append(tok_text)
        except Exception:
            pass

    def _get_comment_for_line(self, line_num: int) -> str:
        if line_num in self.comments:
            return ' '.join(self.comments[line_num])
        return ""

    def _get_comment_for_node(self, node: ast.AST) -> str:
        if hasattr(node, 'lineno'):
            return self._get_comment_for_line(node.lineno)
        return ""

    # ================================================================
    # РАБОТА С ТЕКСТОМ
    # ================================================================

    def _get_text(self, start_line: int, end_line: int) -> str:
        """Возвращает текст из строк (1-индексация)."""
        if start_line < 1 or end_line > len(self.lines):
            return ""
        return '\n'.join(self.lines[start_line - 1:end_line])

    # ================================================================
    # ПАРСИНГ С СОРТИРОВКОЙ ПО ПОЗИЦИИ
    # ================================================================

    def _parse_header(self) -> str:
        return ast.get_docstring(self.tree) or ""

    def _parse_imports(self) -> List[Dict]:
        imports = []
        for node in self.tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                text = self._get_text(node.lineno, node.end_lineno)
                comment = self._get_comment_for_node(node)
                imports.append({
                    'text': text,
                    'position': node.lineno,
                    'comment': comment
                })
        imports.sort(key=lambda x: x.get('position', 0))
        return imports

    def _parse_global_variables(self) -> List[Dict]:
        variables = []
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        text = self._get_text(node.lineno, node.end_lineno)
                        comment = self._get_comment_for_node(node)
                        variables.append({
                            'name': target.id,
                            'text': text,
                            'position': node.lineno,
                            'comment': comment,
                            'value': self._get_value(node.value),
                            'type': self._infer_type(node.value),
                            'is_constant': target.id.isupper(),
                            'is_annotated': False
                        })
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    text = self._get_text(node.lineno, node.end_lineno)
                    comment = self._get_comment_for_node(node)
                    variables.append({
                        'name': node.target.id,
                        'text': text,
                        'position': node.lineno,
                        'comment': comment,
                        'value': self._get_value(node.value),
                        'type': self._get_type_hint(node.annotation),
                        'is_constant': node.target.id.isupper(),
                        'is_annotated': True
                    })
        variables.sort(key=lambda x: x.get('position', 0))
        return variables

    def _parse_procedures(self) -> List[Dict]:
        """Парсит процедуры (функции на уровне файла)."""
        procedures = []
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                text = self._get_text(node.lineno, node.end_lineno)
                comment = self._get_comment_for_node(node)

                if self.debug:
                    print(f"      🔍 Найдена процедура: {node.name} (строка {node.lineno}-{node.end_lineno})")

                procedures.append({
                    'name': node.name,
                    'text': text,
                    'position': node.lineno,
                    'end_line': node.end_lineno,  # <-- ДОБАВЛЕНО!
                    'comment': comment,
                    'docstring': ast.get_docstring(node) or "",
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'is_generator': self._is_generator(node),
                    'return_type': self._get_return_type(node),
                    'params': self._parse_params(node),
                    'decorators': self._safe_get_decorators(node),
                    'calls': self._parse_calls(node)
                })
        procedures.sort(key=lambda x: x.get('position', 0))

        if self.debug:
            print(f"      📊 Всего процедур: {len(procedures)}")

        return procedures

    def _parse_params(self, node: ast.FunctionDef) -> List[Dict]:
        params = []
        for arg in node.args.args:
            param = {
                'name': arg.arg,
                'type': self._get_type_hint(arg.annotation) if arg.annotation else None,
                'default': None,
                'is_required': True
            }
            params.append(param)

        defaults = node.args.defaults
        if defaults:
            offset = len(node.args.args) - len(defaults)
            for i, default in enumerate(defaults):
                idx = offset + i
                if idx < len(params):
                    params[idx]['default'] = self._get_value(default)
                    params[idx]['is_required'] = False

        if node.args.vararg:
            params.append({
                'name': f"*{node.args.vararg.arg}",
                'type': 'tuple',
                'default': None,
                'is_required': False
            })

        if node.args.kwarg:
            params.append({
                'name': f"**{node.args.kwarg.arg}",
                'type': 'dict',
                'default': None,
                'is_required': False
            })

        return params

    def _parse_classes(self) -> List[Dict]:
        """Парсит классы."""
        classes = []
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                text = self._get_text(node.lineno, node.end_lineno)
                header = self._get_text(node.lineno, node.lineno)
                comment = self._get_comment_for_node(node)

                if self.debug:
                    print(f"      🔍 Найден класс: {node.name} (строка {node.lineno}-{node.end_lineno})")

                classes.append({
                    'name': node.name,
                    'header': header,
                    'text': text,
                    'position': node.lineno,
                    'end_line': node.end_lineno,  # <-- ДОБАВЛЕНО!
                    'comment': comment,
                    'docstring': ast.get_docstring(node) or "",
                    'bases': [self._get_base_name(b) for b in node.bases],
                    'is_dataclass': self._is_dataclass(node),
                    'methods': self._parse_methods(node),
                    'properties': self._parse_properties(node),
                    'class_variables': self._parse_class_variables(node)
                })
        classes.sort(key=lambda x: x.get('position', 0))

        if self.debug:
            print(f"      📊 Всего классов: {len(classes)}")

        return classes

    def _parse_methods(self, node: ast.ClassDef) -> List[Dict]:
        """Парсит методы класса."""
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Проверяем, не property ли это
                is_property = False
                for d in item.decorator_list:
                    if isinstance(d, ast.Name) and d.id == 'property':
                        is_property = True
                        break
                    if isinstance(d, ast.Call):
                        if isinstance(d.func, ast.Name) and d.func.id == 'property':
                            is_property = True
                            break

                if is_property:
                    continue

                text = self._get_text(item.lineno, item.end_lineno)
                comment = self._get_comment_for_node(item)
                method_type = 'instance'
                for d in item.decorator_list:
                    if isinstance(d, ast.Name):
                        if d.id == 'classmethod':
                            method_type = 'classmethod'
                        elif d.id == 'staticmethod':
                            method_type = 'staticmethod'

                if self.debug:
                    print(f"         🔍 Найден метод: {item.name} (строка {item.lineno}-{item.end_lineno})")

                methods.append({
                    'name': item.name,
                    'text': text,
                    'position': item.lineno,
                    'end_line': item.end_lineno,  # <-- ДОБАВЛЕНО!
                    'comment': comment,
                    'method_type': method_type,
                    'docstring': ast.get_docstring(item) or "",
                    'is_async': isinstance(item, ast.AsyncFunctionDef),
                    'is_generator': self._is_generator(item),
                    'return_type': self._get_return_type(item),
                    'params': self._parse_params(item),
                    'decorators': self._safe_get_decorators(item),
                    'calls': self._parse_calls(item)
                })
        methods.sort(key=lambda x: x.get('position', 0))
        return methods

    def _parse_properties(self, node: ast.ClassDef) -> List[Dict]:
        """Парсит свойства @property."""
        properties = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                is_property = False
                for d in item.decorator_list:
                    if isinstance(d, ast.Name) and d.id == 'property':
                        is_property = True
                        break
                    if isinstance(d, ast.Call):
                        if isinstance(d.func, ast.Name) and d.func.id == 'property':
                            is_property = True
                            break

                if is_property:
                    text = self._get_text(item.lineno, item.end_lineno)
                    comment = self._get_comment_for_node(item)

                    if self.debug:
                        print(f"         🔍 Найдено свойство: {item.name} (строка {item.lineno}-{item.end_lineno})")

                    properties.append({
                        'name': item.name,
                        'text': text,
                        'position': item.lineno,
                        'end_line': item.end_lineno,  # <-- ДОБАВЛЕНО!
                        'comment': comment,
                        'return_type': self._get_return_type(item),
                        'is_readonly': True
                    })
        properties.sort(key=lambda x: x.get('position', 0))
        return properties

    def _parse_class_variables(self, node: ast.ClassDef) -> List[Dict]:
        """Парсит переменные класса."""
        variables = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        text = self._get_text(item.lineno, item.end_lineno)
                        comment = self._get_comment_for_node(item)
                        variables.append({
                            'name': target.id,
                            'text': text,
                            'position': item.lineno,
                            'comment': comment,
                            'value': self._get_value(item.value),
                            'type': self._infer_type(item.value)
                        })
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    text = self._get_text(item.lineno, item.end_lineno)
                    comment = self._get_comment_for_node(item)
                    variables.append({
                        'name': item.target.id,
                        'text': text,
                        'position': item.lineno,
                        'comment': comment,
                        'value': self._get_value(item.value),
                        'type': self._get_type_hint(item.annotation),
                        'is_annotated': True
                    })
        variables.sort(key=lambda x: x.get('position', 0))
        return variables

    def _parse_calls(self, node: ast.AST) -> List[Dict]:
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_info = {
                    'line_number': child.lineno,
                    'callee_name': None,
                    'callee_type': 'unknown',
                }

                if isinstance(child.func, ast.Name):
                    call_info['callee_name'] = child.func.id
                    call_info['callee_type'] = 'function'
                elif isinstance(child.func, ast.Attribute):
                    call_info['callee_name'] = child.func.attr
                    call_info['callee_type'] = 'method'

                if call_info['callee_name']:
                    calls.append(call_info)

        return calls

    # ================================================================
    # БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ДЕКОРАТОРОВ
    # ================================================================

    def _safe_get_decorators(self, node) -> List[str]:
        names = []
        if not hasattr(node, 'decorator_list'):
            return names

        for d in node.decorator_list:
            try:
                if isinstance(d, ast.Name):
                    names.append(d.id)
                elif isinstance(d, ast.Call):
                    if hasattr(d, 'func'):
                        if isinstance(d.func, ast.Name):
                            names.append(d.func.id)
                        elif isinstance(d.func, ast.Attribute):
                            names.append(d.func.attr)
                elif isinstance(d, ast.Attribute):
                    names.append(d.attr)
            except Exception:
                pass

        return names

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    def _get_type_hint(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
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
        return "Any"

    def _infer_type(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, bool):
                return "bool"
            elif node.value is None:
                return "None"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        elif isinstance(node, ast.Name):
            return node.id
        return "Any"

    def _get_value(self, node: ast.AST) -> Optional[str]:
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            values = [self._get_value(e) for e in node.elts]
            return f"[{', '.join(v for v in values if v)}]"
        elif isinstance(node, ast.Dict):
            keys = [self._get_value(k) for k in node.keys]
            values = [self._get_value(v) for v in node.values]
            pairs = [f"{k}: {v}" for k, v in zip(keys, values) if k]
            return f"{{{', '.join(pairs)}}}"
        elif isinstance(node, ast.Tuple):
            values = [self._get_value(e) for e in node.elts]
            return f"({', '.join(v for v in values if v)})"
        elif isinstance(node, ast.Call):
            return f"{self._get_value(node.func)}(...)"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_value(node.value)}.{node.attr}"
        return "..."

    def _get_return_type(self, node: ast.FunctionDef) -> str:
        if node.returns:
            return self._get_type_hint(node.returns)
        return "None"

    def _get_base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return "object"

    def _is_generator(self, node: ast.FunctionDef) -> bool:
        for item in node.body:
            if isinstance(item, ast.Yield) or isinstance(item, ast.YieldFrom):
                return True
        return False

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        for d in node.decorator_list:
            if isinstance(d, ast.Name) and d.id == 'dataclass':
                return True
            if isinstance(d, ast.Call):
                if isinstance(d.func, ast.Name) and d.func.id == 'dataclass':
                    return True
        return False


# Добавляем импорт os для basename
import os