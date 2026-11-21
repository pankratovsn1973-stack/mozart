# utils/contextMozart/context_packer_gui.py
# -*- coding: utf-8 -*-
"""
GUI-сборщик контекста Mozart ERP для ИИ.
Окно с деревом проекта (чекбоксы), полем вывода и кнопками генерации.
"""
# utils/contextMozart/context_packer_gui.py
# -*- coding: utf-8 -*-
"""
GUI-сборщик контекста Mozart ERP для ИИ.
Окно с деревом проекта (чекбоксы), полем вывода и кнопками генерации.
"""

import os
import sys
import traceback

# --- Умный импорт: работает и как модуль, и как скрипт ---
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QPushButton, QLineEdit, QLabel,
    QFileDialog, QStyle, QFrame, QTextEdit,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal

# Импорты без точки — работают при запуске как скрипт
from checkable_model import CheckableContextModel
from state_store import ContextStateStore


DEFAULT_ROOT = "/home/sergey/Documents/configurate"
DEFAULT_OUTPUT = os.path.join(_THIS_DIR, "output")


# ============================================================
# ПОТОК ГЕНЕРАЦИИ (чтобы GUI не подвисал)
# ============================================================

class GenerationWorker(QThread):
    """Выполняет генерацию в фоне и стримит лог в GUI."""

    log = Signal(str)
    finished_ok = Signal(str)
    finished_err = Signal(str)

    def __init__(self, task: str, config):
        super().__init__()
        self.task = task        # 'md', 'json', 'db', 'all'
        self.config = config

    def run(self):
        try:
            if self.task in ('md', 'json', 'all'):
                self._run_code()
            if self.task in ('db', 'all'):
                self._run_db()
            self.finished_ok.emit("Готово.")
        except Exception as e:
            self.log.emit(traceback.format_exc())
            self.finished_err.emit(str(e))

    # --------------------------------------------------------
    def _run_code(self):
        from code_context_generator import (
            FileScanner, PythonFileParser, ReferenceLinker,
            MarkdownRenderer, JsonRenderer,
        )

        self.log.emit(f"[contextMozart] Корень: {self.config.root}")
        scanner = FileScanner(self.config)
        files = scanner.scan()
        self.log.emit(f"[contextMozart] Найдено .py файлов: {len(files)}")

        if not files:
            self.log.emit("[contextMozart] ⚠️ Нечего сканировать — отметьте файлы или снимите выбор.")
            return

        parser = PythonFileParser(self.config)
        cards = []
        errors = 0
        for i, rel in enumerate(files, 1):
            if i % 20 == 0 or i == len(files):
                self.log.emit(f"[contextMozart] Парсинг {i}/{len(files)}…")
            card = parser.parse(rel)
            if card.get('error'):
                errors += 1
            cards.append(card)
        if errors:
            self.log.emit(f"[contextMozart] ⚠️ Ошибок парсинга: {errors}")

        self.log.emit("[contextMozart] Построение обратных связей…")
        linker = ReferenceLinker(self.config, cards)
        linker.link()

        os.makedirs(self.config.output_dir, exist_ok=True)

        if self.task in ('md', 'all'):
            path = os.path.join(self.config.output_dir, 'Mozart_context.md')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(MarkdownRenderer(self.config, cards, linker).render())
            self.log.emit(f"[contextMozart] ✅ {path} ({os.path.getsize(path)/1024:.1f} KB)")

        if self.task in ('json', 'all'):
            import json
            path = os.path.join(self.config.output_dir, 'Mozart_context.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(
                    JsonRenderer(self.config, cards, linker).render(),
                    f, ensure_ascii=False, indent=2
                )
            self.log.emit(f"[contextMozart] ✅ {path} ({os.path.getsize(path)/1024:.1f} KB)")

    # --------------------------------------------------------
    def _run_db(self):
        from db_context_generator import main as db_main
        path = os.path.join(self.config.output_dir, 'Mozart_db_context.md')
        os.makedirs(self.config.output_dir, exist_ok=True)
        rc = db_main(["--output", path, "--root", self.config.root])
        if rc == 0:
            self.log.emit(f"[contextMozart] ✅ {path} ({os.path.getsize(path)/1024:.1f} KB)")
        else:
            self.log.emit("[contextMozart] ⚠️ Генерация БД завершилась с ошибкой.")


# ============================================================
# ГЛАВНОЕ ОКНО
# ============================================================

class ContextPackerWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.project_root = DEFAULT_ROOT
        self.store = ContextStateStore()
        self.worker = None

        self.setWindowTitle("Сборщик контекста Mozart ERP — contextMozart")
        self.resize(1100, 720)

        self._setup_ui()
        self._load_state()

    # --------------------------------------------------------
    def _setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        # --- ЛЕВАЯ ПАНЕЛЬ: дерево проекта ---
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)

        self.lbl_root = QLabel(f"<b>Проект:</b><br><small>{self.project_root}</small>")
        lv.addWidget(self.lbl_root)

        self.btn_change_root = QPushButton("📂 Выбрать корень проекта")
        self.btn_change_root.clicked.connect(self._select_root)
        lv.addWidget(self.btn_change_root)

        self.tree = QTreeView()
        self.model = CheckableContextModel(self.project_root)
        self.tree.setModel(self.model)
        self.tree.expanded.connect(
            lambda idx: self.model.load_folder_dynamic(self.model.itemFromIndex(idx))
        )
        lv.addWidget(self.tree)

        main.addWidget(left, stretch=6)

        # Разделитель
        main.addWidget(QFrame(frameShape=QFrame.VLine))

        # --- ПРАВАЯ ПАНЕЛЬ ---
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(10)

        # Каталог вывода
        rv.addWidget(QLabel("<b>Каталог вывода:</b>"))
        out_row = QHBoxLayout()
        self.edt_output = QLineEdit(DEFAULT_OUTPUT)
        out_row.addWidget(self.edt_output)
        btn_out = QPushButton()
        btn_out.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        btn_out.clicked.connect(self._select_output)
        out_row.addWidget(btn_out)
        rv.addLayout(out_row)

        # Группа «Генерация»
        gen_group = QGroupBox("<b>Генерация карты</b>")
        gl = QVBoxLayout(gen_group)

        self.btn_gen_md = QPushButton("📄 Карта кода (.md)")
        self.btn_gen_md.clicked.connect(lambda: self._start('md'))
        gl.addWidget(self.btn_gen_md)

        self.btn_gen_json = QPushButton("🔧 Карта кода (.json)")
        self.btn_gen_json.clicked.connect(lambda: self._start('json'))
        gl.addWidget(self.btn_gen_json)

        self.btn_gen_db = QPushButton("🗄️ Карта БД (.md)")
        self.btn_gen_db.clicked.connect(lambda: self._start('db'))
        gl.addWidget(self.btn_gen_db)

        self.btn_gen_all = QPushButton("📦 Сгенерировать всё (код + БД)")
        self.btn_gen_all.setStyleSheet(
            "background:#27ae60; color:white; font-weight:bold; height:34px;"
        )
        self.btn_gen_all.clicked.connect(lambda: self._start('all'))
        gl.addWidget(self.btn_gen_all)

        rv.addWidget(gen_group)

        # Дерево выбора — предупреждение
        hint = QLabel(
            "<i>Если в дереве ничего не отмечено — сканируется весь проект "
            "с учётом встроенных исключений.</i>"
        )
        hint.setWordWrap(True)
        rv.addWidget(hint)

        # Лог
        rv.addWidget(QLabel("<b>Журнал:</b>"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet(
            "background:#1e1e1e; color:#a9b7c6; "
            "font-family:'Courier New',monospace;"
        )
        rv.addWidget(self.log, 1)

        main.addWidget(right, stretch=5)

    # --------------------------------------------------------
    def _load_state(self):
        out, checked, expanded = self.store.load()
        if out:
            self.edt_output.setText(out)
        if checked:
            valid = [p for p in checked if os.path.exists(p)]
            self.model.set_saved_checked_paths(valid)
        # Восстановление раскрытых узлов — простой проход
        if expanded:
            self._restore_expanded(set(expanded))

    def _restore_expanded(self, expanded_set):
        # Один проход: раскрываем всё, что нужно, на верхнем уровне
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item:
                self._expand_recursive(item, expanded_set)

    def _expand_recursive(self, item, expanded_set):
        path = item.data(Qt.UserRole)
        if path in expanded_set:
            self.model.load_folder_dynamic(item)
            idx = self.model.indexFromItem(item)
            self.tree.setExpanded(idx, True)
        for r in range(item.rowCount()):
            child = item.child(r, 0)
            if child and child.text() != "loading...":
                self._expand_recursive(child, expanded_set)

    # --------------------------------------------------------
    def _select_root(self):
        d = QFileDialog.getExistingDirectory(
            self, "Выберите корень проекта", self.project_root,
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        )
        if d:
            self.project_root = d
            self.lbl_root.setText(f"<b>Проект:</b><br><small>{d}</small>")
            self.model = CheckableContextModel(d)
            self.tree.setModel(self.model)

    def _select_output(self):
        d = QFileDialog.getExistingDirectory(
            self, "Каталог вывода", self.edt_output.text(),
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        )
        if d:
            self.edt_output.setText(d)

    # --------------------------------------------------------
    def _start(self, task: str):
        from code_context_generator import ContextConfig, DEFAULT_EXCLUDE

        output = self.edt_output.text().strip()
        if not output:
            QMessageBox.warning(self, "Внимание", "Укажите каталог вывода!")
            return

        selected = self.model.get_selected_py_files()
        only_files = selected if selected else None

        if only_files is not None:
            self.log.append(
                f"[GUI] Режим: только выбранные файлы ({len(only_files)} шт.)"
            )
        else:
            self.log.append("[GUI] Режим: весь проект (с исключениями)")

        config = ContextConfig(
            root=self.project_root,
            output_dir=output,
            exclude=set(DEFAULT_EXCLUDE),
            only_files=only_files,
        )

        # Блокируем кнопки
        for b in (self.btn_gen_md, self.btn_gen_json,
                  self.btn_gen_db, self.btn_gen_all):
            b.setEnabled(False)

        self.worker = GenerationWorker(task, config)
        self.worker.log.connect(self.log.append)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.finished_err.connect(self._on_err)
        self.worker.start()

    def _on_done(self, msg: str):
        self.log.append(f"[GUI] ✅ {msg}")
        for b in (self.btn_gen_md, self.btn_gen_json,
                  self.btn_gen_db, self.btn_gen_all):
            b.setEnabled(True)

    def _on_err(self, msg: str):
        self.log.append(f"[GUI] ❌ Ошибка: {msg}")
        QMessageBox.critical(self, "Ошибка", msg)
        for b in (self.btn_gen_md, self.btn_gen_json,
                  self.btn_gen_db, self.btn_gen_all):
            b.setEnabled(True)

    # --------------------------------------------------------
    def closeEvent(self, event):
        out = self.edt_output.text().strip()
        checked = self.model.get_all_checked_nodes()
        expanded = self._collect_expanded()
        self.store.save(out, checked, expanded)
        event.accept()

    def _collect_expanded(self):
        result = []
        def walk(item):
            path = item.data(Qt.UserRole)
            idx = self.model.indexFromItem(item)
            if self.tree.isExpanded(idx):
                result.append(path)
            for r in range(item.rowCount()):
                child = item.child(r, 0)
                if child and child.text() != "loading...":
                    walk(child)
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item:
                walk(item)
        return result


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ContextPackerWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())