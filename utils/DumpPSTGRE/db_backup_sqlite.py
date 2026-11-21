# utils/db_backup_sqlite.py
# -- coding: utf-8 --
import os
import sqlite3


class BackupDbManager:
    """Компонент автономного сохранения состояния интерфейса бэкапа в локальную SQLite БД."""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_backup_settings.sqlt")

    def load_settings(self):
        if not os.path.exists(self.db_path):
            return "", "mozart_dump.txt", []
        conn = None
        target_path, file_name = "", "mozart_dump.txt"
        checked_nodes = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT target_path, file_name FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                target_path, file_name = row[0], row[1]
            cursor.execute("SELECT node_path FROM checked_nodes ORDER BY node_path")
            checked_nodes = [r[0] for r in cursor.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()
        return target_path, file_name, checked_nodes

    def save_settings(self, target_path, file_name, checked_nodes):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                return
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE settings (target_path TEXT, file_name TEXT)")
            cursor.execute("CREATE TABLE checked_nodes (node_path TEXT PRIMARY KEY)")
            cursor.execute("INSERT INTO settings VALUES (?, ?)", (target_path, file_name))
            if checked_nodes:
                cursor.executemany("INSERT OR REPLACE INTO checked_nodes VALUES (?)", [(p,) for p in checked_nodes])
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

    def remove_nodes(self, paths_to_remove):
        """Удаляет указанные пути из БД. Используется для массового сброса."""
        if not paths_to_remove or not os.path.exists(self.db_path):
            return
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in paths_to_remove)
            cursor.execute(f"DELETE FROM checked_nodes WHERE node_path IN ({placeholders})", paths_to_remove)
            conn.commit()
        except sqlite3.Error as e:
            print(f"[SQLite Remove Error] {e}")
        finally:
            if conn:
                conn.close()