# /home/sergey/Documents/configurate/fix_qaction_imports.py
import os
import re


def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Ищем строки с импортом QAction из QtWidgets и переносим в QtGui
    # Удаляем QAction из QtWidgets
    content = re.sub(
        r'from PySide6\.QtWidgets import ([^;]+?)QAction,?\s*',
        'from PySide6.QtWidgets import \\1',
        content
    )
    content = re.sub(
        r'from PySide6\.QtWidgets import ',
        '',
        content
    )

    # Добавляем импорт QAction из QtGui, если его нет и QAction используется
    if 'QAction' in content and 'from PySide6.QtGui import QAction' not in content:
        # Вставляем после последнего импорта из PySide6
        lines = content.split('\n')
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.startswith('from PySide6.') and 'import' in line:
                new_lines.append('from PySide6.QtGui import QAction')
                inserted = True
        content = '\n'.join(new_lines)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Исправлен: {filepath}")
        return True
    return False


# Пройтись по всем .py файлам
for root, dirs, files in os.walk('/home/sergey/Documents/configurate'):
    # Пропускаем .venv
    if '.venv' in dirs:
        dirs.remove('.venv')
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))

print("Готово!")