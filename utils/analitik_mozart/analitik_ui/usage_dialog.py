# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/usage_dialog.py
"""
Диалог отображения графа использований (Usage Chain).
Версия: 2.0 — для единой таблицы сущностей
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QHBoxLayout, QProgressDialog,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from sqlalchemy import text

from analitik_core.database import get_session, get_db
from analitik_core.models import Entity, EntityType


class UsageDialog(QDialog):
    """Диалог отображения графа использований."""

    def __init__(self, entity_id: str, entity_name: str = None,
                 parent=None, db_session=None, view_time=None):
        super().__init__(parent)

        self.entity_id = entity_id
        self.entity_name = entity_name
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.view_time = view_time

        # Получаем сущность
        self.entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not self.entity:
            QMessageBox.critical(self, "Ошибка", "Сущность не найдена")
            self.reject()
            return

        display_name = self.entity_name or self.entity.c_name
        self.setWindowTitle(f"🕸️ Используется в: {display_name}")
        self.resize(700, 600)

        self._setup_ui()
        self._load_usage()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            f"🕸️ Поиск цепочек вызовов для: <b>{self.entity.c_name}</b>"
            f" ({EntityType.get_name(self.entity.type_id)})"
        )
        info.setStyleSheet("padding: 8px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Вызывающий элемент", "Контекст (Класс/Файл)", "Уровень"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 250)
        self.tree.setColumnWidth(2, 80)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self._load_usage)
        btn_layout.addWidget(self.btn_refresh)

        self.btn_close = QPushButton("✖ Закрыть")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _load_usage(self):
        """Загружает граф использований."""
        self.tree.clear()

        if not self.entity:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "❌ Сущность не найдена")
            return

        try:
            progress = QProgressDialog("Поиск использований...", "Отмена", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()

            dt = self.view_time or datetime.now()

            # Используем хранимую функцию find_usage_chain
            result = self.db_session.execute(
                text("SELECT * FROM mozart.find_usage_chain(:id, 5, :dt)"),
                {'id': self.entity_id, 'dt': dt}
            )

            rows = result.fetchall()
            progress.close()

            if not rows:
                item = QTreeWidgetItem(self.tree)
                item.setText(0, "ℹ️ Нет активных использований в базе данных")
                item.setText(1, "")
                item.setText(2, "")
                return

            # Добавляем корневой элемент — саму сущность
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, f"🎯 {self.entity.c_name}")
            root_item.setText(1, EntityType.get_name(self.entity.type_id))
            root_item.setText(2, "0")
            root_item.setExpanded(True)

            # Группируем по уровням
            for row in rows:
                level = row.level if hasattr(row, 'level') else 1
                caller_name = row.caller_name if hasattr(row, 'caller_name') else 'неизвестно'
                caller_type = row.caller_type if hasattr(row, 'caller_type') else 'unknown'
                parent_name = row.parent_name if hasattr(row, 'parent_name') else ''

                # Определяем иконку
                icon = "🔧" if caller_type == 'method' else "⚡" if caller_type == 'procedure' else "📄"

                item = QTreeWidgetItem()
                item.setText(0, f"{icon} {caller_name}")
                item.setText(1, parent_name)
                item.setText(2, f"L{level}")

                # Добавляем в дерево
                if level == 1:
                    root_item.addChild(item)
                else:
                    # Ищем родителя на предыдущем уровне
                    self._add_to_parent(root_item, item, level - 1)

            self.tree.expandAll()

        except Exception as e:
            progress.close()
            item = QTreeWidgetItem(self.tree)
            item.setText(0, f"❌ Ошибка: {str(e)}")
            QMessageBox.warning(self, "Ошибка", str(e))

    def _add_to_parent(self, parent_item: QTreeWidgetItem, child_item: QTreeWidgetItem, target_level: int):
        """Добавляет элемент к родителю на указанном уровне."""
        # Ищем элемент на нужном уровне
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            # Проверяем уровень
            level_text = child.text(2)
            if level_text and level_text.startswith(f"L{target_level}"):
                child.addChild(child_item)
                return
            # Рекурсивно ищем глубже
            self._add_to_parent(child, child_item, target_level)

        # Если не нашли — добавляем к корню
        parent_item.addChild(child_item)


# ================================================================
# ФУНКЦИЯ ДЛЯ БЫСТРОГО ЗАПУСКА
# ================================================================

def show_usage_dialog(entity_id: str, entity_name: str = None,
                      parent=None, db_session=None, view_time=None):
    """Показывает диалог графа использований."""
    dialog = UsageDialog(entity_id, entity_name, parent, db_session, view_time)
    return dialog.exec_()