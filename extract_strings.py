# /home/sergey/Documents/configurate/extract_strings.py
# -*- coding: utf-8 -*-
# Извлекает все строки из QMessageBox, show_error, show_warning, show_info, setWindowTitle
# Сохраняет в JSON с указанием файла, строки, типа и полного контекста

import os
import re
import json

EXTENSIONS = ('.py', '.pyw', '.pyx')
IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env', '.env',
    'dist', 'build', '.mypy_cache', '.pytest_cache', '.tox',
    '.ipynb_checkpoints', '.DS_Store', 'lang_data'
}


def extract_strings(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
        return results

    lines = content.split('\n')

    for i, line in enumerate(lines):
        line_num = i + 1

        # Пропускаем строки, где уже есть вызов translator.tr
        if 'translator.tr' in line:
            continue

        # QMessageBox.information / warning / critical / question
        match = re.search(r'QMessageBox\.(information|warning|critical|question)\(([^,]+),\s*(["\'])([^"\']+)\3', line)
        if match:
            msg_type = match.group(1)
            text = match.group(4)
            if re.search('[а-яА-ЯёЁ]', text):
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'QMessageBox',
                    'subtype': msg_type,
                    'original': text,
                    'full_line': line.strip()
                })
            continue

        # QMessageBox.about (два сообщения: заголовок и текст)
        match = re.search(r'QMessageBox\.about\(([^,]+),\s*(["\'])([^"\']+)\2,\s*(["\'])([^"\']+)\4', line)
        if match:
            title = match.group(3)
            text = match.group(5)
            if title and re.search('[а-яА-ЯёЁ]', title):
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'QMessageBox.about_title',
                    'original': title,
                    'full_line': line.strip()
                })
            if text and re.search('[а-яА-ЯёЁ]', text):
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'QMessageBox.about_text',
                    'original': text,
                    'full_line': line.strip()
                })
            continue

        # self.show_error / show_warning / show_info
        match = re.search(r'self\.(show_error|show_warning|show_info)\((["\'])([^"\']+)\2', line)
        if match:
            msg_type = match.group(1)
            text = match.group(3)
            if text and re.search('[а-яА-ЯёЁ]', text):
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'show_xxx',
                    'subtype': msg_type,
                    'original': text,
                    'full_line': line.strip()
                })
            continue

        # self.show_error / show_warning / show_info (с self.translator? пропускаем)

        # setWindowTitle
        match = re.search(r'\.setWindowTitle\((["\'])([^"\']*[а-яА-ЯёЁ]+[^"\']*)\1', line)
        if match:
            text = match.group(2)
            if text:
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'setWindowTitle',
                    'original': text,
                    'full_line': line.strip()
                })
            continue

        # raise Exception
        match = re.search(r'raise Exception\((["\'])([^"\']*[а-яА-ЯёЁ]+[^"\']*)\1', line)
        if match:
            text = match.group(2)
            if text:
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'raise',
                    'original': text,
                    'full_line': line.strip()
                })
            continue

        # print с русским текстом
        match = re.search(r'print\((["\'])([^"\']*[а-яА-ЯёЁ]+[^"\']*)\1', line)
        if match:
            text = match.group(2)
            if text:
                results.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'print',
                    'original': text,
                    'full_line': line.strip()
                })
            continue

    return results


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_strings = []

    print("🔍 Сканируем проект...")

    for root, dirs, files in os.walk(script_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file.endswith(EXTENSIONS):
                filepath = os.path.join(root, file)
                strings = extract_strings(filepath)
                if strings:
                    all_strings.extend(strings)
                    print(f"  ✅ {os.path.relpath(filepath, script_dir)}: {len(strings)} строк")

    output_file = os.path.join(script_dir, 'extracted_strings.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_strings, f, ensure_ascii=False, indent=2)

    print(f"\n📊 Итого найдено строк: {len(all_strings)}")
    print(f"💾 Результат сохранён: {output_file}")

    # Группировка по типам
    types = {}
    for item in all_strings:
        t = item['type']
        if t not in types:
            types[t] = 0
        types[t] += 1

    print("\n📋 По типам:")
    for t, count in types.items():
        print(f"    {t}: {count}")


if __name__ == "__main__":
    main()