# utils/contextMozart/state_store.py
# -*- coding: utf-8 -*-
"""SQLite-хранилище состояния GUI contextMozart."""

import os
import sqlite3


class ContextStateStore:
    """Хранит: output_dir, checked_nodes, expanded_nodes."""

    def __init__(self):
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "context_packer.sqlt"
        )

    def load(self):
        if not os.path.exists(self.db_path):
            return "", [], []
        conn = None
        output_dir, checked, expanded = "", [], []
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS settings (output_dir TEXT)")
            cur.execute("SELECT output_dir FROM settings LIMIT 1")
            row = cur.fetchone()
            if row:
                output_dir = row[0] or ""

            cur.execute("CREATE TABLE IF NOT EXISTS checked_nodes (path TEXT)")
            checked = [r[0] for r in cur.execute("SELECT path FROM checked_nodes")]

            cur.execute("CREATE TABLE IF NOT EXISTS expanded_nodes (path TEXT)")
            expanded = [r[0] for r in cur.execute("SELECT path FROM expanded_nodes")]
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()
        return output_dir, checked, expanded

    def save(self, output_dir, checked, expanded):
        tmp = self.db_path + ".tmp"
        conn = None
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            cur.execute("CREATE TABLE settings (output_dir TEXT)")
            cur.execute("CREATE TABLE checked_nodes (path TEXT)")
            cur.execute("CREATE TABLE expanded_nodes (path TEXT)")
            cur.execute("INSERT INTO settings VALUES (?)", (output_dir,))
            if checked:
                cur.executemany("INSERT INTO checked_nodes VALUES (?)", [(p,) for p in checked])
            if expanded:
                cur.executemany("INSERT INTO expanded_nodes VALUES (?)", [(p,) for p in expanded])
            conn.commit()
            conn.close()
            conn = None
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            os.rename(tmp, self.db_path)
        except sqlite3.Error:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        finally:
            if conn:
                conn.close()