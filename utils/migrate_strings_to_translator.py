#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт автоматической замены русских строк на translator.tr()
Запуск: python migrate_strings_to_translator.py
"""

import os
import re
from pathlib import Path

# Словарь замены (русская строка -> label_key)
# Составлен на основе extracted_strings.json
REPLACEMENTS = {
    # QMessageBox заголовки
    '"Ошибка"': 'translator.tr("error")',
    '"Предупреждение"': 'translator.tr("warning")',
    '"Информация"': 'translator.tr("info")',
    '"Подтверждение"': 'translator.tr("confirm_title")',

    # QMessageBox сообщения
    '"Выберите запись для редактирования"': 'translator.tr("warn_select_record_edit")',
    '"Выберите запись для удаления"': 'translator.tr("warn_select_record_delete")',
    '"Удалить выбранную запись?"': 'translator.tr("confirm_delete_record")',
    '"Такая связь уже существует"': 'translator.tr("error_composition_exists")',
    '"Не удалось подготовить ext-таблицу/поле"': 'translator.tr("error_ext_table_prepare")',
    '"У сущности нет полей"': 'translator.tr("info_entity_no_fields")',
    '"Выберите тип связи"': 'translator.tr("warn_select_ref_type")',
    '"Выберите правило"': 'translator.tr("warn_select_rule")',
    '"Не удалось создать копию"': 'translator.tr("error_copy_failed")',
    '"Выберите запись"': 'translator.tr("warn_select_record")',
    '"Не указан entity_alias для Reference"': 'translator.tr("error_no_entity_alias")',

    # setWindowTitle
    '.setWindowTitle("Свойства поля (meta.fields)")': '.setWindowTitle(translator.tr("title_field_properties"))',
    '.setWindowTitle("Просмотрщик SQLite")': '.setWindowTitle(translator.tr("title_sqlite_viewer"))',
    '.setWindowTitle("Тип связи")': '.setWindowTitle(translator.tr("title_ref_type"))',
    '.setWindowTitle("Правило связи")': '.setWindowTitle(translator.tr("title_ref_rule"))',
    '.setWindowTitle("Импорт данных")': '.setWindowTitle(translator.tr("title_import_data"))',
    '.setWindowTitle("Выбор значения")': '.setWindowTitle(translator.tr("title_select_value"))',
    '.setWindowTitle("MOZART ERP - Конфигуратор")': '.setWindowTitle(translator.tr("title_main_window"))',

    # show_xxx
    'self.show_warning("Выберите запись")': 'self.show_warning(translator.tr("warn_select_record"))',
    'self.show_error("Не удалось создать копию")': 'self.show_error(translator.tr("error_copy_failed"))',
}


def add_translator_import(content):
    """Добавляет импорт translator, если его нет"""
    if 'from lang.local_translator import LocalTranslator' not in content:
        # Находим место для вставки
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_pos = i + 1
        lines.insert(insert_pos, 'from lang.local_translator import LocalTranslator')
        content = '\n'.join(lines)
    return content


def add_translator_instance(content):
    """Добавляет self.translator = LocalTranslator() в __init__ методов"""
    if 'self.translator' not in content and 'translator.tr' in content:
        # Ищем def __init__
        pattern = r'(def __init__\([^)]*\):.*?)(?=\n    def |\n    @|$)'

        def replace_init(match):
            init_body = match.group(1)
            if 'self.translator' not in init_body:
                # Добавляем после первой строки
                lines = init_body.split('\n')
                lines.insert(1, '        self.translator = LocalTranslator()')
                return '\n'.join(lines)
            return init_body

        content = re.sub(pattern, replace_init, content, flags=re.DOTALL)
    return content


def process_file(filepath):
    """Обрабатывает один файл"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ Ошибка чтения {filepath}: {e}")
        return False

    original = content

    # Добавляем импорт
    content = add_translator_import(content)

    # Добавляем self.translator
    content = add_translator_instance(content)

    # Выполняем замены
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    root_dir = Path("/home/sergey/Documents/configurate")

    # Файлы, которые нужно обработать (на основе extracted_strings.json)
    target_files = [
        "ide_main.py",
        "ide_db_work.py",
        "ide_field_edit.py",
        "view_sqlite.py",
        "openDBF.py",
        "tabs/balance_units_tab.py",
        "tabs/users_roles_tab.py",
        "tabs/entities_tab.py",
        "tabs/relations_tab.py",
        "tabs/entity_subtabs/fields_tab.py",
        "tabs/entity_subtabs/import_engine.py",
        "tabs/entity_subtabs/bu_visibility_tab.py",
        "tabs/entity_subtabs/composition_tab.py",
        "tabs/user_roles/context_tab.py",
        "mozart_import/gui/progress_dialog.py",
        "widgets/reference_editor.py",
    ]

    print("=" * 60)
    print("Миграция строк интерфейса на translator.tr()")
    print("=" * 60)

    modified = 0
    for file in target_files:
        full_path = root_dir / file
        if full_path.exists():
            if process_file(full_path):
                print(f"  ✅ {file}")
                modified += 1
            else:
                print(f"  ⏭️ {file} (без изменений)")
        else:
            print(f"  ⚠️ {file} (не найден)")

    print(f"\n✅ Обработано файлов: {modified}")
    print("\n⚠️ ВНИМАНИЕ! После миграции:")
    print("   1. Убедитесь, что SQL с переводами выполнен в БД")
    print("   2. Проверьте работу приложения")
    print("   3. При необходимости откатите изменения через git")


if __name__ == "__main__":
    main()