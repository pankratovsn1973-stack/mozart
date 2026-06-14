# /home/sergey/Documents/configurate/migrate_to_pyside6.py
# -*- coding: utf-8 -*-
# Скрипт для автоматической миграции с PyQt5 на PySide6
# ЗАПУСКАТЬ ТОЛЬКО ПОСЛЕ УСТАНОВКИ PySide6

import os
import re
import sys

# Расширения файлов для обработки
EXTENSIONS = ('.py', '.pyw', '.pyx', '.pxd')

# Директории, которые НЕ обрабатываем
IGNORE_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', '.idea', '.vscode',
    'node_modules', 'venv', 'env', '.venv', '.env', 'virtualenv',
    'dist', 'build', '.mypy_cache', '.pytest_cache', '.tox',
    '.ipynb_checkpoints', '.DS_Store', 'Thumbs.db', '.trash', '.tmp',
    'logs', 'backup', 'old'
}


def migrate_file(filepath):
    """Обрабатывает один файл: заменяет импорты PyQt5 -> PySide6"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"  ⚠️ Пропущен (ошибка чтения): {filepath} - {e}")
        return False

    original = content

    # 1. Замена импортов PyQt5 -> PySide6
    content = re.sub(r'from PyQt5\.', 'from PySide6.', content)
    content = re.sub(r'import PyQt5\.', 'import PySide6.', content)
    content = re.sub(r'from PySide6 import', 'from PySide6 import', content)

    # 2. Замена Signal -> Signal (только если это класс PyQt5)
    content = re.sub(r'Signal', 'Signal', content)
    content = re.sub(r'Slot', 'Slot', content)
    content = re.sub(r'Property', 'Property', content)

    # 3. Замена QHeaderView.setStretchLastSection (работает так же, но оставляем)
    #    Ничего не меняем, метод одинаковый.

    # 4. Замена Qt.AlignmentFlag.AlignLeft -> Qt.AlignLeft (PySide6 поддерживает оба)
    #    Оставляем как есть — PySide6 понимает старый синтаксис.

    # Если содержимое изменилось, записываем обратно
    if content != original:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Обновлён: {filepath}")
            return True
        except Exception as e:
            print(f"  ❌ Ошибка записи: {filepath} - {e}")
            return False
    else:
        print(f"  ⏭️ Без изменений: {filepath}")
        return False


def migrate_directory(root_dir):
    """Рекурсивно обходит директорию и обрабатывает все .py файлы"""
    processed = 0
    changed = 0

    print(f"\n📁 Сканируем: {root_dir}\n")

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Пропускаем игнорируемые директории
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            if filename.endswith(EXTENSIONS):
                processed += 1
                filepath = os.path.join(dirpath, filename)
                if migrate_file(filepath):
                    changed += 1

    print(f"\n{'=' * 60}")
    print(f"📊 Обработано файлов: {processed}")
    print(f"✏️  Изменено файлов: {changed}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    # Определяем корень проекта (директория, где находится скрипт)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("🔧 МИГРАЦИЯ С PyQt5 НА PySide6")
    print("=" * 60)
    print("\n⚠️  ВНИМАНИЕ!")
    print("   1. Перед запуском убедитесь, что PySide6 установлен:")
    print("      pip install PySide6")
    print("   2. Рекомендуется сделать резервную копию проекта")
    print("   3. Скрипт изменит ВСЕ .py файлы в проекте")
    print("\n" + "=" * 60)

    response = input("\nПродолжить? (y/n): ").strip().lower()

    if response != 'y':
        print("Миграция отменена.")
        sys.exit(0)

    # Запускаем миграцию
    migrate_directory(script_dir)

    print("\n✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("\n📌 После миграции:")
    print("   1. Проверьте, что приложение запускается")
    print("   2. Если есть ошибки импорта, проверьте:")
    print("      - from PySide6.QtCore import Signal (вместо Signal)")
    print("      - from PySide6.QtCore import Slot (вместо Slot)")
    print("      - from PySide6.QtCore import Property (вместо Property)")
    print("\n📌 Если что-то пошло не так, откатить изменения можно через Git:")
    print("      git checkout .")