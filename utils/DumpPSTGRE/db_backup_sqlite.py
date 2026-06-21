# utils/db_backup_sqlite.py
# -*- coding: utf-8 -*-

import os
import sqlite3


class BackupDbManager:
    """Компонент автономного сохранения состояния интерфейса бэкапа в локальную SQLite БД."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_backup_settings.sqlt")

    def load_settings(self):
        """Чтение параметров из базы данных. Возвращает (target_path, file_name, checked_nodes)."""
        if not os.path.exists(self.db_path):
            return "", "mozart_dump.sql", []

        conn = None
        target_path, file_name = "", "mozart_dump.sql"
        checked_nodes = []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Читаем строковые параметры формы
            cursor.execute("SELECT target_path, file_name FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                target_path, file_name = row[0], row[1]

            # Читаем отмеченные чекбоксы дерева объектов
            cursor.execute("SELECT node_path FROM checked_nodes")
            checked_nodes = [r[0] for r in cursor.fetchall()]

        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

        return target_path, file_name, checked_nodes

    def save_settings(self, target_path, file_name, checked_nodes):
        """Аппаратное пересоздание БД и фиксация слепка интерфейса в SQLite."""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                return

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Создаем чистую структуру таблиц
            cursor.execute("""
                CREATE TABLE settings (
                    target_path TEXT,
                    file_name TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE checked_nodes (
                    node_path TEXT
                )
            """)

            # Сохраняем текстовые поля
            cursor.execute("INSERT INTO settings VALUES (?, ?)", (target_path, file_name))

            # Сохраняем все прочеканные узлы дерева объектов
            if checked_nodes:
                cursor.executemany("INSERT INTO checked_nodes VALUES (?)", [(p,) for p in checked_nodes])

            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()
