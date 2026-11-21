# dialogs/select_field_dialog.py
"""
Независимое модальное окно выбора поля.
Отвязано от сцены. Всегда поверх всех окон приложения.
Поддерживает контекст сущности (binding_entity).
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QApplication
)
from PySide6.QtCore import Qt
from database import DatabaseService
from core.system_fields import SYSTEM_FIELDS


class SelectFieldDialog(QDialog):
    """Выбор поля (вшитого или расширения) с деревом сущностей."""

    def __init__(self, parent=None, db: DatabaseService = None,
                 current_value: Optional[str] = None,
                 entity_id: Optional[int] = None):
        # 🚀 КРИТИЧЕСКИ ВАЖНО: Игнорируем родителя для создания независимого окна
        super().__init__(None)

        # Устанавливаем флаги для независимого окна, которое ВСЕГДА ПОВЕРХ
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowTitleHint |
            Qt.CustomizeWindowHint
        )

        # Модальность приложения
        self.setWindowModality(Qt.ApplicationModal)

        self.setWindowTitle("Выбор поля")
        self.resize(800, 600)

        # Центрируем окно относительно активного окна приложения
        main_window = QApplication.activeWindow()
        if main_window:
            geo = main_window.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

        # Подключение к БД (ОБЯЗАТЕЛЬНО явная передача)
        if db is None:
            raise ValueError("SelectFieldDialog требует активного подключения к БД")
        self.db = db

        # Нормализация параметров
        self.current_value = str(current_value).strip() if current_value not in (None, "", "None") else None
        self.entity_id = int(entity_id) if entity_id not in (None, "") else None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите поле:"))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя", "Алиас", "Тип", "Источник"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 260)
        self.tree.setColumnWidth(2, 60)
        self.tree.setColumnWidth(3, 260)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setFocusPolicy(Qt.StrongFocus)
        self.tree.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("Выбрать")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self._target_item = None
        self._load()
        self.tree.setFocus()

    def _load(self):
        """Загрузка дерева полей."""
        if self.entity_id is not None:
            # Режимы B / C — одна сущность
            self._load_one_entity(self.entity_id)
        else:
            # Режим A — все сущности
            self._load_all_entities()

        self.tree.expandAll()
        if self._target_item is not None:
            self.tree.setCurrentItem(self._target_item)
            self.tree.scrollToItem(self._target_item)

    def _make_entity_item(self, entity_row, parent=None) -> QTreeWidgetItem:
        """Создает узел сущности в дереве."""
        eid, cname, calias = entity_row
        item = QTreeWidgetItem()
        item.setText(0, f"📁 {cname} ({calias})")
        item.setData(0, Qt.UserRole, None)  # папка — не поле
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        return item

    def _fill_entity_fields(self, entity_item: QTreeWidgetItem, entity_id: int):
        """Заполняет узел сущности её полями."""
        # 1) Вшитые поля (общие для всех) — id < 0
        for sid in sorted(SYSTEM_FIELDS.keys()):
            info = SYSTEM_FIELDS[sid]
            child = QTreeWidgetItem(entity_item)
            child.setText(0, info["cname"])
            child.setText(1, info["calias"])
            child.setText(2, info["cfieldtype"])
            child.setText(3, f"вшитое ({info['table']})")
            child.setData(0, Qt.UserRole, sid)
            child.setForeground(0, Qt.gray)
            self._maybe_mark_target(child, sid)

        # 2) Поля расширения — meta.fields
        sql = """
            SELECT f.id, f.cfieldname, f.calias, f.cfieldtype,
                   COALESCE(ft.cname, '')
            FROM meta.fields f
            LEFT JOIN meta.field_types ft ON f.cfieldtype = ft.ccode
            WHERE f.entitytypeid = %s
            ORDER BY f.isortorder, f.id
        """
        rows = self.db.execute_query(sql, (entity_id,)) or []
        for (fid, cfieldname, calias, cfieldtype, type_name) in rows:
            child = QTreeWidgetItem(entity_item)
            child.setText(0, cfieldname)
            child.setText(1, calias or "")
            child.setText(2, cfieldtype or "")
            child.setText(3, f"meta.fields ({type_name})")
            child.setData(0, Qt.UserRole, fid)
            self._maybe_mark_target(child, fid)

    def _maybe_mark_target(self, item: QTreeWidgetItem, field_id):
        """Подсвечивает строку, если ID совпадает с current_value."""
        if self.current_value is not None and str(field_id) == self.current_value:
            self._target_item = item

    def _load_one_entity(self, entity_id: int):
        """Загружает дерево для одной конкретной сущности."""
        sql = "SELECT id, cname, calias FROM meta.entitytypes WHERE id = %s"
        rows = self.db.execute_query(sql, (entity_id,)) or []
        if not rows:
            return
        entity_item = self._make_entity_item(rows[0])
        self._fill_entity_fields(entity_item, entity_id)

    def _load_all_entities(self):
        """Загружает дерево для всех сущностей."""
        sql = "SELECT id, cname, calias FROM meta.entitytypes ORDER BY cname"
        rows = self.db.execute_query(sql) or []
        for row in rows:
            entity_item = self._make_entity_item(row)
            self._fill_entity_fields(entity_item, row[0])

    def get_selected_id(self) -> Optional[str]:
        """Возвращает ID выбранного поля как строку."""
        item = self.tree.currentItem()
        if item is None:
            return None
        fid = item.data(0, Qt.UserRole)
        if fid is None:
            return None
        return str(fid)

    def accept(self):
        """Переопределяем accept для проверки выбора."""
        if self.get_selected_id() is None:
            return
        super().accept()

    def keyPressEvent(self, event):
        """Обрабатываем Enter и Escape корректно."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)