# /home/sergey/Documents/configurate/fix_missing_imports.py
import os
import re


def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Список недостающих импортов для разных классов
    missing_imports = {
        'QGraphicsScene': 'from PySide6.QtWidgets import QGraphicsScene',
        'QGraphicsItem': 'from PySide6.QtWidgets import QGraphicsItem',
        'QAction': 'from PySide6.QtGui import QAction',
        'QColor': 'from PySide6.QtGui import QColor',
        'QFont': 'from PySide6.QtGui import QFont',
        'QTransform': 'from PySide6.QtGui import QTransform',
    }

    # Проверяем использование классов и добавляем импорты
    lines = content.split('\n')
    new_lines = []
    imports_to_add = set()

    # Находим все строки с 'class ...(' и определяем родительские классы
    for line in lines:
        if 'class ' in line and '(' in line:
            # Извлекаем родительские классы
            import re
            match = re.search(r'class\s+\w+\(([^)]+)\)', line)
            if match:
                parents = match.group(1).split(',')
                for parent in parents:
                    parent = parent.strip()
                    if parent in missing_imports:
                        imports_to_add.add(missing_imports[parent])

    # Добавляем недостающие импорты в начало файла (после существующих импортов)
    if imports_to_add:
        new_content = content
        for imp in imports_to_add:
            if imp not in content:
                # Вставляем после последнего импорта
                lines = new_content.split('\n')
                inserted = False
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].startswith('from PySide6.') or lines[i].startswith('import '):
                        lines.insert(i + 1, imp)
                        inserted = True
                        break
                if not inserted:
                    lines.insert(0, imp)
                new_content = '\n'.join(lines)

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    return False


# Проходим по всем файлам
fixed = 0
for root, dirs, files in os.walk('/home/sergey/Documents/configurate'):
    if '.venv' in dirs:
        dirs.remove('.venv')
    for file in files:
        if file.endswith('.py'):
            if fix_file(os.path.join(root, file)):
                print(f"✅ Исправлен: {os.path.join(root, file)}")
                fixed += 1

print(f"\nГотово! Исправлено файлов: {fixed}")