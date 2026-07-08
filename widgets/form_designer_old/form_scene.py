# /home/sergey/Documents/configurate/widgets/form_designer_old/form_scene.py
"""
Модуль: Графическая сцена визуального проектирования форм Mozart ERP.

Роль в архитектуре Mozart ERP:
    - Ядро WYSIWYG-дизайнера. Управляет всеми графическими объектами на холсте.
    - Реализует паттерн Unit of Work (UoW) для отслеживания изменений перед сохранением.
    - Координирует работу миксинов: GridMixin, EventsMixin, ControlsMixin, SceneLoaderMixin.
    - Обеспечивает фокус и выделение контролов, обработку событий мыши и клавиатуры.
    - Предоставляет API для инициализации формы, добавления/удаления контролов.
    - Поддерживает отрицательные ID для новых контролов (маркер INSERT).
    - Реализует двухфазную инициализацию формы (временный ID "0" -> реальный ID из БД).

Ключевые зависимости:
    - FormBackground - визуальное представление бланка формы.
    - ResizeHandle - маркер изменения размеров.
    - FormObjectsRegistry - реестр метаданных объектов.
    - DesignerDataModel - in-memory хранилище свойств.
    - ControlItem - графический прокси-контейнер для контролов.
"""

import weakref
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF
from PySide6.QtGui import QPen, QColor

from .form_background import FormBackground
from .resize_handle import ResizeHandle
from .scene_grid_mixin import GridMixin
from .scene_events_mixin import EventsMixin
from .scene_controls_mixin import ControlsMixin
from .scene_loader_mixin import SceneLoaderMixin
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class FormDesignerScene(QGraphicsScene, GridMixin, EventsMixin, ControlsMixin, SceneLoaderMixin):
    """
    Графическая сцена визуального проектирования форм Mozart ERP.

    Назначение:
        - Хост для всех графических объектов (форма, контролы, маркеры).
        - Управление состоянием выделения и фокуса.
        - Реализация Unit of Work для атомарного сохранения.
        - Координация миксинов для разделения ответственности.
        - Единая точка входа для всех операций с формой.

    Ключевые свойства:
        - focused_control: ControlItem - Единственный источник истины для выделения.
        - deleted_control_ids: set[str] - ID контролов, помеченных на DELETE.
        - pending_inserts: list - Данные для INSERT (новые контролы с id < 0).
        - pending_updates: list - Данные для UPDATE (существующие контролы с id > 0).
        - background: FormBackground - Бланк формы на сцене.
        - controls: dict[str, ControlItem] - Все контролы на сцене (ключ = control_id).
        - _next_negative_id: int - Счетчик для генерации отрицательных ID.

    Основные методы:
        - init_form() - Инициализация бланка формы с временным ID "0".
        - reset_uow_state() - Сброс состояния Unit of Work.
        - prepare_save_data() - Подготовка данных для сохранения.
        - set_focused_control() - Централизованное управление фокусом.
        - load_controls() - Загрузка контролов из данных (из SceneLoaderMixin).
        - add_control() - Добавление контрола на сцену (из ControlsMixin).
        - delete_control() - Удаление контрола со сцены (из ControlsMixin).
    """

    # Сигналы
    control_selected = Signal(object)
    form_resized = Signal(float, float)
    form_geometry_changed = Signal()
    control_added = Signal(object)
    control_deleted = Signal(str)
    geometry_changed = Signal(str, int, int, int, int)
    save_requested = Signal()

    def __init__(self, parent=None):
        """
        Инициализация сцены дизайнера.

        Args:
            parent: QWidget - Родительский виджет
        """
        super().__init__(parent)

        # ==================== ПУНКТ 3.1.2.1 ====================
        # Unit of Work: Коллекции для отслеживания изменений перед сохранением
        self.deleted_control_ids = set()  # ID, помеченные на DELETE
        self.pending_inserts = []  # Данные для INSERT (id < 0)
        self.pending_updates = []  # Данные для UPDATE (id > 0)

        # Единственный источник истины для выделения
        self.focused_control = None

        # Базовые структуры
        self.background = None
        self.controls = {}
        self.selected_control = None
        self.db = None
        self._next_negative_id = -1

        # Настройка сцены
        self.setSceneRect(0, 0, 3000, 2000)
        self._init_grid()
        self._init_controls()

        # Инициализация контекстных метаданных (для EventsMixin)
        if hasattr(self, '_init_context_metadata'):
            self._init_context_metadata()

        # Подключение сигнала изменения выделения
        self.selectionChanged.connect(self._on_selection_changed)

    # ==================== ПУНКТ 3.1.2.1 ====================
    def reset_uow_state(self):
        """
        Сбрасывает состояние Unit of Work после успешного сохранения.

        Вызывается после успешного сохранения формы в БД.
        Очищает все коллекции изменений.
        """
        self.deleted_control_ids.clear()
        self.pending_inserts.clear()
        self.pending_updates.clear()
        print("[UOW] Состояние сохранения сброшено.")

    # ==================== ПУНКТ 3.1.2.1 ====================
    def prepare_save_data(self):
        """
        Подготавливает данные для сервиса сохранения на основе текущего состояния сцены.

        Собирает все контролы из реестра и распределяет их по категориям:
        - INSERT: контролы с отрицательным ID (новые)
        - UPDATE: контролы с положительным ID (существующие)
        - DELETE: контролы, помеченные на удаление

        Returns:
            dict: {
                'inserts': list - Данные для INSERT (id < 0),
                'updates': list - Данные для UPDATE (id > 0),
                'deletes': list - ID для DELETE
            }
        """
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        inserts = []
        updates = []

        # Перебираем все объекты в реестре
        for control_id, meta in registry._registry.items():
            # Пропускаем системные объекты и уже удаленные
            if control_id in self.deleted_control_ids or control_id in ('1', '840', 'form_root'):
                continue

            widget_ref = meta.get("widget_ref")
            if not widget_ref:
                continue

            widget_obj = widget_ref() if isinstance(widget_ref, weakref.ref) else widget_ref
            if not widget_obj:
                continue

            # Получаем данные из метаданных
            calias = meta.get("calias", "")
            cclass = meta.get("cclass", "")
            parentid = meta.get("parentid")

            # Получаем геометрию
            if hasattr(widget_obj, 'rect') and hasattr(widget_obj, 'pos'):
                pos, rect = widget_obj.pos(), widget_obj.rect()
                x, y = int(pos.x()), int(pos.y())
                width, height = int(rect.width()), int(rect.height())
            elif hasattr(widget_obj, 'geometry'):
                geo = widget_obj.geometry()
                x, y = geo.x(), geo.y()
                width, height = geo.width(), geo.height()
            else:
                x, y, width, height = 50, 50, 150, 30

            # Собираем свойства
            props = {
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }

            # Добавляем ERP-свойства из модели
            erp_props = ['label', 'binding_field', 'entity_alias', 'display_field',
                         'selector_form', 'is_required', 'is_readonly']
            for prop_name in erp_props:
                val = model.get_value(control_id, prop_name)
                if val:
                    props[prop_name] = val

            # Формируем данные
            data = {
                'id': control_id,
                'parentid': parentid,
                'calias': calias,
                'cclass': cclass,
                'properties': props
            }

            # ==================== ПУНКТ 3.1.2.1 ====================
            # Определяем, INSERT или UPDATE на основе знака ID
            try:
                num_id = int(control_id)
                if num_id < 0:
                    inserts.append(data)
                else:
                    updates.append(data)
            except (ValueError, TypeError):
                # Если ID не число, считаем, что это новый элемент
                inserts.append(data)

        return {
            'inserts': inserts,
            'updates': updates,
            'deletes': list(self.deleted_control_ids)
        }

    # ==================== ПУНКТ 3.1.2.1 ====================
    def mark_for_deletion(self, control_id):
        """
        Помечает контрол на удаление вместо немедленного стирания.

        Args:
            control_id: str - ID контрола для удаления
        """
        cid_str = str(control_id).strip()
        if cid_str and cid_str not in ('', 'form_root'):
            self.deleted_control_ids.add(cid_str)
            print(f"[UOW] Контрол {cid_str} помечен на удаление.")

    def _on_selection_changed(self):
        """
        Обработчик изменения выделения на сцене.
        Синхронизирует состояние фокуса и панели свойств.
        """
        selected_items = [i for i in self.selectedItems() if hasattr(i, 'control_id')]

        if len(selected_items) == 0:
            # Ничего не выбрано - сбрасываем фокус
            self.focused_control = None
            self.selected_control = None
            self.control_selected.emit(None)
        elif len(selected_items) == 1:
            # Выбран один контрол
            item = selected_items[0]
            self.focused_control = item
            self.selected_control = item
            self.control_selected.emit(item)

    def set_db(self, db):
        """
        Устанавливает подключение к БД.

        Args:
            db: DatabaseService - Сервис базы данных
        """
        self.db = db

    # ==================== ПУНКТ 2.1.2.1 ====================
    def set_focused_control(self, control_item):
        """
        Централизованное управление фокусом и маркером.

        Args:
            control_item: ControlItem - Контрол для установки фокуса
        """
        old_focus = self.focused_control
        self.focused_control = control_item

        # Очищаем старый фокус
        if old_focus and hasattr(old_focus, 'clear_internal_selection'):
            old_focus.clear_internal_selection()

        # Обновляем выделение на сцене
        if control_item:
            # Снимаем выделение со всех, кроме выбранного
            for item in self.selectedItems():
                if item != control_item and hasattr(item, 'setSelected'):
                    item.setSelected(False)
            if not control_item.isSelected():
                control_item.setSelected(True)
            self.selected_control = control_item
        else:
            self.clearSelection()
            self.selected_control = None

        # Сигнал о выборе контрола
        self.control_selected.emit(control_item)

    # ==================== ПУНКТ 1 + ДВУХФАЗНАЯ ИНИЦИАЛИЗАЦИЯ ====================
    def init_form(self, width: float, height: float, title: str = " ", form_id: str = "841") -> FormBackground:
        """
        Атомарная инициализация визуального бланка формы (Фаза 1).

        Создает новый бланк формы, очищает реестр и сбрасывает UOW.
        Регистрирует форму с временным ID "0" до получения данных из БД.

        Args:
            width: float - Ширина формы
            height: float - Высота формы
            title: str - Заголовок формы
            form_id: str - ID формы из БД (используется только для совместимости сигнатуры,
                           но НЕ для регистрации на этом этапе!)

        Returns:
            FormBackground - Созданный бланк формы
        """
        # ==================== ПУНКТ 3.1.2.1 ====================
        # Очищаем реестр и сбрасываем UOW
        FormObjectsRegistry().clear()
        self.reset_uow_state()
        self._next_negative_id = -1  # Сбрасываем счетчик ID

        # Удаляем старый бланк, если есть
        if self.background:
            for handle in getattr(self.background, '_handles', []):
                if handle and handle.scene() == self:
                    self.removeItem(handle)
            if self.background.scene() == self:
                self.removeItem(self.background)
            self.background = None

        # Создаем новый бланк
        self.background = FormBackground(width, height, title)
        self.background.setPos(0, 0)

        # ✅ ФАЗА 1: Присваиваем временный ID "0" ДО регистрации в реестре
        self.background.control_id = "0"

        self.addItem(self.background)

        # Подключаем сигналы бланка
        self.background.form_geometry_changed.connect(self._on_form_geometry_changed)
        self.background.form_resized.connect(self._on_form_resized)

        # Создаем маркер ресайза
        handle = ResizeHandle(4, self.background, parent=None)
        self.addItem(handle)
        self.background._handles = [handle]
        handle.setZValue(self.background.zValue() + 1000)
        self.background.update_handles_position()

        # ✅ РЕГИСТРИРУЕМ С ВРЕМЕННЫМ ID "0"
        registry = FormObjectsRegistry()
        registry.register_object(
            control_id="0",  # Временный ID до загрузки БД
            widget_obj=self.background,
            parentid=None,
            full_path="form_root",
            calias="OrdinaryDictionary",
            cclass="form"
        )
        print(f"[INIT_FORM] Форма зарегистрирована с временным ID='0'")

        # Сохраняем свойства бланка в модели по ключу "0"
        model = DesignerDataModel()
        model.set_value("0", "width", str(int(width)))
        model.set_value("0", "height", str(int(height)))
        model.set_value("0", "x", "0")
        model.set_value("0", "y", "0")
        model.set_value("0", "title", str(title))
        model.set_value("0", "form_alias", "OrdinaryDictionary")

        # Обновляем сцену
        self.setSceneRect(0, 0, 3000, 2000)
        self.update()

        # Центрируем вид
        for view in self.views():
            view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            view.centerOn(0.0, 0.0)
            QTimer.singleShot(0, lambda v=view: self._reset_view_scrollbars(v))

        return self.background

    def _on_form_geometry_changed(self):
        """Обработчик изменения геометрии формы."""
        self.form_geometry_changed.emit()

    def _on_form_resized(self, width, height):
        """Обработчик изменения размеров формы."""
        self.form_resized.emit(width, height)

    def _reset_view_scrollbars(self, view):
        """
        Сбрасывает позицию скроллбаров вьюхи.

        Args:
            view: QGraphicsView - Вьюха для сброса
        """
        if view and view.horizontalScrollBar():
            view.horizontalScrollBar().setValue(0)
        if view and view.verticalScrollBar():
            view.verticalScrollBar().setValue(0)

    def select_control(self, widget_or_item):
        """
        Выбирает контрол на сцене.

        Args:
            widget_or_item: QWidget or ControlItem - Объект для выбора
        """
        if widget_or_item:
            self.selected_control = widget_or_item
            if hasattr(widget_or_item, 'setSelected'):
                widget_or_item.setSelected(True)
                self.focused_control = widget_or_item
        else:
            self.selected_control = None
            self.focused_control = None
            self.clearSelection()
        self.control_selected.emit(self.selected_control)

    def clear_selection(self):
        """Снимает выделение со всех контролов."""
        self.clearSelection()
        self.selected_control = None
        self.focused_control = None
        self.control_selected.emit(None)

    def get_selected_control(self):
        """
        Возвращает текущий выбранный контрол.

        Returns:
            ControlItem or None - Выбранный контрол или None
        """
        return self.selected_control

    # ==================== ПУНКТ 3.1.2.1 ====================
    def get_inserts_count(self) -> int:
        """
        Возвращает количество новых контролов (для INSERT).

        Returns:
            int - Количество контролов с отрицательным ID
        """
        registry = FormObjectsRegistry()
        count = 0
        for cid in registry._registry.keys():
            try:
                if int(cid) < 0:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count

    # ==================== ПУНКТ 3.1.2.1 ====================
    def get_updates_count(self) -> int:
        """
        Возвращает количество существующих контролов (для UPDATE).

        Returns:
            int - Количество контролов с положительным ID
        """
        registry = FormObjectsRegistry()
        count = 0
        for cid in registry._registry.keys():
            try:
                if int(cid) > 0:
                    count += 1
            except (ValueError, TypeError):
                pass
        return count

    def has_unsaved_changes(self) -> bool:
        """
        Проверяет, есть ли несохраненные изменения.

        Returns:
            bool - True если есть изменения, иначе False
        """
        return (len(self.deleted_control_ids) > 0 or
                self.get_inserts_count() > 0 or
                self.get_updates_count() > 0)

    def drawForeground(self, painter, rect):
        """
        Переопределение отрисовки переднего плана.
        Рисует координатную сетку через FormBackground.
        """
        # Сетка рисуется в FormBackground.paint(), здесь ничего не делаем
        super().drawForeground(painter, rect)

    def drawBackground(self, painter, rect):
        """
        Переопределение отрисовки фона.
        Заливает фон сцены серым цветом.
        """
        painter.fillRect(rect, QColor(230, 230, 230))
        super().drawBackground(painter, rect)

    def update_handles_position(self):
        """
        Обновляет позицию маркеров ресайза.
        """
        if self.background and hasattr(self.background, 'update_handles_position'):
            self.background.update_handles_position()

    def get_controls_count(self) -> int:
        """
        Возвращает общее количество контролов на сцене.

        Returns:
            int - Количество контролов
        """
        return len(self.controls)

    def get_all_control_ids(self) -> list:
        """
        Возвращает список всех ID контролов на сцене.

        Returns:
            list[str] - Список control_id
        """
        return list(self.controls.keys())

    def get_control_by_id(self, control_id: str):
        """
        Возвращает контрол по его ID.

        Args:
            control_id: str - ID контрола

        Returns:
            ControlItem or None - Контрол или None
        """
        return self.controls.get(str(control_id))

    def is_control_exists(self, control_id: str) -> bool:
        """
        Проверяет существование контрола по ID.

        Args:
            control_id: str - ID контрола

        Returns:
            bool - True если контрол существует
        """
        return str(control_id) in self.controls