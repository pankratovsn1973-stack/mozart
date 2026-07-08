# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/ai_assistant_dialog.py
"""
Диалог взаимодействия с ИИ-ассистентом.
Версия: 2.0 — для единой таблицы сущностей
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QMessageBox, QSplitter,
    QWidget, QFrame, QComboBox, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QClipboard, QColor

from analitik_ai.context_builder import ContextBuilder
from analitik_core.database import get_session
from analitik_core.models import Entity, EntityType, Task


class AIAssistantDialog(QDialog):
    """
    Диалог ИИ-помощника.
    Левое поле — промпт, правое — ответ от ИИ.
    """

    def __init__(
        self,
        entity_id: str = None,
        entity_name: str = None,
        task_id: str = None,
        parent=None,
        db_session=None,
        view_time=None
    ):
        super().__init__(parent)

        self.entity_id = entity_id
        self.entity_name = entity_name
        self.task_id = task_id
        self.db_session = db_session or get_session()
        self.view_time = view_time

        self.builder = ContextBuilder(self.db_session, view_time)
        self._parse_result = None

        # Получаем информацию о сущности
        self.entity = None
        if self.entity_id:
            self.entity = self.db_session.query(Entity).filter(
                Entity.id == self.entity_id,
                Entity.is_active == True
            ).first()
            if self.entity:
                self.entity_name = self.entity_name or self.entity.c_name

        title = "🤖 ИИ-Помощник"
        if self.entity_name:
            title += f": {self.entity_name}"
        if self.task_id:
            task = self.db_session.query(Task).filter(Task.id == self.task_id).first()
            if task:
                title += f" (Задача: {task.task_number})"

        self.setWindowTitle(title)
        self.resize(1200, 750)

        self._setup_ui()
        self._generate_initial_prompt()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()

        info_text = f"🤖 ИИ-Помощник"
        if self.entity_name:
            info_text += f": {self.entity_name}"
        if self.task_id:
            task = self.db_session.query(Task).filter(Task.id == self.task_id).first()
            if task:
                info_text += f" (Задача: {task.task_number})"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        header.addWidget(self.info_label)

        header.addStretch()

        self.status_label = QLabel("🟢 Готов")
        self.status_label.setStyleSheet("color: green; padding: 8px;")
        header.addWidget(self.status_label)

        layout.addLayout(header)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Основные панели
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель — ПРОМПТ
        left_panel = self._create_panel(
            "📋 ПРОМПТ (скопируй в чат с ИИ)",
            "prompt",
            "Сгенерированный промпт для ИИ"
        )
        splitter.addWidget(left_panel)

        # Правая панель — ОТВЕТ ИИ
        right_panel = self._create_panel(
            "📥 ОТВЕТ ИИ (вставь сюда ответ)",
            "response",
            "Вставь сюда ответ от ИИ"
        )
        splitter.addWidget(right_panel)

        splitter.setSizes([600, 600])
        layout.addWidget(splitter, 1)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        # Кнопки для левой панели
        self.btn_copy_prompt = QPushButton("📋 Копировать промпт")
        self.btn_copy_prompt.clicked.connect(self._copy_prompt)
        self.btn_copy_prompt.setStyleSheet("background-color: #3498db; color: white;")
        btn_layout.addWidget(self.btn_copy_prompt)

        self.btn_regenerate = QPushButton("🔄 Регенерировать промпт")
        self.btn_regenerate.clicked.connect(self._generate_initial_prompt)
        btn_layout.addWidget(self.btn_regenerate)

        btn_layout.addStretch()

        # Кнопки для правой панели
        self.btn_parse = QPushButton("🔍 Парсить ответ")
        self.btn_parse.clicked.connect(self._parse_response)
        self.btn_parse.setStyleSheet("background-color: #f39c12; color: white;")
        btn_layout.addWidget(self.btn_parse)

        self.btn_apply = QPushButton("✅ Применить изменения")
        self.btn_apply.clicked.connect(self._apply_changes)
        self.btn_apply.setStyleSheet("background-color: #2ecc71; color: white;")
        self.btn_apply.setEnabled(False)
        btn_layout.addWidget(self.btn_apply)

        btn_layout.addStretch()

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

        # Статусная строка
        self.status_bar = QLabel("Готов к работе. Скопируйте промпт и отправьте в ИИ.")
        self.status_bar.setStyleSheet("padding: 8px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(self.status_bar)

    def _create_panel(self, title: str, name: str, placeholder: str) -> QWidget:
        """Создаёт панель с текстовым полем."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; padding: 4px; background-color: #f1f3f5; border-radius: 4px;")
        layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setFont(QFont("Courier New", 10))
        text_edit.setPlaceholderText(placeholder)
        text_edit.setLineWrapMode(QTextEdit.NoWrap)
        text_edit.setReadOnly(name == "prompt")

        layout.addWidget(text_edit)

        # Счётчик строк
        count_label = QLabel("Строк: 0")
        count_label.setStyleSheet("color: #6c757d; font-size: 10px; padding: 2px;")
        layout.addWidget(count_label)

        setattr(self, f"{name}_edit", text_edit)
        setattr(self, f"{name}_count", count_label)

        text_edit.textChanged.connect(
            lambda: count_label.setText(f"Строк: {text_edit.document().blockCount()}")
        )

        return panel

    def _generate_initial_prompt(self):
        """Генерирует начальный промпт."""
        try:
            self.status_bar.setText("⏳ Генерация промпта...")
            QTimer.singleShot(100, self._do_generate_prompt)
        except Exception as e:
            self.status_bar.setText(f"❌ Ошибка: {e}")

    def _do_generate_prompt(self):
        """Выполняет генерацию промпта."""
        try:
            prompt = ""

            if self.task_id:
                prompt = self.builder.build_prompt_from_task(self.task_id)
            elif self.entity_id:
                prompt = self.builder.build_prompt_from_entity(self.entity_id)
            else:
                prompt = "❌ Не указана ни задача, ни сущность."

            self.prompt_edit.setText(prompt)
            self.status_bar.setText("✅ Промпт сгенерирован. Скопируйте его и отправьте в ИИ.")

        except Exception as e:
            self.prompt_edit.setText(f"❌ Ошибка генерации: {e}")
            self.status_bar.setText(f"❌ Ошибка: {e}")

    def _copy_prompt(self):
        """Копирует промпт в буфер обмена."""
        text = self.prompt_edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Ошибка", "Промпт пуст!")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_bar.setText("✅ Промпт скопирован в буфер обмена")

    def _parse_response(self):
        """Парсит ответ ИИ."""
        response = self.response_edit.toPlainText()
        if not response.strip():
            QMessageBox.warning(self, "Ошибка", "Поле ответа пусто!")
            return

        if not self.entity_id:
            QMessageBox.warning(self, "Ошибка", "Не указана сущность для обновления!")
            return

        self.status_bar.setText("⏳ Парсинг ответа...")
        QTimer.singleShot(100, self._do_parse_response)

    def _do_parse_response(self):
        """Выполняет парсинг ответа."""
        try:
            response = self.response_edit.toPlainText()
            parse_result = self.builder.parse_ai_response(response, self.entity_id)

            if parse_result.get('success'):
                self._parse_result = parse_result
                self.btn_apply.setEnabled(True)

                changes = parse_result.get('changes', [])
                if changes:
                    msg = f"✅ Найдены изменения:\n"
                    for ch in changes:
                        msg += f"  - {ch['type']}: {ch['entity']}\n"
                    msg += f"\nНажмите 'Применить изменения' для сохранения."
                    self.status_bar.setText(msg)
                    QMessageBox.information(self, "Парсинг успешен", msg)
                else:
                    self.status_bar.setText("✅ Код не изменился (совпадает с текущим)")
                    self.btn_apply.setEnabled(False)
            else:
                error = parse_result.get('error', 'Неизвестная ошибка')
                self.status_bar.setText(f"❌ Ошибка парсинга: {error}")
                QMessageBox.warning(self, "Ошибка парсинга", error)
                self.btn_apply.setEnabled(False)

        except Exception as e:
            self.status_bar.setText(f"❌ Ошибка: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))
            self.btn_apply.setEnabled(False)

    def _apply_changes(self):
        """Применяет изменения."""
        if not hasattr(self, '_parse_result'):
            QMessageBox.warning(self, "Ошибка", "Сначала выполните парсинг ответа!")
            return

        parse_result = self._parse_result
        if not parse_result.get('success'):
            QMessageBox.warning(self, "Ошибка", parse_result.get('error', 'Неизвестная ошибка'))
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Применить изменения в базе данных?\n\n"
            "Старая версия будет закрыта, создана новая.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.status_bar.setText("⏳ Применение изменений...")
        QTimer.singleShot(100, self._do_apply_changes)

    def _do_apply_changes(self):
        """Выполняет применение изменений."""
        try:
            result = self.builder.apply_changes(self._parse_result)

            if result.get('success'):
                self.status_bar.setText(f"✅ {result.get('message', 'Изменения применены')}")
                QMessageBox.information(
                    self,
                    "Успех",
                    f"✅ {result.get('message', 'Изменения применены')}\n\n"
                    f"Новая версия: {result.get('new_version_id')}"
                )
                self.btn_apply.setEnabled(False)

                self.entity_id = result.get('new_version_id')
                self._generate_initial_prompt()

            else:
                error = result.get('error', 'Неизвестная ошибка')
                self.status_bar.setText(f"❌ Ошибка: {error}")
                QMessageBox.critical(self, "Ошибка", error)

        except Exception as e:
            self.status_bar.setText(f"❌ Ошибка: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))


# ================================================================
# ФУНКЦИЯ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_ai_assistant(
    entity_id: str = None,
    entity_name: str = None,
    task_id: str = None,
    parent=None,
    db_session=None,
    view_time=None
):
    """Показывает диалог ИИ-помощника."""
    dialog = AIAssistantDialog(
        entity_id=entity_id,
        entity_name=entity_name,
        task_id=task_id,
        parent=parent,
        db_session=db_session,
        view_time=view_time
    )
    return dialog.exec_()