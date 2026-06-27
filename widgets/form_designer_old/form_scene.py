# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/form_scene.py

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, Signal, QTimer
from .form_background import FormBackground
from .resize_handle import ResizeHandle
from .scene_grid_mixin import GridMixin
from .scene_events_mixin import EventsMixin
from .scene_controls_mixin import ControlsMixin
from .scene_loader_mixin import SceneLoaderMixin
from .form_objects_registry import FormObjectsRegistry


class FormDesignerScene(QGraphicsScene, GridMixin, EventsMixin, ControlsMixin, SceneLoaderMixin):
    """Графическая сцена визуального проектирования форм Mozart ERP.
    Реализует паттерн Unit of Work для управления состоянием сохранения."""

    control_selected = Signal(object)
    form_resized = Signal(float, float)
    form_geometry_changed = Signal()
    control_added = Signal(object)
    control_deleted = Signal(str)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ✅ ЕДИНСТВЕННЫЙ ИСТОЧНИК ИСТИНЫ ДЛЯ ВЫДЕЛЕНИЯ
        self.focused_control = None

        # ✅ UNIT OF WORK: Коллекции для отслеживания изменений перед сохранением
        self.deleted_control_ids = set()  # ID, помеченные на DELETE
        self.pending_inserts = []  # Данные для INSERT (id=0)
        self.pending_updates = []  # Данные для UPDATE (id!=0)

        self.background = None
        self.controls = {}
        self.selected_control = None
        self.db = None

        self.setSceneRect(0, 0, 3000, 2000)
        self._init_grid()
        self._init_controls()

        if hasattr(self, '_init_context_metadata'):
            self._init_context_metadata()

    def reset_uow_state(self):
        """Сбрасывает состояние Unit of Work после успешного сохранения."""
        self.deleted_control_ids.clear()
        self.pending_inserts.clear()
        self.pending_updates.clear()
        print("[UOW] Состояние сохранения сброшено.")

    def mark_for_deletion(self, control_id):
        """Помечает контрол на удаление вместо немедленного стирания."""
        cid_str = str(control_id).strip()
        if cid_str and cid_str not in ('', 'form_root'):
            self.deleted_control_ids.add(cid_str)
            print(f"[UOW] Контрол {cid_str} помечен на удаление.")

    def prepare_save_data(self):
        """Подготавливает данные для сервиса сохранения на основе текущего состояния сцены."""
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        inserts = []
        updates = []

        for obj_ptr, meta in list(registry._registry.items()):
            widget_ref = meta["widget_ref"]
            control_id = str(meta.get("control_id", "")).strip()

            # Пропускаем системные объекты и уже удаленные
            if control_id in self.deleted_control_ids or control_id in ('1', '840', 'form_root'):
                continue

            calias = getattr(widget_ref, 'calias', meta.get('object_name', ''))
            cclass = model.get_value(control_id, "control_type") or widget_ref.__class__.__name__.lower()
            full_path = meta.get('full_path', '')

            # Получаем геометрию из прокси или виджета
            pos = widget_ref.pos() if hasattr(widget_ref, 'pos') else QPointF(0, 0)
            rect = widget_ref.rect() if hasattr(widget_ref, 'rect') else QRectF(0, 0, 100, 30)

            data = {
                'id': control_id if control_id != '0' else None,  # None = новый элемент
                'parentid': meta.get('parent_container_id'),
                'calias': calias,
                'cclass': cclass,
                'full_path': full_path,
                'properties': {
                    'x': int(pos.x()),
                    'y': int(pos.y()),
                    'width': int(rect.width()),
                    'height': int(rect.height())
                }
            }

            if control_id == '0' or not control_id:
                inserts.append(data)
            else:
                updates.append(data)

        return {
            'inserts': inserts,
            'updates': updates,
            'deletes': list(self.deleted_control_ids)
        }

    def set_db(self, db):
        self.db = db

    def set_focused_control(self, control_item):
        """Централизованное управление фокусом и маркером."""
        old_focus = self.focused_control
        self.focused_control = control_item

        if old_focus and hasattr(old_focus, 'clear_internal_selection'):
            old_focus.clear_internal_selection()

        self.control_selected.emit(control_item)

    def init_form(self, width: float, height: float, title: str = " ") -> FormBackground:
        """Атомарная инициализация визуального бланка формы."""
        FormObjectsRegistry().clear_registry()
        self.reset_uow_state()  # ✅ Сброс UOW при новой форме

        if self.background:
            for handle in getattr(self.background, '_handles', []):
                if handle and handle.scene() == self:
                    self.removeItem(handle)
            if self.background.scene() == self:
                self.removeItem(self.background)
            self.background = None

        self.background = FormBackground(width, height, title)
        self.background.setPos(0, 0)
        self.addItem(self.background)

        self.background.form_geometry_changed.connect(lambda: self.form_geometry_changed.emit())
        self.background.form_resized.connect(lambda w, h: self.form_resized.emit(w, h))

        handle = ResizeHandle(4, self.background, parent=None)
        self.addItem(handle)
        self.background._handles = [handle]
        handle.setZValue(self.background.zValue() + 1000)

        self.background.update_handles_position()

        self.setSceneRect(0, 0, 3000, 2000)
        self.update()

        for view in self.views():
            view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            view.centerOn(0.0, 0.0)
            QTimer.singleShot(0, lambda v=view: self._reset_view_scrollbars(v))

        return self.background

    def _reset_view_scrollbars(self, view):
        if view and view.horizontalScrollBar():
            view.horizontalScrollBar().setValue(0)
        if view and view.verticalScrollBar():
            view.verticalScrollBar().setValue(0)

    def select_control(self, widget_or_item):
        self.selected_control = widget_or_item if widget_or_item else self.background
        self.control_selected.emit(self.selected_control)