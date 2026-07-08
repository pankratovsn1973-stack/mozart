# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_core/description_loader.py
"""
Загрузчик описаний из документации проекта.
Версия: 2.0 — для единой таблицы сущностей
"""

import os
import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class DescriptionLoader:
    """Загружает описания файлов, классов, функций из документации."""

    def __init__(self, description_file: Optional[str] = None):
        self.description_file = description_file
        self.data = None
        self._loaded = False
        self._load()

    def _load(self):
        if self._loaded:
            return

        if not self.description_file:
            base = Path(__file__).parent.parent
            candidates = [
                base / "docs" / "документация_проекта_новый.md",
                base / "docs" / "документация.json",
                base / "Документация_проекта.md",
                base / "docs" / "Документация_проекта.md",
                Path.home() / "Documents" / "configurate" / "docs" / "документация_проекта_новый.md",
            ]
            for candidate in candidates:
                if candidate.exists():
                    self.description_file = str(candidate)
                    break

        if not self.description_file or not Path(self.description_file).exists():
            print(f"⚠️ Документация не найдена")
            self.data = {'files': [], 'directories': [], 'statistics': {}}
            self._loaded = True
            return

        if self.description_file.endswith('.json'):
            with open(self.description_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self._loaded = True
            print(f"✅ Загружена документация из {self.description_file} (JSON)")
            return

        if self.description_file.endswith('.md'):
            self.data = self._parse_markdown()
            self._loaded = True
            print(f"✅ Загружена документация из {self.description_file} (MD)")
            return

    def _parse_markdown(self) -> Dict:
        with open(self.description_file, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            'files': [],
            'directories': [],
            'statistics': {}
        }

        file_pattern = r'#{3,4} Файл \d+: `([^`]+)`'
        file_blocks = re.split(file_pattern, content)

        for i in range(1, len(file_blocks), 2):
            filename = file_blocks[i]
            block = file_blocks[i + 1] if i + 1 < len(file_blocks) else ''

            file_info = self._parse_file_block(filename, block)
            if file_info:
                result['files'].append(file_info)

        stat_pattern = r'\*\*Всего файлов\*\*\s+(\d+)'
        stat_match = re.search(stat_pattern, content)
        if stat_match:
            result['statistics']['total_files'] = int(stat_match.group(1))

        return result

    def _parse_file_block(self, filename: str, block: str) -> Dict:
        info = {
            'filename': filename,
            'path': '',
            'description': '',
            'classes': [],
            'functions': [],
            'imports': [],
            'status': '',
            'used_in': ''
        }

        path_match = re.search(r'\*\*Полный путь:\*\*\s*`([^`]+)`', block)
        if path_match:
            info['path'] = path_match.group(1)

        desc_match = re.search(r'\*\*Описание:\*\*\s*(.+?)(?=\n\*\*|$)', block, re.DOTALL)
        if desc_match:
            info['description'] = desc_match.group(1).strip()

        class_section = re.search(r'\*\*Классы:\*\*\s*\n((?:.+\n)+?)(?=\*\*|$)', block)
        if class_section:
            classes_text = class_section.group(1)
            for line in classes_text.strip().split('\n'):
                if line.strip().startswith('-'):
                    class_match = re.search(r'`([^`]+)`\s*---\s*(.+)', line)
                    if class_match:
                        info['classes'].append({
                            'name': class_match.group(1),
                            'description': class_match.group(2).strip()
                        })

        func_section = re.search(r'\*\*Основные функции:\*\*\s*\n((?:.+\n)+?)(?=\*\*|$)', block)
        if func_section:
            funcs_text = func_section.group(1)
            for line in funcs_text.strip().split('\n'):
                if line.strip().startswith('-'):
                    func_match = re.search(r'`([^`]+)`\s*---\s*(.+)', line)
                    if func_match:
                        info['functions'].append({
                            'name': func_match.group(1),
                            'description': func_match.group(2).strip()
                        })

        imports_match = re.search(r'\*\*Импорты:\*\*\s*(.+?)(?=\n\*\*|$)', block)
        if imports_match:
            imports_text = imports_match.group(1).strip()
            for imp in imports_text.split(','):
                imp = imp.strip()
                if imp:
                    info['imports'].append(imp)

        status_match = re.search(r'\*\*Статус:\*\*\s*(.+)', block)
        if status_match:
            info['status'] = status_match.group(1).strip()

        used_match = re.search(r'\*\*Используется в:\*\*\s*(.+)', block)
        if used_match:
            info['used_in'] = used_match.group(1).strip()

        return info

    def get_file_description(self, file_path: str) -> Dict:
        if not self.data:
            return {}

        for file_info in self.data.get('files', []):
            if file_info.get('path') == file_path or file_info.get('filename') in file_path:
                return file_info
        return {}

    def get_class_description(self, file_path: str, class_name: str) -> Dict:
        file_info = self.get_file_description(file_path)
        for cls in file_info.get('classes', []):
            if cls.get('name') == class_name or class_name in cls.get('name', ''):
                return cls
        return {}

    def get_function_description(self, file_path: str, func_name: str) -> Dict:
        file_info = self.get_file_description(file_path)
        for func in file_info.get('functions', []):
            if func.get('name') == func_name or func_name in func.get('name', ''):
                return func
        return {}

    def is_loaded(self) -> bool:
        return self._loaded and self.data is not None