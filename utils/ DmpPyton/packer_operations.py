# utils/packer_operations.py
# -*- coding: utf-8 -*-

import os
import json
import shutil
from PySide6.QtWidgets import QMessageBox


class PackerOperations:
    """Модуль выполнения физических операций экспорта JSON, TXT и копирования файлов."""

    def __init__(self, project_root):
        self.project_root = project_root

    def export_to_json(self, parent_widget, selected_paths, target_dir):
        if not selected_paths or not target_dir:
            QMessageBox.warning(parent_widget, "Внимание", "Проверьте выбор файлов и каталог назначения!")
            return

        json_file_path = os.path.join(target_dir, "Mozart.json")

        files_data = []
        skipped_files = []

        for path in selected_paths:
            if not os.path.isfile(path):
                continue

            rel_path = os.path.relpath(path, self.project_root)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                files_data.append({
                    "path": rel_path,
                    "content": content
                })
            except UnicodeDecodeError:
                skipped_files.append(rel_path)
            except Exception as e:
                skipped_files.append(f"{rel_path} (ошибка: {str(e)})")

        data_to_save = {
            "project_root": self.project_root,
            "total_files": len(files_data),
            "files": files_data
        }

        if skipped_files:
            QMessageBox.warning(
                parent_widget,
                "Внимание",
                f"Следующие файлы не удалось прочитать (бинарные или повреждённые):\n\n" + "\n".join(
                    skipped_files[:10]) +
                (f"\n\n... и ещё {len(skipped_files) - 10}" if len(skipped_files) > 10 else "")
            )

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

    def export_to_single_txt(self, parent_widget, selected_paths, target_dir):
        """Выгрузка содержимого выделенных файлов в один TXT с разделителями."""
        if not selected_paths or not target_dir:
            QMessageBox.warning(parent_widget, "Внимание", "Проверьте выбор файлов и каталог назначения!")
            return

        txt_file_path = os.path.join(target_dir, "Mozart_Combined.txt")
        files_processed = 0
        skipped_files = []

        try:
            with open(txt_file_path, "w", encoding="utf-8") as out_f:
                for path in selected_paths:
                    # Пропускаем папки, берем только реальные файлы
                    if not os.path.isfile(path):
                        continue

                    # Пишем заголовок ровно по твоему шаблону
                    out_f.write("#**************************************************\n")
                    out_f.write(f"#*далее файл @({path})\n")
                    out_f.write("#***************************************************\n")

                    # Пытаемся прочитать и написать содержимое
                    try:
                        with open(path, "r", encoding="utf-8") as in_f:
                            out_f.write(in_f.read())
                        files_processed += 1
                    except UnicodeDecodeError:
                        skipped_files.append(path)
                        out_f.write("\n[ ОШИБКА: Файл бинарный или текст не в UTF-8 ]\n")
                    except Exception as e:
                        skipped_files.append(f"{path} (ошибка: {str(e)})")
                        out_f.write(f"\n[ ОШИБКА ЧТЕНИЯ: {str(e)} ]\n")

                    # Пишем подвал ровно по твоему шаблону
                    out_f.write("\n###**************************************\n")
                    out_f.write("#*закончили описание файла*************\n")
                    out_f.write("#*********************************************\n\n")

            # Предупреждение о пропущенных
            if skipped_files:
                QMessageBox.warning(
                    parent_widget,
                    "Внимание",
                    f"Некоторые файлы не удалось прочитать как текст:\n\n" + "\n".join(skipped_files[:10]) +
                    (f"\n\n... и ещё {len(skipped_files) - 10}" if len(skipped_files) > 10 else "")
                )

            QMessageBox.information(
                parent_widget,
                "Успех",
                f"Файл Mozart_Combined.txt успешно создан!\n\n"
                f"Обработано файлов: {files_processed}\n"
                f"Пропущено: {len(skipped_files)}\n"
                f"Путь: {txt_file_path}"
            )

        except Exception as e:
            QMessageBox.critical(parent_widget, "Ошибка", f"Не удалось создать TXT файл:\n{str(e)}")

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