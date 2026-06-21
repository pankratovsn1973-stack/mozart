# utils/db_manager.py
# -*- coding: utf-8 -*-

import os
import sqlite3


class PackDbManager:
    """Изолированный компонент сохранения состояния интерфейса в локальную SQLite БД."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_packer.sqlt")

    def load_settings(self):
        """Чтение параметров из базы данных."""
        if not os.path.exists(self.db_path):
            return "", "configurate_package", [], []

        conn = None
        target_path, folder_name = "", "configurate_package"
        checked_nodes, expanded_nodes = [], []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT target_path, folder_name FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                target_path, folder_name = row[0], row[1]

            cursor.execute("SELECT node_path FROM checked_nodes")
            checked_nodes = [r[0] for r in cursor.fetchall()]

            cursor.execute("SELECT node_path FROM expanded_nodes")
            expanded_nodes = [r[0] for r in cursor.fetchall()]

        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

        return target_path, folder_name, checked_nodes, expanded_nodes

    def save_settings(self, target_path, folder_name, checked_nodes, expanded_nodes):
        """Аппаратная перезапись файла БД и фиксация всех состояний."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                return

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE settings (target_path TEXT, folder_name TEXT)")
            cursor.execute("CREATE TABLE checked_nodes (node_path TEXT)")
            cursor.execute("CREATE TABLE expanded_nodes (node_path TEXT)")

            cursor.execute("INSERT INTO settings VALUES (?, ?)", (target_path, folder_name))

            # ИСПРАВЛЕНО: Убран мусор 'Nar', синтаксис полностью валиден
            if checked_nodes:
                cursor.executemany("INSERT INTO checked_nodes VALUES (?)", [(p,) for p in checked_nodes])

            if expanded_nodes:
                cursor.executemany("INSERT INTO expanded_nodes VALUES (?)", [(p,) for p in expanded_nodes])

            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()
