# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_ui/tree_tasks.py
"""
Дерево задач, архитектурных решений и планов для Аналитика Моцарт.
Версия: 2.0 — для единой таблицы сущностей
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFrame,
    QMessageBox, QDialog, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QDialogButtonBox, QSplitter,
    QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from sqlalchemy import text

from analitik_core.models import Task, ArchSolution, Plan, Action, ActionResult, Entity, EntityType
from analitik_core.database import get_db, get_session


class TaskDialog(QDialog):
    """Диалог создания/редактирования задачи."""

    def __init__(self, parent=None, task_data=None, db_session=None):
        super().__init__(parent)
        self.db_session = db_session or get_session()
        self.db = get_db()
        self.task_data = task_data
        self.is_edit = task_data is not None

        self.setWindowTitle("📋 Задача" if not self.is_edit else "📋 Редактирование задачи")
        self.resize(600, 500)

        self._setup_ui()
        if self.is_edit:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.number_label = QLabel("Автоматически")
        form.addRow("Номер:", self.number_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите название задачи...")
        form.addRow("Название:", self.title_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Введите описание задачи...")
        self.desc_edit.setMaximumHeight(120)
        form.addRow("Описание:", self.desc_edit)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['critical', 'high', 'medium', 'low'])
        form.addRow("Приоритет:", self.priority_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['draft', 'approved', 'in_progress', 'done', 'cancelled'])
        form.addRow("Статус:", self.status_combo)

        self.deadline_edit = QLineEdit()
        self.deadline_edit.setPlaceholderText("2024-12-31")
        form.addRow("Дедлайн:", self.deadline_edit)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_data(self):
        if not self.task_data:
            return
        self.title_edit.setText(self.task_data.get('title', ''))
        self.desc_edit.setText(self.task_data.get('description', ''))

        idx = self.priority_combo.findText(self.task_data.get('priority', 'medium'))
        if idx >= 0:
            self.priority_combo.setCurrentIndex(idx)

        idx = self.status_combo.findText(self.task_data.get('status', 'draft'))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.deadline_edit.setText(self.task_data.get('deadline', ''))

    def get_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip(),
            'priority': self.priority_combo.currentText(),
            'status': self.status_combo.currentText(),
            'deadline': self.deadline_edit.text().strip() or None
        }


class TreeTasks(QWidget):
    """Виджет с деревом задач, архитектуры и планов."""

    task_selected = Signal(str)
    arch_selected = Signal(str)
    plan_selected = Signal(str)
    entity_selected = Signal(str, str)  # entity_id, entity_type

    def __init__(self, parent=None, db_session=None, view_time=None):
        super().__init__(parent)
        self._db_session = db_session
        self._view_time = view_time or datetime.now()

        self.db_session = None
        self.db = None

        self._setup_ui()

    def update_session(self, db_session, db):
        """Обновляет сессию БД после инициализации главного окна."""
        self.db_session = db_session
        self.db = db
        self.refresh()

    def _ensure_db(self):
        """Гарантирует, что подключение к БД установлено."""
        if self.db_session is None:
            if self._db_session is not None:
                self.db_session = self._db_session
                self.db = get_db()
            else:
                try:
                    self.db_session = get_session()
                    self.db = get_db()
                except RuntimeError:
                    return False
        return self.db_session is not None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        control_layout = QHBoxLayout()

        self.btn_add_task = QPushButton("➕ Новая задача")
        self.btn_add_task.clicked.connect(self._add_task)
        control_layout.addWidget(self.btn_add_task)

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.refresh)
        control_layout.addWidget(self.btn_refresh)

        self.btn_expand_all = QPushButton("📂 Развернуть всё")
        self.btn_expand_all.clicked.connect(lambda: self.tree.expandAll())
        control_layout.addWidget(self.btn_expand_all)

        self.btn_collapse_all = QPushButton("📁 Свернуть всё")
        self.btn_collapse_all.clicked.connect(lambda: self.tree.collapseAll())
        control_layout.addWidget(self.btn_collapse_all)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Элемент", "Статус", "Дата"])
        self.tree.setColumnWidth(0, 500)
        self.tree.setColumnWidth(1, 120)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.tree, 1)

    def refresh(self):
        """Обновляет дерево с учётом времени."""
        if not self._ensure_db():
            self.tree.clear()
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "⏳ Подключение к базе данных...")
            return

        self.tree.clear()
        dt = self._view_time or datetime.now()

        tasks = self._get_tasks(dt)
        for task in tasks:
            task_item = self._create_task_item(task)
            self.tree.addTopLevelItem(task_item)
            task_item.setExpanded(True)

            # Кандидаты задачи (сущности)
            candidates = self._get_task_candidates(task.id, dt)
            if candidates:
                cand_item = QTreeWidgetItem(task_item)
                cand_item.setText(0, f"📎 Связанные сущности ({len(candidates)})")
                cand_item.setData(0, Qt.UserRole, {'type': 'category'})
                cand_item.setExpanded(True)

                for candidate in candidates:
                    self._create_entity_item(candidate, cand_item)

            archs = self._get_arch_solutions(task.id, dt)
            for arch in archs:
                arch_item = self._create_arch_item(arch, task_item)
                arch_item.setExpanded(True)

                # Кандидаты архитектуры
                arch_candidates = self._get_arch_candidates(arch.id, dt)
                if arch_candidates:
                    arch_cand_item = QTreeWidgetItem(arch_item)
                    arch_cand_item.setText(0, f"📎 Связанные сущности ({len(arch_candidates)})")
                    arch_cand_item.setData(0, Qt.UserRole, {'type': 'category'})
                    arch_cand_item.setExpanded(True)

                    for candidate in arch_candidates:
                        self._create_entity_item(candidate, arch_cand_item)

                plans = self._get_plans(arch.id, dt)
                for plan in plans:
                    plan_item = self._create_plan_item(plan, arch_item)
                    plan_item.setExpanded(True)

                    # Кандидаты плана
                    plan_candidates = self._get_plan_candidates(plan.id, dt)
                    if plan_candidates:
                        plan_cand_item = QTreeWidgetItem(plan_item)
                        plan_cand_item.setText(0, f"📎 Связанные сущности ({len(plan_candidates)})")
                        plan_cand_item.setData(0, Qt.UserRole, {'type': 'category'})
                        plan_cand_item.setExpanded(True)

                        for candidate in plan_candidates:
                            self._create_entity_item(candidate, plan_cand_item)

                    actions = self._get_actions(plan.id, dt)
                    for action in actions:
                        self._create_action_item(action, plan_item)

    def _get_tasks(self, dt: datetime):
        """Получает задачи на момент времени."""
        if not self._ensure_db():
            return []

        return self.db_session.query(Task).filter(
            Task.dt_start <= dt,
            (Task.dt_end.is_(None) | (Task.dt_end > dt))
        ).order_by(Task.created_at.desc()).all()

    def _get_task_candidates(self, task_id: str, dt: datetime):
        """Получает кандидатов задачи."""
        from analitik_core.models import TaskCandidate
        return self.db_session.query(TaskCandidate).filter(
            TaskCandidate.task_id == task_id,
            TaskCandidate.is_active == True
        ).all()

    def _get_arch_solutions(self, task_id: str, dt: datetime):
        return self.db_session.query(ArchSolution).filter(
            ArchSolution.task_id == task_id,
            ArchSolution.is_active == True,
            ArchSolution.dt_start <= dt,
            (ArchSolution.dt_end.is_(None) | (ArchSolution.dt_end > dt))
        ).all()

    def _get_arch_candidates(self, arch_id: str, dt: datetime):
        from analitik_core.models import ArchCandidate
        return self.db_session.query(ArchCandidate).filter(
            ArchCandidate.arch_solution_id == arch_id,
            ArchCandidate.is_active == True
        ).all()

    def _get_plans(self, arch_id: str, dt: datetime):
        return self.db_session.query(Plan).filter(
            Plan.arch_solution_id == arch_id,
            Plan.is_active == True,
            Plan.dt_start <= dt,
            (Plan.dt_end.is_(None) | (Plan.dt_end > dt))
        ).order_by(Plan.step_order).all()

    def _get_plan_candidates(self, plan_id: str, dt: datetime):
        from analitik_core.models import PlanCandidate
        return self.db_session.query(PlanCandidate).filter(
            PlanCandidate.plan_id == plan_id,
            PlanCandidate.is_active == True
        ).all()

    def _get_actions(self, plan_id: str, dt: datetime):
        return self.db_session.query(Action).filter(
            Action.plan_id == plan_id,
            Action.is_active == True,
            Action.dt_start <= dt,
            (Action.dt_end.is_(None) | (Action.dt_end > dt))
        ).order_by(Action.action_order).all()

    def _create_task_item(self, task):
        item = QTreeWidgetItem()
        priority_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(task.priority, '⚪')

        status_icon = {
            'draft': '📝',
            'approved': '✅',
            'in_progress': '🔄',
            'done': '✔️',
            'cancelled': '❌'
        }.get(task.status, '❓')

        item.setText(0, f"{priority_icon} TASK-{task.task_number} {task.title}")
        item.setText(1, f"{status_icon} {task.status}")
        item.setText(2, task.created_at.strftime('%d.%m.%Y') if task.created_at else '')
        item.setData(0, Qt.UserRole, {'type': 'task', 'id': str(task.id)})

        return item

    def _create_arch_item(self, arch, parent):
        item = QTreeWidgetItem(parent)
        status_icon = {
            'proposed': '💡',
            'reviewed': '👁️',
            'approved': '✅',
            'rejected': '❌'
        }.get(arch.status, '❓')

        approach_icon = {
            'monolith': '🏛️',
            'microservices': '🔗',
            'serverless': '☁️',
            'event_driven': '📨'
        }.get(arch.approach, '📐')

        item.setText(0, f"📐 {arch.solution_name} ({approach_icon})")
        item.setText(1, f"{status_icon} {arch.status}")
        item.setText(2, arch.created_at.strftime('%d.%m.%Y') if arch.created_at else '')
        item.setData(0, Qt.UserRole, {'type': 'arch', 'id': str(arch.id)})

        return item

    def _create_plan_item(self, plan, parent):
        item = QTreeWidgetItem(parent)
        status_icon = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'blocked': '🚫',
            'skipped': '⏭️'
        }.get(plan.status, '❓')

        item.setText(0, f"📋 [{plan.step_order}] {plan.plan_name}")
        item.setText(1, f"{status_icon} {plan.status}")
        item.setText(2, plan.created_at.strftime('%d.%m.%Y') if plan.created_at else '')
        item.setData(0, Qt.UserRole, {'type': 'plan', 'id': str(plan.id)})

        return item

    def _create_action_item(self, action, parent):
        item = QTreeWidgetItem(parent)
        type_icon = {
            'create_file': '📄+',
            'delete_file': '📄-',
            'rename_file': '📄✏️',
            'create_procedure': '⚡+',
            'update_procedure': '⚡✏️',
            'delete_procedure': '⚡-',
            'create_class': '📦+',
            'update_class': '📦✏️',
            'delete_class': '📦-',
            'add_import': '📥',
            'remove_import': '📤',
            'update_global_var': '🔤✏️',
            'add_global_var': '🔤+'
        }.get(action.action_type, '•')

        item.setText(0, f"  {type_icon} {action.change_description}")
        item.setText(1, action.executed_at.strftime('%d.%m.%Y') if action.executed_at else '⏳')
        item.setText(2, '')
        item.setData(0, Qt.UserRole, {'type': 'action', 'id': str(action.id)})

        return item

    def _create_entity_item(self, candidate, parent):
        """Создаёт элемент для сущности-кандидата."""
        entity = self.db_session.query(Entity).filter(
            Entity.id == candidate.target_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return

        item = QTreeWidgetItem(parent)
        icon = EntityType.get_icon(entity.type_id)
        type_name = EntityType.get_name(entity.type_id)

        impact_icon = {
            'create': '➕',
            'modify': '✏️',
            'delete': '➖',
            'deprecate': '⚠️'
        }.get(candidate.impact_type, '•')

        item.setText(0, f"  {icon} {entity.c_name} {impact_icon}")
        item.setText(1, f"{type_name} → {candidate.impact_type}")
        item.setText(2, '')
        item.setData(0, Qt.UserRole, {
            'type': 'entity',
            'id': str(entity.id),
            'entity_type': type_name,
            'entity_type_id': entity.type_id
        })

        return item

    def _add_task(self):
        if not self._ensure_db():
            QMessageBox.warning(self, "Ошибка", "База данных не подключена")
            return

        dialog = TaskDialog(self, db_session=self.db_session)
        if dialog.exec_():
            data = dialog.get_data()
            if not data['title']:
                QMessageBox.warning(self, "Ошибка", "Название задачи обязательно")
                return

            # Генерируем номер задачи
            with self.db.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT task_number FROM mozart.tbl_task ORDER BY task_number DESC LIMIT 1")
                )
                last = result.fetchone()

                if last:
                    try:
                        num = int(last[0].split('-')[-1]) + 1
                    except:
                        num = 1
                else:
                    num = 1

            task_number = f"{datetime.now().year}-{num:04d}"

            new_task = Task(
                task_number=task_number,
                title=data['title'],
                description=data['description'],
                priority=data['priority'],
                status=data['status'],
                deadline=data['deadline'],
                created_at=datetime.now(),
                dt_start=datetime.now()
            )
            self.db_session.add(new_task)
            self.db_session.commit()

            self.refresh()
            QMessageBox.information(self, "Успех", f"Задача {task_number} создана")

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        entity_type = data.get('type')
        entity_id = data.get('id')

        menu = QMenu(self)

        if entity_type == 'task':
            action_edit = QAction("✏️ Редактировать задачу", self)
            action_edit.triggered.connect(lambda: self._edit_task(entity_id))
            menu.addAction(action_edit)

            action_add_arch = QAction("📐 Добавить архитектурное решение", self)
            action_add_arch.triggered.connect(lambda: self._add_arch(entity_id))
            menu.addAction(action_add_arch)

            action_add_entity = QAction("📎 Привязать сущность", self)
            action_add_entity.triggered.connect(lambda: self._add_entity_to_task(entity_id))
            menu.addAction(action_add_entity)

            menu.addSeparator()

            action_delete = QAction("🗑️ Удалить задачу", self)
            action_delete.triggered.connect(lambda: self._delete_task(entity_id))
            menu.addAction(action_delete)

        elif entity_type == 'arch':
            action_add_plan = QAction("📋 Добавить план", self)
            action_add_plan.triggered.connect(lambda: self._add_plan(entity_id))
            menu.addAction(action_add_plan)

            menu.addSeparator()

            action_delete = QAction("🗑️ Удалить решение", self)
            action_delete.triggered.connect(lambda: self._delete_arch(entity_id))
            menu.addAction(action_delete)

        elif entity_type == 'plan':
            action_edit = QAction("✏️ Редактировать план", self)
            action_edit.triggered.connect(lambda: self._edit_plan(entity_id))
            menu.addAction(action_edit)

            menu.addSeparator()

            action_delete = QAction("🗑️ Удалить план", self)
            action_delete.triggered.connect(lambda: self._delete_plan(entity_id))
            menu.addAction(action_delete)

        elif entity_type == 'entity':
            action_view = QAction("👁️ Показать сущность", self)
            action_view.triggered.connect(lambda: self.entity_selected.emit(entity_id, data.get('entity_type', '')))
            menu.addAction(action_view)

            action_remove = QAction("❌ Отвязать сущность", self)
            action_remove.triggered.connect(lambda: self._remove_entity(entity_id))
            menu.addAction(action_remove)

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def _on_item_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        entity_type = data.get('type')
        entity_id = data.get('id')

        if entity_type == 'task':
            self.task_selected.emit(entity_id)
        elif entity_type == 'arch':
            self.arch_selected.emit(entity_id)
        elif entity_type == 'plan':
            self.plan_selected.emit(entity_id)
        elif entity_type == 'entity':
            self.entity_selected.emit(entity_id, data.get('entity_type', ''))

    def _edit_task(self, task_id):
        if not self._ensure_db():
            QMessageBox.warning(self, "Ошибка", "База данных не подключена")
            return

        task = self.db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        data = {
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else ''
        }

        dialog = TaskDialog(self, task_data=data, db_session=self.db_session)
        if dialog.exec_():
            new_data = dialog.get_data()
            if not new_data['title']:
                QMessageBox.warning(self, "Ошибка", "Название задачи обязательно")
                return

            task.title = new_data['title']
            task.description = new_data['description']
            task.priority = new_data['priority']
            task.status = new_data['status']
            task.deadline = new_data['deadline']

            self.db_session.commit()
            self.refresh()
            QMessageBox.information(self, "Успех", "Задача обновлена")

    def _delete_task(self, task_id):
        if not self._ensure_db():
            QMessageBox.warning(self, "Ошибка", "База данных не подключена")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить задачу и все связанные элементы?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            task = self.db_session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.is_active = False
                task.dt_end = datetime.now()
                self.db_session.commit()
                self.refresh()

    def _add_arch(self, task_id):
        QMessageBox.information(self, "Информация", "Диалог в разработке")

    def _add_entity_to_task(self, task_id):
        QMessageBox.information(self, "Информация", "Диалог выбора сущности в разработке")

    def _delete_arch(self, arch_id):
        if not self._ensure_db():
            QMessageBox.warning(self, "Ошибка", "База данных не подключена")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить архитектурное решение и связанные планы?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            arch = self.db_session.query(ArchSolution).filter(ArchSolution.id == arch_id).first()
            if arch:
                arch.is_active = False
                arch.dt_end = datetime.now()
                self.db_session.commit()
                self.refresh()

    def _add_plan(self, arch_id):
        QMessageBox.information(self, "Информация", "Диалог в разработке")

    def _edit_plan(self, plan_id):
        QMessageBox.information(self, "Информация", "Диалог в разработке")

    def _delete_plan(self, plan_id):
        if not self._ensure_db():
            QMessageBox.warning(self, "Ошибка", "База данных не подключена")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить план?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            plan = self.db_session.query(Plan).filter(Plan.id == plan_id).first()
            if plan:
                plan.is_active = False
                plan.dt_end = datetime.now()
                self.db_session.commit()
                self.refresh()

    def _remove_entity(self, entity_id):
        QMessageBox.information(self, "Информация", "Функция отвязки сущности в разработке")