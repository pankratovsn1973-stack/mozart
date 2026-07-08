# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_compare/diff_dialog.py
"""
Диалог сравнения кода из БД и с диска.
Версия: 2.0 — для единой таблицы сущностей
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QLabel, QPushButton, QFrame,
    QMessageBox, QApplication, QProgressDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter, QFont

from analitik_compare.diff_engine import DiffEngine
from analitik_core.database import get_session
from analitik_core.models import Entity, EntityType


class DiffHighlighter(QSyntaxHighlighter):
    """Подсветка различий в тексте."""

    def __init__(self, parent, diff_result, side='db'):
        super().__init__(parent)
        self.diff_result = diff_result
        self.side = side
        self._setup_formats()

    def _setup_formats(self):
        self.added_format = QTextCharFormat()
        self.added_format.setBackground(QColor(144, 238, 144))
        self.added_format.setForeground(QColor(0, 100, 0))

        self.deleted_format = QTextCharFormat()
        self.deleted_format.setBackground(QColor(255, 182, 182))
        self.deleted_format.setForeground(QColor(139, 0, 0))

        self.changed_format = QTextCharFormat()
        self.changed_format.setBackground(QColor(255, 255, 153))
        self.changed_format.setForeground(QColor(139, 69, 19))

    def highlightBlock(self, text):
        block_index = self.currentBlock().blockNumber()

        if not self.diff_result or 'changed_lines' not in self.diff_result:
            return

        for change in self.diff_result['changed_lines']:
            if change.get('line_num') == block_index + 1:
                if self.side == 'db':
                    if change.get('type') == 'deleted':
                        self.setFormat(0, len(text), self.deleted_format)
                    elif change.get('type') == 'changed':
                        self.setFormat(0, len(text), self.changed_format)
                else:
                    if change.get('type') == 'added':
                        self.setFormat(0, len(text), self.added_format)
                    elif change.get('type') == 'changed':
                        self.setFormat(0, len(text), self.changed_format)
                break


class DiffDialog(QDialog):
    """Диалог сравнения кода."""

    def __init__(
        self,
        entity_id: str,
        entity_name: str = None,
        parent=None,
        db_session=None,
        view_time=None
    ):
        super().__init__(parent)

        self.entity_id = entity_id
        self.entity_name = entity_name
        self.db_session = db_session or get_session()
        self.view_time = view_time or datetime.now()

        self.engine = DiffEngine(self.db_session)
        self.diff_result = None

        # Получаем информацию о сущности
        self.entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not self.entity:
            QMessageBox.critical(self, "Ошибка", "Сущность не найдена")
            self.reject()
            return

        entity_type_name = EntityType.get_name(self.entity.type_id)
        display_name = self.entity_name or self.entity.c_name

        self.setWindowTitle(f"📊 Сравнение: {display_name} ({entity_type_name})")
        self.resize(1400, 800)

        self._setup_ui()
        self._load_comparison()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._setup_header(layout)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        self._setup_analysis_panel(layout)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)

        self._setup_diff_panels(layout)

        self._setup_buttons(layout)

    def _setup_header(self, layout):
        header = QHBoxLayout()

        entity_type_name = EntityType.get_name(self.entity.type_id)
        display_name = self.entity_name or self.entity.c_name

        info_text = f"📄 {display_name} ({entity_type_name})"
        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.info_label)

        header.addStretch()

        time_text = f"⏱️ {self.view_time.strftime('%d.%m.%Y %H:%M')}"
        self.time_label = QLabel(time_text)
        self.time_label.setStyleSheet("color: #7f8c8d;")
        header.addWidget(self.time_label)

        self.status_indicator = QLabel("")
        self.status_indicator.setFixedWidth(120)
        header.addWidget(self.status_indicator)

        layout.addLayout(header)

    def _setup_analysis_panel(self, layout):
        self.analysis_frame = QFrame()
        self.analysis_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        analysis_layout = QVBoxLayout(self.analysis_frame)

        self.analysis_label = QLabel("⏳ Загрузка анализа...")
        self.analysis_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        analysis_layout.addWidget(self.analysis_label)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("font-size: 11px; color: #495057;")
        analysis_layout.addWidget(self.detail_label)

        layout.addWidget(self.analysis_frame)

    def _setup_diff_panels(self, layout):
        self.splitter = QSplitter(Qt.Horizontal)

        self.db_panel = self._create_text_panel("📦 База данных", 'db')
        self.splitter.addWidget(self.db_panel)

        self.disk_panel = self._create_text_panel("💾 Файл на диске", 'disk')
        self.splitter.addWidget(self.disk_panel)

        self.splitter.setSizes([700, 700])
        layout.addWidget(self.splitter, 1)

    def _create_text_panel(self, title: str, side: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                background-color: #f1f3f5;
                padding: 6px 12px;
                font-weight: bold;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(title_label)

        text_edit = QTextEdit()
        text_edit.setFont(QFont("Courier New", 10))
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(text_edit)

        status_label = QLabel("Строк: 0")
        status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 2px 8px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                font-size: 10px;
            }
        """)
        layout.addWidget(status_label)

        frame.text_edit = text_edit
        frame.status_label = status_label
        frame.side = side

        return frame

    def _setup_buttons(self, layout):
        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self._load_comparison)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setStyleSheet("background-color: #6c757d; color: white;")
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _load_comparison(self):
        try:
            progress = QProgressDialog("Сравнение...", "Отмена", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()

            self.diff_result = self.engine.compare_entity(self.entity_id, self.view_time)

            progress.close()

            if 'error' in self.diff_result:
                QMessageBox.warning(self, "Ошибка", self.diff_result['error'])
                return

            self._update_ui()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _update_ui(self):
        if not self.diff_result:
            return

        status = self.diff_result.get('status', 'unknown')
        stats = self.diff_result.get('stats', {})

        # Обновляем анализ
        analysis = self.diff_result.get('analysis', '')
        self.analysis_label.setText(f"📊 {analysis}")

        # Детали
        details = []
        if stats.get('added', 0) > 0:
            details.append(f"➕ +{stats['added']}")
        if stats.get('deleted', 0) > 0:
            details.append(f"➖ -{stats['deleted']}")
        if stats.get('changed', 0) > 0:
            details.append(f"✏️ ±{stats['changed']}")
        if stats.get('total_diff', 0) > 0:
            details.append(f"📊 всего: {stats['total_diff']}")
        self.detail_label.setText(" | ".join(details) if details else "✅ Файлы идентичны")

        # Индикатор статуса
        status_colors = {
            'identical': ('🟢 Идентичны', '#28a745', '#d4edda'),
            'modified': ('🟡 Изменён', '#ffc107', '#fff3cd'),
            'new': ('🔵 Новый на диске', '#17a2b8', '#d1ecf1'),
            'deleted': ('🔴 Удалён с диска', '#dc3545', '#f8d7da')
        }

        status_text, color, bg_color = status_colors.get(
            status,
            ('❓', '#6c757d', '#f8f9fa')
        )

        self.status_indicator.setText(status_text)
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                background-color: {bg_color};
            }}
        """)

        # Заполняем панели
        db_lines = self.diff_result.get('db_lines', [])
        disk_lines = self.diff_result.get('disk_lines', [])

        self.db_panel.text_edit.setPlainText('\n'.join(db_lines))
        self.disk_panel.text_edit.setPlainText('\n'.join(disk_lines))

        self.db_panel.status_label.setText(f"Строк: {len(db_lines)}")
        self.disk_panel.status_label.setText(f"Строк: {len(disk_lines)}")

        # Подсветка
        if self.diff_result.get('changed_lines'):
            DiffHighlighter(self.db_panel.text_edit.document(), self.diff_result, 'db')
            DiffHighlighter(self.disk_panel.text_edit.document(), self.diff_result, 'disk')

    def _get_color(self, status):
        return {
            'identical': '#28a745',
            'modified': '#ffc107',
            'new': '#17a2b8',
            'deleted': '#dc3545'
        }.get(status, '#6c757d')

    def _get_bg_color(self, status):
        return {
            'identical': '#d4edda',
            'modified': '#fff3cd',
            'new': '#d1ecf1',
            'deleted': '#f8d7da'
        }.get(status, '#f8f9fa')


# ================================================================
# ФУНКЦИЯ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_diff_dialog(
    entity_id: str,
    entity_name: str = None,
    parent=None,
    db_session=None,
    view_time=None
):
    """Показывает диалог сравнения."""
    dialog = DiffDialog(
        entity_id=entity_id,
        entity_name=entity_name,
        parent=parent,
        db_session=db_session,
        view_time=view_time
    )
    return dialog.exec_()