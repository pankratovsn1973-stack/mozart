# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/control_item.py

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QWidget, QGraphicsItem, QMenu, QGraphicsProxyWidget

# Импортируем все необходимые миксины
from .control_item_movement import ControlItemMovement
from .control_item_context import ControlItemContext
from .focus_registry import FocusRegistry


class ControlItem(ControlItemMovement, ControlItemContext, QGraphicsProxyWidget):
    """Главный управляющий класс графического прокси-контейнера на сцене визуального дизайнера.
    Идентификация строго через calias и коллекцию selectedItems()."""

    selected_changed = Signal(bool)
    geometry_changed = Signal(str, int, int, int, int)

    def __init__(self, widget, control_id, control_type, parent=None):
        # Инициализация миксинов в правильном порядке
        ControlItemMovement.__init__(self, widget, control_id, control_type, parent)
        QGraphicsProxyWidget.__init__(self, parent)

        self.control_id = str(control_id).strip()
        self._selected_child_widgets = []
        self._active_child_item = None
        self._focused_child_widget = None

        self.setWidget(widget)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def clear_internal_selection(self):
        """Сброс и скрытие маркеров изменения размеров."""
        if hasattr(self, '_selected_child_widgets') and self._selected_child_widgets:
            for handle in list(self._selected_child_widgets):
                if hasattr(handle, 'setVisible'):
                    handle.setVisible(False)
                if handle.scene():
                    try:
                        handle.scene().removeItem(handle)
                    except RuntimeError:
                        pass
            self._selected_child_widgets.clear()

        if self._active_child_item is not None or self._focused_child_widget is not None:
            self._active_child_item = None
            self._focused_child_widget = None

        self.update()

    def itemChange(self, change, value):
        """Автоматическая очистка маркеров при снятии нативного выделения Qt."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            is_selected = bool(value)
            if not is_selected:
                self.clear_internal_selection()
        return super().itemChange(change, value)

    def _get_calias(self, widget):
        """Безопасное получение calias у виджета."""
        # 1. Пробуем получить calias
        if hasattr(widget, 'calias'):
            calias = getattr(widget, 'calias', None)
            if calias:
                return str(calias).strip()

        # 2. Fallback: используем objectName
        obj_name = widget.objectName()
        if obj_name:
            # Обрезаем суффикс с ID, если есть (например, "btn_clear_of_ref_823" -> "btn_clear_of_ref")
            for internal_alias in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref'):
                if obj_name.startswith(internal_alias):
                    return internal_alias
            return obj_name

        return ""

    def handle_internal_click(self, event):
        """Активация контекста внутренней части составного референса при каскадном клике."""
        print(f"[INTERNAL_DIAG] handle_internal_click вызван для {self.control_id}")

        if not self.scene():
            return

        source_widget = self.widget()
        if not source_widget:
            return

        child = source_widget.childAt(event.pos().toPoint())
        if not child and event.widget():
            child = event.widget()

        if child and child != source_widget:
            child_calias = self._get_calias(child)
            if child_calias in ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref'):
                from .form_objects_registry import FormObjectsRegistry
                registry = FormObjectsRegistry()

                child_meta = registry.get_meta_by_parent_and_calias(self.control_id, child_calias)

                if child_meta:
                    print(f"[OK] Метаданные найдены по пути: Parent={self.control_id}, Calias={child_calias}")
                    self.scene()._active_context_container = self
                    self._active_child_item = child
                    self._focused_child_widget = child
                    event.accept()
                    self.update_handles_position()
                    self.update()
                    return
                else:
                    print(f"[FAIL] Метаданные НЕ найдены для Parent={self.control_id}, Calias={child_calias}")

        print(f"[INTERNAL_DIAG] Внутренний элемент не найден или не распознан")

    def update_handles_position(self):
        """Синхронизация положения маркера юго-восточного ресайза."""
        if self.scene() and self not in self.scene().selectedItems():
            self.clear_internal_selection()
            return

        if self.scene() and self.scene().focused_control != self:
            self.clear_internal_selection()
            return

        if not hasattr(self, '_selected_child_widgets') or self._selected_child_widgets is None:
            self._selected_child_widgets = []

        if not self._selected_child_widgets and self.scene():
            try:
                from .resize_handle import ResizeHandle
                handle = ResizeHandle(4, self, parent=None)
                self.scene().addItem(handle)
                handle.setZValue(self.zValue() + 1000)
                self._selected_child_widgets.append(handle)
            except Exception as e:
                print(f"[HANDLE_LOG] ОШИБКА создания ResizeHandle: {e}")

        for handle in self._selected_child_widgets:
            try:
                handle.update_position()
                handle.setVisible(True)
                if hasattr(handle, 'update'):
                    handle.update()
            except Exception as e:
                print(f"[HANDLE_LOG] Ошибка позиционирования хэндла: {e}")

    def paint(self, painter, option, widget):
        """Переопределение отрисовки: жесткое наложение FoxPro-style синей рамки выделения."""
        super().paint(painter, option, widget)

        if self.isSelected():
            from PySide6.QtGui import QPen, QColor
            painter.save()
            pen = QPen(QColor(0, 120, 215), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect = self.rect()
            painter.drawRect(rect)
            painter.restore()

    def setWidgetSize(self, width: float, height: float):
        """Изменяет размер контрола через нативный механизм QGraphicsProxyWidget."""
        w = max(20.0, float(width))
        h = max(15.0, float(height))

        self.setGeometry(self.pos().x(), self.pos().y(), w, h)

        widget = self.widget()
        if widget:
            widget.setFixedSize(int(w), int(h))
            if hasattr(widget, 'updateGeometry'):
                widget.updateGeometry()
            if hasattr(widget, 'update'):
                widget.update()

        self.update_handles_position()
        self.geometry_changed.emit(self.control_id, int(self.pos().x()), int(self.pos().y()), int(w), int(h))
        if self.scene():
            self.scene().update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Перехват клика мыши с полной диагностикой выделения внутренних элементов."""

        scene = self.scene()
        if not scene:
            return super().mousePressEvent(event)

        is_in_collection = self in scene.selectedItems()
        print(f"\n[DIAG_CLICK] === КЛИК НА {self.control_id} ({self.__class__.__name__}) ===")
        print(f"[DIAG_CLICK] 1. В глобальной коллекции selectedItems(): {'ДА' if is_in_collection else 'НЕТ'}")
        print(f"[DIAG_CLICK]    Текущий фокус сцены: {getattr(scene, 'focused_control', None)}")

        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:

            # Проверка маркера
            for handle in getattr(self, '_selected_child_widgets', []):
                if handle.isVisible():
                    local_pos = handle.mapFromScene(event.scenePos())
                    if handle.contains(local_pos):
                        print(f"[DIAG_CLICK] -> Действие: Клик по маркеру ресайза")
                        return

            # Диагностика 2: Определение типа контрола через реестр
            is_internal_child = False
            parent_id_in_registry = None

            try:
                from .form_objects_registry import FormObjectsRegistry
                registry = FormObjectsRegistry()

                # Ищем по САМОМУ ControlItem (self), а не по внутреннему widget
                meta = registry.get_meta_by_widget(self)

                if meta:
                    parent_id_in_registry = meta.get('parent_id') or meta.get('parent_container_id')
                    reg_calias = meta.get('calias', 'N/A')
                    reg_path = meta.get('full_path', 'N/A')
                    reg_control_id = meta.get('control_id', 'N/A')

                    print(f"[DIAG_CLICK] 2. Реестр нашел запись по ControlItem:")
                    print(f"       - control_id: {reg_control_id}")
                    print(f"       - calias: {reg_calias}")
                    print(f"       - full_path: {reg_path}")
                    print(f"       - parent_container_id: {parent_id_in_registry}")

                    is_internal_child = bool(
                        parent_id_in_registry and
                        str(parent_id_in_registry).strip() not in ('', 'None', 'form_root')
                    )
                    print(f"       - Статус 'is_internal_child': {is_internal_child}")
                else:
                    print(f"[DIAG_CLICK] 2. Реестр НЕ нашел запись для ControlItem id={id(self)}")
                    is_internal_child = False

            except Exception as e:
                print(f"[DIAG_CLICK] 2. Ошибка при проверке реестра: {e}")
                is_internal_child = False

            # 3. ГЛАВНОЕ ПРАВИЛО: Если нас нет в selectedItems — СБРОС И ВЫДЕЛЕНИЕ
            if not is_in_collection:
                print(f"[DIAG_CLICK] 3. Контрол НЕ в коллекции. Проверяем тип...")

                if is_internal_child:
                    print(f"[DIAG_CLICK]    -> Это ВНУТРЕННИЙ элемент. Пропускаем clearSelection().")
                    print(f"[DIAG_CLICK]    -> Переходим сразу к каскадной логике.")
                else:
                    print(f"[DIAG_CLICK]    -> Это КОРНЕВОЙ элемент. Выполняем ПОЛНЫЙ СБРОС.")
                    modifiers = event.modifiers()

                    if not (modifiers & Qt.KeyboardModifier.ControlModifier):
                        scene.clearSelection()
                        FocusRegistry().reset_active_context()
                        print(f"[DIAG_CLICK]    -> Коллекция после clearSelection: {len(scene.selectedItems())} эл.")

                    self._active_child_item = None
                    self._focused_child_widget = None
                    self.clear_internal_selection()

                    print(f"[DIAG_CLICK]    -> Выделение контейнера (setSelected=True)")
                    self.setSelected(True)
                    scene.set_focused_control(self)

                    self.update()
                    self.update_handles_position()

                    print(
                        f"[DIAG_CLICK]    -> Статус после выделения: {'ЕСТЬ' if self in scene.selectedItems() else 'НЕТ'}")

                    event.accept()
                    ControlItemMovement.mousePressEvent(self, event)
                    return

            # 4. УРОВЕНЬ Б: КОНТРОЛ УЖЕ В КОЛЛЕКЦИИ ИЛИ ВНУТРЕННИЙ ЭЛЕМЕНТ -> КАСКАДНЫЙ КЛИК
            print(f"[DIAG_CLICK] 4. Проверка каскадного клика...")

            source_widget = self.widget()
            clicked_child_name = "NONE"

            if source_widget:
                child = source_widget.childAt(event.pos().toPoint())
                if not child and event.widget():
                    child = event.widget()

                if child:
                    clicked_child_name = self._get_calias(child) or child.objectName()
                    print(f"[DIAG_CLICK]    -> childAt вернул: {clicked_child_name}")
                    print(f"[DIAG_CLICK]       Тип ребенка: {type(child).__name__}")

                    if child != source_widget:
                        internal_aliases = ('txt_of_ref', 'btn_select_of_ref', 'btn_clear_of_ref', 'lbl_of_ref')

                        if clicked_child_name in internal_aliases:
                            print(
                                f"[DIAG_CLICK]    -> СОВПАДЕНИЕ! Вызываем handle_internal_click для {clicked_child_name}")
                            self.handle_internal_click(event)
                            event.accept()
                            return
                        else:
                            print(
                                f"[DIAG_CLICK]    -> Имя '{clicked_child_name}' НЕ входит в список внутренних алиасов")
                    else:
                        print(f"[DIAG_CLICK]    -> child == source_widget (клик по самому контейнеру)")
                else:
                    print(f"[DIAG_CLICK]    -> childAt вернул None")
            else:
                print(f"[DIAG_CLICK]    -> source_widget отсутствует")

            # 5. СТАНДАРТНЫЙ ДРАГ (только для корневых контролов)
            if not is_internal_child:
                print(f"[DIAG_CLICK] 5. Стандартный драг корневого контрола")
                event.accept()
                ControlItemMovement.mousePressEvent(self, event)
                return
            else:
                print(f"[DIAG_CLICK] 5. Внутренний элемент: драг запрещен, событие игнорируется")

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Переопределение для делегирования движения миксину."""
        if self._is_dragging:
            ControlItemMovement.mouseMoveEvent(self, event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Переопределение для завершения движения."""
        if self._is_dragging:
            ControlItemMovement.mouseReleaseEvent(self, event)
        else:
            super().mouseReleaseEvent(event)

    def _show_context_menu(self, event):
        """Контекстное меню групповых операций для выделенных контролов."""
        if not self.scene():
            return

        selected_items = [i for i in self.scene().selectedItems() if isinstance(i, ControlItem)]
        if len(selected_items) < 1:
            return

        menu = QMenu(self.widget())
        has_group = len(selected_items) > 1

        act_same_size = menu.addAction("Одинаковый размер")
        act_same_size.setEnabled(has_group)
        menu.addSeparator()

        act_left = menu.addAction("Выровнять по левому краю")
        act_top = menu.addAction("Выровнять по верхнему краю")
        act_right = menu.addAction("Выровнять по правому краю")
        act_bottom = menu.addAction("Выровнять по нижнему краю")

        for act in [act_left, act_top, act_right, act_bottom]:
            act.setEnabled(has_group)

        action = menu.exec(event.screenPos())

        if action and has_group:
            master = selected_items[0]
            master_rect = master.rect()
            master_pos = master.pos()

            for item in selected_items:
                if item == master:
                    continue

                if action == act_same_size:
                    item.setWidgetSize(master_rect.width(), master_rect.height())
                elif action == act_left:
                    item.setPos(master_pos.x(), item.pos().y())
                elif action == act_top:
                    item.setPos(item.pos().x(), master_pos.y())
                elif action == act_right:
                    new_x = master_pos.x() + master_rect.width() - item.rect().width()
                    item.setPos(new_x, item.pos().y())
                elif action == act_bottom:
                    new_y = master_pos.y() + master_rect.height() - item.rect().height()
                    item.setPos(item.pos().x(), new_y)

            for item in selected_items:
                if hasattr(item, 'update_handles_position'):
                    item.update_handles_position()
            self.scene().update()