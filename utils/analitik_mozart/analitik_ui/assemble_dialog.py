# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/assemble_dialog.py
"""
Диалог предпросмотра собранного файла.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QMessageBox, QSplitter,
    QWidget, QFrame, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from analitik_core.database import get_session
from analitik_core.assembler import CodeAssembler
from analitik_core.models import Entity, EntityType


class AssemblePreviewDialog(QDialog):
    """Диалог предпросмотра собранного файла."""

    def __init__(
        self,
        file_id: str,
        assembled_text: str,
        parent=None,
        db_session=None
    ):
        super().__init__(parent)
        self.file_id = file_id
        self.assembled_text = assembled_text
        self.db_session = db_session or get_session()
        self.assembler = CodeAssembler(self.db_session)

        self.setWindowTitle("🔧 Сборка файла — предпросмотр")
        self.resize(1000, 700)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()
        self.info_label = QLabel("📄 Собранный файл")
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.info_label)

        header.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #6c757d;")
        header.addWidget(self.stats_label)

        layout.addLayout(header)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Основной текст
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.text_edit.setPlainText(self.assembled_text)
        layout.addWidget(self.text_edit, 1)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.btn_apply = QPushButton("✅ Применить сборку")
        self.btn_apply.clicked.connect(self._apply_assemble)
        self.btn_apply.setStyleSheet("background-color: #28a745; color: white;")
        btn_layout.addWidget(self.btn_apply)

        self.btn_compare = QPushButton("📊 Сравнить с текущим")
        self.btn_compare.clicked.connect(self._compare_with_current)
        btn_layout.addWidget(self.btn_compare)

        btn_layout.addStretch()

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Загружает информацию о файле."""
        file_entity = self.db_session.query(Entity).filter(
            Entity.id == self.file_id,
            Entity.is_active == True
        ).first()

        if file_entity:
            current_text = file_entity.t_full_text or ""
            stats = f"Размер: {len(self.assembled_text)} байт"
            if current_text:
                diff = len(self.assembled_text) - len(current_text)
                stats += f" | Изменение: {diff:+d} байт"
            self.stats_label.setText(stats)

    def _apply_assemble(self):
        """Применяет собранный текст к файлу."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Применить сборку?\n\n"
            "Это создаст новую версию файла и всех его частей.\n"
            "⚠️ Изменения будут сохранены в БД!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Получаем текущий файл
            file_entity = self.db_session.query(Entity).filter(
                Entity.id == self.file_id,
                Entity.is_active == True
            ).first()

            if not file_entity:
                QMessageBox.warning(self, "Ошибка", "Файл не найден")
                return

            # Закрываем старую версию файла
            file_entity.is_active = False
            file_entity.dt_end = datetime.now()

            # Создаём новую версию файла с собранным текстом
            new_file = Entity(
                type_id=EntityType.FILE,
                c_name=file_entity.c_name,
                parent_id=file_entity.parent_id,
                t_full_text=self.assembled_text,
                j_data=file_entity.j_data.copy() if file_entity.j_data else {},
                m_comment=file_entity.m_comment,
                n_order=file_entity.n_order,
                n_old_version=file_entity.id
            )
            self.db_session.add(new_file)
            self.db_session.flush()

            # Пересобираем все части файла (импорты, переменные, классы, процедуры)
            self._rebuild_parts_from_text(new_file.id, self.assembled_text)

            self.db_session.commit()

            QMessageBox.information(
                self,
                "Успех",
                f"✅ Файл собран и сохранён!\n\n"
                f"Новая версия: {new_file.id}"
            )

            self.accept()

            # Обновляем дерево в главном окне
            if self.parent():
                self.parent().refresh_tree()

        except Exception as e:
            self.db_session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _rebuild_parts_from_text(self, file_id: str, text: str):
        """Пересобирает все части файла из текста."""
        # Парсим текст
        from analitik_core.parser import PythonParser
        parser = PythonParser()
        parse_result = parser.parse_file("assembled.py", text)

        if parse_result.get('error'):
            print(f"⚠️ Ошибка парсинга при сборке: {parse_result['error']}")
            return

        # Закрываем старые части
        self.db_session.query(Entity).filter(
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).update({'is_active': False, 'dt_end': datetime.now()})

        # Загружаем новые части
        from analitik_scanner.loader import DataLoader
        loader = DataLoader(self.db_session)
        loader._load_file_structure(file_id, "assembled.py", parse_result)

    def _compare_with_current(self):
        """Сравнивает собранный текст с текущим файлом."""
        file_entity = self.db_session.query(Entity).filter(
            Entity.id == self.file_id,
            Entity.is_active == True
        ).first()

        if not file_entity:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return

        current_text = file_entity.t_full_text or ""

        from analitik_compare import show_diff_dialog
        # Показываем сравнение в отдельном диалоге
        show_diff_dialog(
            entity_id=self.file_id,
            entity_name=file_entity.c_name,
            parent=self,
            db_session=self.db_session
        )