# mozart_import/gui/progress_dialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QPushButton, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from lang.local_translator import LocalTranslator


class ImportProgressDialog(QDialog):
    """Диалог отображения прогресса импорта с двумя шкалами."""

    def __init__(self, total_tables: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translator.tr("title_import_data"))
        self.setMinimumWidth(500)
        self.setModal(True)

        self.total_tables = total_tables
        self.current_table_index = 0
        self.current_table_records = 0
        self.current_table_processed = 0
        self.cancelled = False

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Информация о текущей таблице
        self.table_label = QLabel("Подготовка к импорту...")
        self.table_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.table_label)

        # Общая шкала прогресса (по таблицам)
        layout.addWidget(QLabel("Общий прогресс:"))
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, self.total_tables)
        self.total_progress.setValue(0)
        self.total_progress.setFormat("%v из %m таблиц")
        layout.addWidget(self.total_progress)

        layout.addSpacing(10)

        # Шкала прогресса текущей таблицы (по записям)
        layout.addWidget(QLabel("Импорт текущей таблицы:"))
        self.table_progress = QProgressBar()
        self.table_progress.setRange(0, 100)
        self.table_progress.setValue(0)
        self.table_progress.setFormat("%p%")
        layout.addWidget(self.table_progress)

        # Дополнительная информация
        self.info_label = QLabel("Обработано записей: 0")
        layout.addWidget(self.info_label)

        # Кнопка отмены
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Применяем стили
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #999;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
            QLabel {
                margin-top: 5px;
            }
        """)

    def _on_cancel(self):
        self.cancelled = True
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Отмена...")

    def start_table(self, table_name: str, total_records: int = 0):
        """Начать импорт новой таблицы."""
        self.current_table_index += 1
        self.current_table_records = total_records
        self.current_table_processed = 0

        self.table_label.setText(f"Импорт таблицы: {table_name}")
        self.total_progress.setValue(self.current_table_index)

        if total_records > 0:
            self.table_progress.setRange(0, total_records)
            self.table_progress.setFormat("%v из %m записей")
        else:
            self.table_progress.setRange(0, 100)
            self.table_progress.setFormat("%p%")

        self.table_progress.setValue(0)
        self.info_label.setText(f"Обработано записей: 0")
        QApplication.processEvents()

    def update_table_progress(self, processed: int, total: int = None):
        """Обновить прогресс текущей таблицы."""
        if total is not None:
            self.current_table_records = total
            self.table_progress.setRange(0, total)
            self.table_progress.setFormat("%v из %m записей")

        self.current_table_processed = processed
        self.table_progress.setValue(processed)
        self.info_label.setText(
            f"Обработано записей: {processed} / {self.current_table_records if self.current_table_records > 0 else '?'}")
        QApplication.processEvents()

    def finish_table(self, inserted: int, updated: int, errors: int, skipped: int = 0):
        """Завершить импорт текущей таблицы с отображением статистики."""
        stats = f"Добавлено: {inserted}, Обновлено: {updated}, Ошибок: {errors}"
        if skipped > 0:
            stats += f", Пропущено: {skipped}"
        self.info_label.setText(stats)
        QApplication.processEvents()

    def finish_all(self):
        """Завершить весь импорт."""
        self.table_label.setText("Импорт завершён!")
        self.table_progress.setValue(self.table_progress.maximum())
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Закрыть")
        QApplication.processEvents()

    def is_cancelled(self) -> bool:
        return self.cancelled


class ImportWorker(QThread):
    """Поток для выполнения импорта с обратной связью по прогрессу."""

    progress_table_start = Signal(str, int)  # (table_name, total_records)
    progress_table_update = Signal(int, int)  # (processed, total)
    progress_table_finish = Signal(int, int, int, int)  # (inserted, updated, errors, skipped)
    progress_all_finish = Signal(dict)  # общая статистика
    error_occurred = Signal(str)

    def __init__(self, orchestrator, profile):
        super().__init__()
        self.orchestrator = orchestrator
        self.profile = profile
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            # Здесь нужно модифицировать orchestrator.run() чтобы он принимал колбэки
            # Для обратной совместимости временно используем заглушку
            stats = self.orchestrator.run(
                progress_callback=self._on_progress
            )
            self.progress_all_finish.emit(stats)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _on_progress(self, event: str, **kwargs):
        """Обработчик событий прогресса."""
        if self._cancelled:
            return

        if event == 'table_start':
            self.progress_table_start.emit(kwargs['table_name'], kwargs.get('total_records', 0))
        elif event == 'table_update':
            self.progress_table_update.emit(kwargs['processed'], kwargs.get('total', 0))
        elif event == 'table_finish':
            self.progress_table_finish.emit(
                kwargs.get('inserted', 0),
                kwargs.get('updated', 0),
                kwargs.get('errors', 0),
                kwargs.get('skipped', 0)
            )