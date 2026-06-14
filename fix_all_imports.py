# /home/sergey/Documents/configurate/fix_all_imports.py
import os
import re


def fix_imports_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Находим строки импорта, где QAction вырезан неправильно
    #    Пример: from PySide6.QtWidgets import (из любых импортов в QtWidgets
    content = re.sub(
        r'from PySide6\.QtWidgets import \([^)]*QAction,?\s*',
        'from PySide6.QtWidgets import (',
        content
    )
    content = re.sub(
        r'from PySide6\.QtWidgets import QAction,?\s*',
        '',
        content
    )

    # 2. Добавляем отдельный импорт QAction из QtGui, если его нет
    if 'QAction' in content and 'from PySide6.QtGui import QAction' not in content:
        # Находим последний импорт из PySide6 и вставляем после него
        lines = content.split('\n')
        new_lines = []
        inserted = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if not inserted and line.startswith('from PySide6.') and 'import' in line:
                # Проверяем, не добавили ли мы уже
                if i + 1 < len(lines) and 'from PySide6.QtGui import QAction' in lines[i + 1]:
                    continue
                new_lines.append('from PySide6.QtGui import QAction')
                inserted = True
        content = '\n'.join(new_lines)

    # 3. Исправляем битые строки импорта (где скобки не закрыты)
    #    Ищем строки, которые начинаются с 'from PySide6.' и заканчиваются на ','
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Если строка начинается с from PySide6 и заканчивается на ',' (не закрыта)
        if line.startswith('from PySide6.') and line.rstrip().endswith(','):
            # Объединяем со следующей строкой
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            combined = line + ' ' + next_line
            # Проверяем, есть ли закрывающая скобка
            if '(' in combined and ')' not in combined:
                # Ищем закрывающую скобку дальше
                j = i + 2
                while j < len(lines) and ')' not in combined:
                    combined += ' ' + lines[j]
                    j += 1
                new_lines.append(combined)
                i = j
                continue
        new_lines.append(line)
        i += 1
    content = '\n'.join(new_lines)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


# Проходим по всем файлам
fixed = 0
for root, dirs, files in os.walk('/home/sergey/Documents/configurate'):
    if '.venv' in dirs:
        dirs.remove('.venv')
    for file in files:
        if file.endswith('.py'):
            if fix_imports_in_file(os.path.join(root, file)):
                print(f"✅ Исправлен: {os.path.join(root, file)}")
                fixed += 1

print(f"\nГотово! Исправлено файлов: {fixed}")