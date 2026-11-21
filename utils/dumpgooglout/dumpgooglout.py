# путь utils/dumpgooglout/dumpgooglout.py


# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import sqlite3
import subprocess
import psutil
from PySide6.QtCore import Qt, QThread, Signal, QModelIndex, QDir
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QTreeView, QPushButton, QLineEdit, QLabel,
                               QFileDialog, QStyle, QFrame, QDialog, QTextEdit,
                               QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QCheckBox, QGroupBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================
# МОДЕЛЬ ДЕРЕВА ФАЙЛОВ
# ==========================================
class CheckableFileModel(QStandardItemModel):
    IGNORE_DIRS = {".venv", "venv", ".git", "__pycache__", ".idea", "build", "dist"}

    def __init__(self, root_path):
        super().__init__()
        self.root_path = os.path.abspath(root_path)
        self.setHorizontalHeaderLabels(["Структура проекта"])
        self._block_signals = False
        self.saved_checked_paths = set()

        if os.path.exists(self.root_path):
            self._populate_node(self.root_path, self.invisibleRootItem())
        self.itemChanged.connect(self._on_item_changed)

    def set_saved_checked_paths(self, paths):
        self.saved_checked_paths = set(paths)
        self._apply_checks_to_visible(self.invisibleRootItem())

    def _apply_checks_to_visible(self, parent_item):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                path = child.data(Qt.UserRole)
                if path in self.saved_checked_paths:
                    child.setCheckState(Qt.Checked)
                    self._update_parent_state(child)
                if child.rowCount() > 0:
                    self._apply_checks_to_visible(child)

    def _populate_node(self, current_path, parent_item):
        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            return
        dirs = [i for i in items if os.path.isdir(os.path.join(current_path, i)) and i not in self.IGNORE_DIRS]
        files = [i for i in items if os.path.isfile(os.path.join(current_path, i))]

        for name in dirs + files:
            full_path = os.path.join(current_path, name)
            is_dir = os.path.isdir(full_path)

            name_item = QStandardItem(name)
            name_item.setCheckable(True)
            name_item.setEditable(False)
            name_item.setData(full_path, Qt.UserRole)
            name_item.setData(False, Qt.UserRole + 1)

            if full_path in self.saved_checked_paths:
                name_item.setCheckState(Qt.Checked)
            else:
                name_item.setCheckState(Qt.Unchecked)

            parent_item.appendRow(name_item)

            if full_path in self.saved_checked_paths:
                self._update_parent_state(name_item)

            if is_dir:
                dummy = QStandardItem("loading...")
                dummy.setEditable(False)
                name_item.appendRow(dummy)

    def load_folder_dynamic(self, item):
        if not item or item.data(Qt.UserRole + 1) or item.text() == "loading...":
            return
        item.setData(True, Qt.UserRole + 1)
        if item.rowCount() > 0 and item.child(0).text() == "loading...":
            item.removeRow(0)

        full_path = item.data(Qt.UserRole)
        self._block_signals = True
        self._populate_node(full_path, item)

        if item.checkState() == Qt.Checked:
            self._set_children_state(item, Qt.Checked)
        self._block_signals = False

    def _on_item_changed(self, item):
        if self._block_signals:
            return
        self._block_signals = True
        self._set_children_state(item, item.checkState())
        self._update_parent_state(item)
        self._block_signals = False

    def _set_children_state(self, parent_item, state):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                child.setCheckState(state)
                if child.rowCount() > 0:
                    self._set_children_state(child, state)

    def _update_parent_state(self, item):
        parent = item.parent()
        if not parent:
            return
        all_checked, all_unchecked = True, True
        for row in range(parent.rowCount()):
            child = parent.child(row, 0)
            if child and child.text() != "loading...":
                if child.checkState() == Qt.Checked:
                    all_unchecked = False
                elif child.checkState() == Qt.Unchecked:
                    all_checked = False
                else:
                    all_checked = all_unchecked = False

        if all_checked:
            parent.setCheckState(Qt.Checked)
        elif all_unchecked:
            parent.setCheckState(Qt.Unchecked)
        else:
            parent.setCheckState(Qt.PartiallyChecked)
        self._update_parent_state(parent)

    def get_selected_files(self):
        selected_paths = []
        self._collect_files(self.invisibleRootItem(), selected_paths)
        return selected_paths

    def _collect_files(self, parent_item, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child:
                if child.text() == "loading...":
                    continue
                path = child.data(Qt.UserRole)
                if child.checkState() == Qt.Checked and os.path.isdir(path) and not child.data(Qt.UserRole + 1):
                    self.load_folder_dynamic(child)
                if child.checkState() == Qt.Checked and os.path.isfile(path):
                    paths_list.append(path)
                if child.rowCount() > 0:
                    self._collect_files(child, paths_list)

    def get_all_checked_nodes(self):
        checked_paths = []
        self._collect_all_checked(self.invisibleRootItem(), checked_paths)
        return checked_paths

    def _collect_all_checked(self, parent_item, paths_list):
        for row in range(parent_item.rowCount()):
            child = parent_item.child(row, 0)
            if child and child.text() != "loading...":
                if child.checkState() == Qt.Checked:
                    paths_list.append(child.data(Qt.UserRole))
                if child.rowCount() > 0:
                    self._collect_all_checked(child, paths_list)


# ==========================================
# МЕНЕДЖЕР НАСТРОЕК
# ==========================================
class PackDbManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standalone_injector.sqlt")

    def load_settings(self):
        if not os.path.exists(self.db_path):
            return "", [], []
        conn = None
        dump_path, checked_nodes, expanded_nodes = "", [], []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS settings (dump_path TEXT)")
            cursor.execute("SELECT dump_path FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                dump_path = row[0]

            cursor.execute("CREATE TABLE IF NOT EXISTS checked_nodes (node_path TEXT)")
            cursor.execute("SELECT node_path FROM checked_nodes")
            checked_nodes = [r[0] for r in cursor.fetchall()]

            cursor.execute("CREATE TABLE IF NOT EXISTS expanded_nodes (node_path TEXT)")
            cursor.execute("SELECT node_path FROM expanded_nodes")
            expanded_nodes = [r[0] for r in cursor.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()
        return dump_path, checked_nodes, expanded_nodes

    def save_settings(self, dump_path, checked_nodes, expanded_nodes):
        temp_path = self.db_path + ".tmp"
        conn = None
        try:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE settings (dump_path TEXT)")
            cursor.execute("CREATE TABLE checked_nodes (node_path TEXT)")
            cursor.execute("CREATE TABLE expanded_nodes (node_path TEXT)")
            cursor.execute("INSERT INTO settings VALUES (?)", (dump_path,))
            if checked_nodes:
                cursor.executemany("INSERT INTO checked_nodes VALUES (?)", [(p,) for p in checked_nodes])
            if expanded_nodes:
                cursor.executemany("INSERT INTO expanded_nodes VALUES (?)", [(p,) for p in expanded_nodes])
            conn.commit()
            conn.close()
            conn = None
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            os.rename(temp_path, self.db_path)
        except sqlite3.Error:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        finally:
            if conn:
                conn.close()


# ==========================================
# ПАРСЕР SQL ДАМПА
# ==========================================
class SqlDumpParser:
    MAX_BLOCK_SIZE = 30000

    @staticmethod
    def parse_dump_file(file_path):
        if not file_path or not os.path.exists(file_path):
            return {}
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        schemas = {}
        current_schema = "unknown_schema"
        current_block = []
        schema_regex = re.compile(r'--\s*СХЕМА:\s*([\w\d_]+)', re.IGNORECASE)
        table_regex = re.compile(r'CREATE\s+TABLE\s+([\w\d_]+)\.([\w\d_]+)', re.IGNORECASE)
        comment_regex = re.compile(r'COMMENT\s+ON\s+(?:TABLE|COLUMN)\s+([\w\d_]+)\.([\w\d_]+)', re.IGNORECASE)
        insert_regex = re.compile(r'INSERT\s+INTO\s+([\w\d_]+)\.([\w\d_]+)', re.IGNORECASE)

        def flush_block():
            nonlocal current_block
            if not current_block:
                return
            text = "".join(current_block).strip()
            if not text:
                current_block = []
                return
            if len(text) > SqlDumpParser.MAX_BLOCK_SIZE:
                chunks = [text[i:i + SqlDumpParser.MAX_BLOCK_SIZE] for i in
                          range(0, len(text), SqlDumpParser.MAX_BLOCK_SIZE)]
                schemas.setdefault(current_schema, []).extend(chunks)
            else:
                schemas.setdefault(current_schema, []).append(text)
            current_block = []

        for line in lines:
            schema_match = schema_regex.search(line)
            if schema_match:
                flush_block()
                current_schema = schema_match.group(1)
                continue
            t_match = (table_regex.search(line) or comment_regex.search(line) or insert_regex.search(line))
            if t_match:
                detected_schema = t_match.group(1)
                if detected_schema != current_schema:
                    flush_block()
                    current_schema = detected_schema
            current_block.append(line)
            if len("".join(current_block)) > SqlDumpParser.MAX_BLOCK_SIZE * 1.5:
                flush_block()
        flush_block()
        return {s: [b for b in blocks if b.strip()] for s, blocks in schemas.items() if any(b.strip() for b in blocks)}


# ==========================================
# ДЕТЕКТОР FIREFOX
# ==========================================
class FirefoxSessionDetector:
    @staticmethod
    def find_firefox_binary():
        for path in ["/snap/firefox/current/usr/lib/firefox/firefox", "/usr/lib/firefox/firefox", "/usr/bin/firefox",
                     "/usr/local/bin/firefox"]:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        try:
            res = subprocess.run(['which', 'firefox'], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def find_firefox_sessions():
        sessions = []
        seen_ports = set()
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline_list = proc.info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline_list).lower()
                    if 'firefox' not in cmdline_str and 'geckodriver' not in cmdline_str:
                        continue
                    for i, arg in enumerate(cmdline_list):
                        if '--marionette-port' in arg.lower():
                            if '=' in arg:
                                port = int(arg.split('=')[1])
                            elif i + 1 < len(cmdline_list):
                                port = int(cmdline_list[i + 1])
                            else:
                                continue
                            if port not in seen_ports:
                                seen_ports.add(port)
                                sessions.append({'pid': proc.info['pid'], 'port': port})
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                    continue
        except Exception:
            pass
        return sessions

    @staticmethod
    def classify_tab(title, url):
        t, u = title.lower(), url.lower()
        if 'gemini' in t or 'gemini' in u or 'aistudio' in u:
            return 'gemini'
        if 'deepseek' in t or 'deepseek' in u:
            return 'deepseek'
        if 'qwen' in t or 'qwen' in u or 'tongyi' in u or 'chat.qwen' in u:
            return 'qwen'
        if 'google.com' in u and ('search' in u or 'поиск' in t):
            return 'gemini'
        return 'unknown'

    @staticmethod
    def probe_all_tabs(port):
        tabs = []
        binary = FirefoxSessionDetector.find_firefox_binary()
        if not binary:
            return []
        driver = None
        try:
            options = Options()
            options.binary_location = binary
            options.set_preference("marionette.enabled", True)
            service = Service(service_args=["--marionette-port", str(port), "--connect-existing"])
            service.log_output = subprocess.DEVNULL
            driver = webdriver.Firefox(options=options, service=service)

            for handle in driver.window_handles:
                try:
                    driver.switch_to.window(handle)
                    time.sleep(0.2)
                    title = driver.title
                    url = driver.current_url

                    has_input = False
                    for xpath in ["//textarea", "//div[@role='textbox']", "//div[@contenteditable='true']"]:
                        try:
                            driver.find_element(By.XPATH, xpath)
                            has_input = True
                            break
                        except Exception:
                            continue

                    if has_input:
                        tabs.append({
                            'handle': handle, 'title': title, 'url': url, 'port': port,
                            'type': FirefoxSessionDetector.classify_tab(title, url)
                        })
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            if driver:
                try:
                    driver.service.stop()
                except Exception:
                    pass
        return tabs


# ==========================================
# ПОТОК СКАНИРОВАНИЯ ВКЛАДОК
# ==========================================
class SessionScanThread(QThread):
    tabs_found = Signal(list)
    scan_finished = Signal()
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self._stop = False

    def run(self):
        self.status_update.emit(" Поиск сессий Firefox...")
        sessions = FirefoxSessionDetector.find_firefox_sessions()

        if not sessions:
            self.status_update.emit(" Сессии Firefox не найдены")
            self.tabs_found.emit([])
            self.scan_finished.emit()
            return

        self.status_update.emit(f"🔌 Найдено {len(sessions)} сессий, сканирую вкладки...")
        all_tabs = []
        for session in sessions:
            if self._stop:
                break
            tabs = FirefoxSessionDetector.probe_all_tabs(session['port'])
            all_tabs.extend(tabs)
            self.status_update.emit(f"   Порт: {session['port']} ({len(tabs)} вкладок)")

        self.tabs_found.emit(all_tabs)
        self.status_update.emit(f"✅ Всего найдено {len(all_tabs)} вкладок")
        self.scan_finished.emit()

    def stop(self):
        self._stop = True


# ==========================================
# ДИАЛОГ ВЫБОРА ВКЛАДОК
# ==========================================
class SessionSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_tabs = {'gemini': None, 'deepseek': None, 'qwen': None}
        self.scan_thread = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Настройка вкладок ИИ")
        self.resize(1000, 550)
        layout = QVBoxLayout(self)

        self.lbl_status = QLabel("<b>Поиск сессий...</b>")
        layout.addWidget(self.lbl_status)
        layout.addWidget(QLabel("<b>Найденные вкладки Firefox. Отметьте, какой ИИ соответствует вкладка:</b>"))

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels(["Вкладка", "URL", "Порт", "Авто-тип", "Gemini", "DeepSeek", "Qwen"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tbl)

        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Сканировать")
        self.btn_ok = QPushButton("✅ Сохранить")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_refresh.clicked.connect(self.start_scan)
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_refresh)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.start_scan()

    def start_scan(self):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait(2000)

        self.tbl.setRowCount(0)
        self.btn_refresh.setEnabled(False)
        self.btn_ok.setEnabled(False)
        self.lbl_status.setText("<b>🔍 Сканирование...</b>")

        self.scan_thread = SessionScanThread()
        self.scan_thread.tabs_found.connect(self.on_tabs_found)
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.status_update.connect(self.lbl_status.setText)
        self.scan_thread.start()

    def on_tabs_found(self, all_tabs):
        self.tbl.setRowCount(len(all_tabs))
        for r, tab in enumerate(all_tabs):
            self.tbl.setItem(r, 0, QTableWidgetItem(tab['title'][:50]))
            self.tbl.item(r, 0).setData(Qt.UserRole, tab)
            self.tbl.setItem(r, 1, QTableWidgetItem(tab['url'][:60]))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(tab['port'])))
            self.tbl.setItem(r, 3, QTableWidgetItem(tab['type'].upper()))

            for c, ai in enumerate(['gemini', 'deepseek', 'qwen'], 4):
                cb = QCheckBox()
                if tab['type'] == ai:
                    cb.setChecked(True)
                cb.stateChanged.connect(lambda state, row=r, col=c: self.enforce_rules(row, col))
                self.tbl.setCellWidget(r, c, cb)

    def on_scan_finished(self):
        self.btn_refresh.setEnabled(True)
        self.btn_ok.setEnabled(True)

    def enforce_rules(self, row, col):
        for c in range(4, 7):
            if c != col:
                w = self.tbl.cellWidget(row, c)
                if w and w.isChecked():
                    w.blockSignals(True)
                    w.setChecked(False)
                    w.blockSignals(False)

        w = self.tbl.cellWidget(row, col)
        if w and w.isChecked():
            for r in range(self.tbl.rowCount()):
                if r != row:
                    w2 = self.tbl.cellWidget(r, col)
                    if w2 and w2.isChecked():
                        w2.blockSignals(True)
                        w2.setChecked(False)
                        w2.blockSignals(False)

    def accept_selection(self):
        self.selected_tabs = {'gemini': None, 'deepseek': None, 'qwen': None}
        for r in range(self.tbl.rowCount()):
            for c, ai in enumerate(['gemini', 'deepseek', 'qwen'], 4):
                w = self.tbl.cellWidget(r, c)
                if w and w.isChecked():
                    item = self.tbl.item(r, 0)
                    if item and item.data(Qt.UserRole):
                        self.selected_tabs[ai] = item.data(Qt.UserRole)
        super().accept()


# ==========================================
# ПОТОК ЗАГРУЗКИ (С ИСПРАВЛЕННОЙ ЛОГИКОЙ ПЕРЕКЛЮЧЕНИЯ)
# ==========================================
class MultiAIUploadThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)

    def __init__(self, files, dump_path, root, targets, active_ais):
        super().__init__()
        self.files = files
        self.dump_path = dump_path
        self.root = root
        self.targets = targets
        self.active_ais = active_ais
        self._stop = False

    def _chunk_text(self, text, ai_name):
        if ai_name == 'qwen' or len(text) <= 30000:
            return [text]
        chunks, curr, size = [], [], 0
        for line in text.split('\n'):
            if size + len(line) > 30000 and curr:
                chunks.append('\n'.join(curr))
                curr, size = [line], len(line)
            else:
                curr.append(line)
                size += len(line)
        if curr:
            chunks.append('\n'.join(curr))
        return chunks

    def _send_and_wait(self, driver, tab, text):
        """Отправляет текст, предварительно найдя актуальный handle вкладки по URL."""
        try:
            # 1. НАДЕЖНЫЙ ПОИСК ВКЛАДКИ ПО URL (защита от NoSuchWindowError)
            target_handle = None
            current_handles = driver.window_handles

            for handle in current_handles:
                try:
                    driver.switch_to.window(handle)
                    # Сравниваем URL из сохраненной информации с текущим URL вкладки
                    if driver.current_url == tab['url']:
                        target_handle = handle
                        break
                except Exception:
                    continue

            if not target_handle:
                self.log_signal.emit(f"   ⚠️ Вкладка '{tab['title']}' не найдена (возможно закрыта). Пропуск.")
                return

            # 2. Работа с найденной активной вкладкой
            wait = WebDriverWait(driver, 10)
            field = wait.until(EC.presence_of_element_located((
                By.XPATH, "//textarea | //div[@role='textbox'] | //div[@contenteditable='true']"
            )))

            # JS-инъекция текста (обходит ElementNotInteractable)
            script = """
            const el = arguments[0];
            const txt = arguments[1];
            el.focus();
            if (el.tagName.toLowerCase() === 'textarea' || el.tagName.toLowerCase() === 'input') {
                el.value = txt;
            } else {
                el.innerText = txt;
            }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            """
            driver.execute_script(script, field, text)
            time.sleep(0.5)

            # Клик по кнопке отправки через JS
            try:
                btn = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@aria-label,'Send') or contains(@aria-label,'Отправить') or @type='submit' or @data-testid='send-button']"
                )))
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                field.send_keys(Keys.RETURN)

            # Ожидание ответа ИИ (стабилизация длины текста)
            time.sleep(2)
            last_len, stable_count = 0, 0
            for _ in range(15):
                if self._stop:
                    return
                try:
                    resp = driver.find_elements(By.XPATH, (
                        "//div[@data-message-author-role='assistant'] | "
                        "//div[contains(@class,'response')] | "
                        "//div[contains(@class,'answer')] | "
                        "//article | //div[contains(@class,'message-content')]"
                    ))
                    if resp:
                        txt = resp[-1].text
                        if len(txt) > 20 and "Прими файл" not in txt and "Подтверди" not in txt:
                            if len(txt) == last_len and last_len > 0:
                                stable_count += 1
                                if stable_count >= 2:
                                    return
                            else:
                                last_len = len(txt)
                                stable_count = 0
                except Exception:
                    pass
                time.sleep(1)

        except Exception as e:
            self.log_signal.emit(f"   ❌ Ошибка отправки: {e}")

    def run(self):
        drivers = {}
        try:
            ports = set(tab['port'] for tab in self.targets.values() if tab)
            binary = FirefoxSessionDetector.find_firefox_binary()
            if not binary:
                self.finished_signal.emit(False, "Firefox не найден!")
                return

            for port in ports:
                try:
                    opts = Options()
                    opts.binary_location = binary
                    opts.set_preference("marionette.enabled", True)
                    svc = Service(service_args=["--marionette-port", str(port), "--connect-existing"])
                    svc.log_output = subprocess.DEVNULL
                    drivers[port] = webdriver.Firefox(options=opts, service=svc)
                    self.log_signal.emit(f" Подключено к порту {port}")
                except Exception as e:
                    self.log_signal.emit(f"❌ Не удалось подключиться к порту {port}: {e}")

            if not drivers:
                self.finished_signal.emit(False, "Нет активных подключений к Firefox!")
                return

            total = len(self.files)
            if self.dump_path and os.path.exists(self.dump_path):
                schemas = SqlDumpParser.parse_dump_file(self.dump_path)
                total += sum(len(blocks) for blocks in schemas.values())

            step = 0
            self.progress_signal.emit(0)

            for fpath in self.files:
                if self._stop:
                    break
                rel = os.path.relpath(fpath, self.root)
                self.log_signal.emit(f"📁 {rel}")
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    self.log_signal.emit(f"   Не удалось прочитать: {e}")
                    step += 1
                    continue

                for ai in self.active_ais:
                    tab = self.targets.get(ai)
                    if not tab or tab['port'] not in drivers:
                        continue
                    self.log_signal.emit(f"  → {ai.upper()}")
                    chunks = self._chunk_text(content, ai)
                    for i, chunk in enumerate(chunks):
                        if self._stop:
                            break
                        header = f"Файл {rel} (Часть {i + 1}/{len(chunks)}):\n" if len(chunks) > 1 else f"Файл {rel}:\n"
                        self._send_and_wait(drivers[tab['port']], tab, f"{header}```\n{chunk}\n```\nОтветь: Принято")
                step += 1
                self.progress_signal.emit(step)

            if self.dump_path and os.path.exists(self.dump_path) and not self._stop:
                self.log_signal.emit("️ Дамп БД")
                schemas = SqlDumpParser.parse_dump_file(self.dump_path)
                for sname, blocks in schemas.items():
                    for i, block in enumerate(blocks):
                        if self._stop:
                            break
                        for ai in self.active_ais:
                            tab = self.targets.get(ai)
                            if not tab or tab['port'] not in drivers:
                                continue
                            self.log_signal.emit(f"  → {ai.upper()} [{sname}] {i + 1}/{len(blocks)}")
                            self._send_and_wait(drivers[tab['port']], tab,
                                                f"Схема {sname} (Часть {i + 1}):\n```sql\n{block}\n```\nОтветь: Принято")
                        step += 1
                        self.progress_signal.emit(step)

            self.finished_signal.emit(True, "Инъекция завершена!")
        except Exception as e:
            self.finished_signal.emit(False, f"Ошибка: {str(e)}")
        finally:
            for d in drivers.values():
                try:
                    d.service.stop()
                except Exception:
                    pass

    def stop(self):
        self._stop = True


# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class StandalonePackerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.project_root = os.path.expanduser("~/Documents/configurate")
        if not os.path.exists(self.project_root):
            self.project_root = os.path.expanduser("~")

        self.setWindowTitle("Инжектор: Qwen / Gemini / DeepSeek")
        self.resize(1100, 650)
        self.db_mgr = PackDbManager()
        self.targets = {'gemini': None, 'deepseek': None, 'qwen': None}
        self.thread = None
        self.setup_ui()
        self.load_state()

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.lbl_root = QLabel(f"<b>Проект:</b><br><small>{self.project_root}</small>")
        lv.addWidget(self.lbl_root)

        btn_change_root = QPushButton("📂 Выбрать папку проекта")
        btn_change_root.clicked.connect(self._select_project_root)
        lv.addWidget(btn_change_root)

        self.tree = QTreeView()
        self.model = CheckableFileModel(self.project_root)
        self.tree.setModel(self.model)
        self.tree.expanded.connect(lambda idx: self.model.load_folder_dynamic(self.model.itemFromIndex(idx)))
        lv.addWidget(self.tree)
        main.addWidget(left, stretch=6)

        main.addWidget(QFrame(frameShape=QFrame.VLine))

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)

        rv.addWidget(QLabel("<b>SQL Дамп:</b>"))
        dr = QHBoxLayout()
        self.edt_dump = QLineEdit()
        self.edt_dump.setReadOnly(True)
        self.edt_dump.setPlaceholderText("Укажите файл дампа...")
        btn_d = QPushButton()
        btn_d.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        btn_d.clicked.connect(self._browse_dump)
        dr.addWidget(self.edt_dump)
        dr.addWidget(btn_d)
        rv.addLayout(dr)

        grp = QGroupBox("<b>Куда отправляем данные?</b>")
        gl = QHBoxLayout(grp)
        self.chk_gemini = QCheckBox("Gemini")
        self.chk_gemini.setChecked(True)
        self.chk_deepseek = QCheckBox("DeepSeek")
        self.chk_deepseek.setChecked(True)
        self.chk_qwen = QCheckBox("Qwen")
        self.chk_qwen.setChecked(True)
        gl.addWidget(self.chk_gemini)
        gl.addWidget(self.chk_deepseek)
        gl.addWidget(self.chk_qwen)
        rv.addWidget(grp)

        btn_map = QPushButton("🔍 Настроить вкладки Firefox (Маппинг)")
        btn_map.setStyleSheet("background:#3498db; color:white; height:30px;")
        btn_map.clicked.connect(self.map_tabs)
        rv.addWidget(btn_map)
        self.lbl_map_status = QLabel("<i>Вкладки не назначены</i>")
        rv.addWidget(self.lbl_map_status)

        rv.addWidget(QLabel("<b>Прогресс:</b>"))
        self.pb = QProgressBar()
        self.pb.setValue(0)
        rv.addWidget(self.pb)
        rv.addWidget(QLabel("<b>Журнал:</b>"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#1e1e1e; color:#a9b7c6; font-family:monospace;")
        rv.addWidget(self.log)

        br = QHBoxLayout()
        self.btn_start = QPushButton("⚡ ЗАПУСТИТЬ")
        self.btn_start.setStyleSheet("background:#27ae60; color:white; font-weight:bold; height:40px;")
        self.btn_abort = QPushButton("Стоп")
        self.btn_abort.setEnabled(False)
        self.btn_abort.setStyleSheet("background:#c0392b; color:white; height:40px;")
        self.btn_start.clicked.connect(self.start_injection)
        self.btn_abort.clicked.connect(self.abort_injection)
        br.addWidget(self.btn_start)
        br.addWidget(self.btn_abort)
        rv.addLayout(br)

        main.addWidget(right, stretch=5)

    def _select_project_root(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Выбрать папку проекта", self.project_root)
        if dir_path:
            self.project_root = dir_path
            self.lbl_root.setText(f"<b>Проект:</b><br><small>{self.project_root}</small>")
            self.model = CheckableFileModel(self.project_root)
            self.tree.setModel(self.model)

    def _browse_dump(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть дамп", QDir.homePath(), "SQL файлы (*.sql *.txt)")
        if path:
            self.edt_dump.setText(path)

    def map_tabs(self):
        dlg = SessionSelectorDialog(self)
        if dlg.exec():
            self.targets = dlg.selected_tabs
            active = [k.upper() for k, v in self.targets.items() if v]
            if active:
                self.lbl_map_status.setText(f"<b>Назначено:</b> {', '.join(active)}")
            else:
                self.lbl_map_status.setText("<i>Вкладки не назначены</i>")

    def start_injection(self):
        active_ais = []
        if self.chk_gemini.isChecked(): active_ais.append('gemini')
        if self.chk_deepseek.isChecked(): active_ais.append('deepseek')
        if self.chk_qwen.isChecked(): active_ais.append('qwen')

        if not active_ais:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы один ИИ!")
            return
        if not any(self.targets.get(ai) for ai in active_ais):
            QMessageBox.warning(self, "Внимание", "Нажмите 'Настроить вкладки' и назначьте вкладки для выбранных ИИ!")
            return

        files = self.model.get_selected_files()
        dump = self.edt_dump.text().strip()
        if not files and not dump:
            QMessageBox.warning(self, "Внимание", "Нет файлов или дампа!")
            return

        self.log.clear()
        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)

        total = len(files)
        if dump and os.path.exists(dump):
            schemas = SqlDumpParser.parse_dump_file(dump)
            total += sum(len(blocks) for blocks in schemas.values())
        self.pb.setMaximum(max(total, 1))
        self.pb.setValue(0)

        self.thread = MultiAIUploadThread(files, dump, self.project_root, self.targets, active_ais)
        self.thread.log_signal.connect(self.log.append)
        self.thread.progress_signal.connect(self.pb.setValue)
        self.thread.finished_signal.connect(self._on_finished)
        self.thread.start()

    def _on_finished(self, ok, msg):
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        if ok:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def abort_injection(self):
        if self.thread and self.thread.isRunning():
            self.log.append("🛑 Остановка...")
            self.thread.stop()

    def load_state(self):
        dump_path, checked_nodes, expanded_nodes = self.db_mgr.load_settings()
        if dump_path:
            self.edt_dump.setText(dump_path)
        if checked_nodes:
            valid_nodes = [p for p in checked_nodes if os.path.exists(p)]
            self.model.set_saved_checked_paths(valid_nodes)

    def closeEvent(self, event):
        self.db_mgr.save_settings(
            self.edt_dump.text(),
            self.model.get_all_checked_nodes(),
            []
        )
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = StandalonePackerWidget()
    w.show()
    sys.exit(app.exec())