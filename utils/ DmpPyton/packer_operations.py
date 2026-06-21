# utils/packer_operations.py
# -*- coding: utf-8 -*-

import os
import json
import shutil
from PySide6.QtWidgets import QMessageBox


class PackerOperations:
    """Модуль выполнения физических операций экспорта JSON и копирования файлов."""

    def __init__(self, project_root):
        self.project_root = project_root

    def export_to_json(self, parent_widget, selected_paths, target_dir):
        if not selected_paths or not target_dir:
            QMessageBox.warning(parent_widget, "Внимание", "Проверьте выбор файлов и каталог назначения!")
            return

        json_file_path = os.path.join(target_dir, "Mozart.json")

        # Собираем данные по файлам: путь + содержимое
        files_data = []
        skipped_files = []

        for path in selected_paths:
            # Проверяем, что это файл и он существует
            if not os.path.isfile(path):
                continue

            # Относительный путь от корня проекта
            rel_path = os.path.relpath(path, self.project_root)

            # Пытаемся прочитать содержимое файла
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                files_data.append({
                    "path": rel_path,
                    "content": content
                })
            except UnicodeDecodeError:
                # Файл не является текстовым (бинарный) — пропускаем
                skipped_files.append(rel_path)
            except Exception as e:
                # Другая ошибка чтения
                skipped_files.append(f"{rel_path} (ошибка: {str(e)})")

        # Формируем структуру для JSON
        data_to_save = {
            "project_root": self.project_root,
            "total_files": len(files_data),
            "files": files_data
        }

        # Если были пропущенные файлы — предупреждаем
        if skipped_files:
            QMessageBox.warning(
                parent_widget,
                "Внимание",
                f"Следующие файлы не удалось прочитать (бинарные или повреждённые):\n\n" + "\n".join(
                    skipped_files[:10]) +
                (f"\n\n... и ещё {len(skipped_files) - 10}" if len(skipped_files) > 10 else "")
            )

        # Сохраняем JSON
        try:
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)

            QMessageBox.information(
                parent_widget,
                "Успех",
                f"Файл Mozart.json успешно создан!\n\n"
                f"Сохранено файлов: {len(files_data)}\n"
                f"Пропущено файлов: {len(skipped_files)}\n"
                f"Каталог: {target_dir}"
            )
        except Exception as e:
            QMessageBox.critical(parent_widget, "Ошибка", f"Не удалось записать JSON:\n{str(e)}")

    def copy_selected_files(self, parent_widget, selected_paths, target_dir, folder_name):
        if not selected_paths or not target_dir or not folder_name:
            QMessageBox.warning(parent_widget, "Внимание", "Проверьте выбор файлов, каталог и имя папки!")
            return

        destination_root = os.path.join(target_dir, folder_name)
        copied_files, created_dirs = 0, 0

        try:
            for path in selected_paths:
                rel_path = os.path.relpath(path, self.project_root)
                dest_path = os.path.join(destination_root, rel_path)

                if os.path.isdir(path):
                    os.makedirs(dest_path, exist_ok=True)
                    created_dirs += 1
                elif os.path.isfile(path):
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(path, dest_path)
                    copied_files += 1

            QMessageBox.information(
                parent_widget,
                "Успех",
                f"Структура успешно создана!\n\nСоздано каталогов: {created_dirs}\nСкопировано файлов: {copied_files}"
            )
        except Exception as e:
            QMessageBox.critical(parent_widget, "Ошибка копирования",
                                 f"Произошел сбой при копировании структуры:\n{str(e)}")