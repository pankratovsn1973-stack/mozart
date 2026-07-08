# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_loader_mixin.py
"""
Модуль: Миксин загрузки контролов на сцену дизайнера.

Роль в архитектуре Mozart ERP:
    - Загрузка контролов из БД (meta.form_elements) на графическую сцену.
    - Поддержка жизненного цикла составных контролов (Reference):
        * Первичная загрузка: генерация дефолтных подконтролов с отрицательными ID.
        * Вторичная загрузка: восстановление сохраненных пропертей подконтролов.
    - Интеграция с FormObjectsRegistry и DesignerDataModel.
    - Топологическая сортировка для правильного порядка создания (родители раньше детей).
    - Реализация двухфазной инициализации формы (замена временного ID "0" на реальный из БД).

Ключевые зависимости:
    - FormObjectsRegistry - для регистрации контролов.
    - DesignerDataModel - для хранения свойств.
    - controls.create_control - фабрика создания контролов.
"""

import weakref
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class SceneLoaderMixin:
    """
    Миксин сцены: загрузка из meta.form_elements с поддержкой Unit of Work.

    Назначение:
        - Загрузка контролов из данных БД на сцену.
        - Топологическая сортировка для правильной иерархии.
        - Генерация дефолтных подконтролов для Reference.
        - Восстановление сохраненных пропертей подконтролов.
        - Атомарная замена временного ID формы на реальный ID из БД.

    Ключевые свойства:
        - id_to_calias_map: dict[str, str] - Маппинг ID -> calias для построения путей.
        - node_map_by_id: dict[str, dict] - Маппинг ID -> данные контрола.

    Основные методы:
        - load_controls() - Основной метод загрузки контролов.
        - _ensure_internal_controls_exist() - Создание подконтролов для Reference.
        - _build_full_path_from_ids() - Построение полного пути в иерархии.
        - _register_internal_widget() - Регистрация внутреннего элемента.
        - _dump_registry() - Отладочный вывод реестра.
    """

    # ==================== ПУНКТ 4.1.1.1 ====================
    def _ensure_internal_controls_exist(self, ref_id, ref_widget):
        """
        Создает внутренние элементы референса, если их нет в БД.

        Вызывается для Reference-контролов при первой загрузке.
        Создает стандартные подконтролы: txt_of_ref, btn_select_of_ref,
        btn_clear_of_ref, lbl_of_ref с отрицательными ID.

        Args:
            ref_id: str - ID родительского референса
            ref_widget: QWidget - Виджет референса

        Returns:
            int - Количество созданных подконтролов
        """
        # Стандартные внутренние элементы референса
        internal_types = [
            ('txt_of_ref', 'textbox', 'QLabel'),
            ('btn_select_of_ref', 'button', 'QPushButton'),
            ('btn_clear_of_ref', 'button', 'QPushButton'),
            ('lbl_of_ref', 'label', 'QLabel')
        ]

        existing_children = set()
        # Собираем существующие calias дочерних элементов
        for child in ref_widget.findChildren(QWidget):
            child_calias = getattr(child, 'calias', None)
            if child_calias:
                existing_children.add(child_calias)
            else:
                # Проверяем по objectName
                obj_name = child.objectName()
                for base_alias, _, _ in internal_types:
                    if obj_name.startswith(base_alias):
                        existing_children.add(base_alias)
                        break

        created_count = 0
        model = DesignerDataModel()

        for base_alias, cclass, widget_class in internal_types:
            # Пропускаем, если уже существует
            if base_alias in existing_children:
                continue

            # Создаем виджет в зависимости от типа
            if widget_class == 'QLabel':
                widget = QLabel(ref_widget)
                if base_alias == 'txt_of_ref':
                    widget.setStyleSheet(
                        "border: 1px solid #b0b0b0; background-color: #ffffff; "
                        "padding-left: 5px; color: #555555;"
                    )
                    widget.setText("[Справочник]")
                else:
                    widget.setText(base_alias.upper())
            elif widget_class == 'QPushButton':
                widget = QPushButton(ref_widget)
                if base_alias == 'btn_select_of_ref':
                    widget.setText("📁")
                    widget.setFixedWidth(28)
                elif base_alias == 'btn_clear_of_ref':
                    widget.setText("✖")
                    widget.setFixedWidth(28)
                else:
                    widget.setText("...")
            else:
                widget = QLabel(ref_widget)
                widget.setText(base_alias)

            # ==================== ПУНКТ 3.1.1.1 ====================
            # Генерируем отрицательный ID для нового подконтрола
            control_id = self._generate_negative_id()

            # Сохраняем свойства в модели
            model.set_value(control_id, "control_type", cclass)
            model.set_value(control_id, "form_calias", base_alias)
            model.set_value(control_id, "parent_id", ref_id)

            # Регистрируем в реестре
            full_path = self._build_full_path_from_ids(ref_id)
            self._register_internal_widget(
                widget,
                ref_id,
                base_alias,
                explicit_id=control_id,
                full_path=f"{full_path}.{base_alias}"
            )

            # Устанавливаем видимость
            widget.show()
            created_count += 1

        if created_count > 0:
            print(f"[LOADER_CREATE] Создано {created_count} подконтролов для референса {ref_id}")

        return created_count

    # ==================== ПУНКТ 4.1.1.2 ====================
    def _register_internal_widget(self, widget, ref_id, base_alias, explicit_id=None, full_path=""):
        """
        Централизованная регистрация внутреннего элемента.

        ВАЖНО: calias остается БАЗОВЫМ (без суффикса ID) для корректного поиска.

        Args:
            widget: QWidget - Виджет для регистрации
            ref_id: str - ID родительского референса
            base_alias: str - Базовый алиас (txt_of_ref, btn_select_of_ref, etc.)
            explicit_id: str - ID из БД (или отрицательный для новых)
            full_path: str - Полный путь в иерархии
        """
        registry = FormObjectsRegistry()

        # Уникальное имя ТОЛЬКО для Qt (чтобы не было коллизий внутри формы)
        unique_qt_name = f"{base_alias}_{ref_id}"
        if widget.objectName() != unique_qt_name:
            widget.setObjectName(unique_qt_name)

        # Присваиваем БАЗОВЫЙ calias как бизнес-атрибут
        widget.calias = base_alias

        # Регистрация в глобальной коллекции с чистым calias
        registry.register_object(
            control_id=explicit_id,
            widget_obj=widget,
            parentid=ref_id,
            full_path=full_path,
            calias=base_alias,
            cclass=widget.__class__.__name__.lower()
        )

    def _build_full_path_from_ids(self, parent_id):
        """
        Строит путь ИЗ CALIAS, но навигацию ведет ПО ID (parentid).

        Args:
            parent_id: str - ID родительского контрола

        Returns:
            str - Полный путь в иерархии (например, "tab1.ref1")
        """
        if not parent_id or str(parent_id).strip() in ('', 'form_root'):
            return ""

        path_parts = []
        current_pid = str(parent_id).strip()
        max_depth = 50
        visited = set()

        while current_pid and current_pid != "form_root" and len(path_parts) < max_depth:
            if current_pid in visited:
                break
            visited.add(current_pid)

            # Получаем алиас из карты
            alias = getattr(self, 'id_to_calias_map', {}).get(current_pid)
            if alias:
                path_parts.append(alias)

            # Переходим к родителю
            parent_data = getattr(self, 'node_map_by_id', {}).get(current_pid)
            if parent_data:
                current_pid = str(parent_data.get('parentid', '')).strip()
            else:
                break

        path_parts.reverse()
        return ".".join(path_parts)

    # ==================== ПУНКТ 4.1.1.2 + ДВУХФАЗНАЯ ИНИЦИАЛИЗАЦИЯ ====================
    def load_controls(self, controls_data):
        """
        Загрузка контролов из данных на сцену.

        Процесс загрузки:
        1. Индексация всех элементов (ID -> данные, ID -> calias)
        2. Топологическая сортировка (родители раньше детей)
        3. Для каждого элемента:
           a. Если это форма - ЗАМЕНЯЕМ временный ID "0" на реальный из БД (Фаза 2)
           b. Если это Reference - создаем/восстанавливаем подконтролы
           c. Создаем основной контрол
           d. Регистрируем в реестре
           e. Применяем свойства

        Args:
            controls_data: list[dict] - Данные контролов из БД
        """
        if not controls_data:
            return

        from controls import create_control
        created_items_map = {}
        registry = FormObjectsRegistry()
        model = DesignerDataModel()

        print(f"\n[LOADER_START] Начинается загрузка {len(controls_data)} элементов...")

        # ======================================================================
        # ШАГ 0: ИНДЕКСАЦИЯ (ID -> calias, ID -> данные)
        # ======================================================================
        self.id_to_calias_map = {"form_root": "OrdinaryDictionary"}
        self.node_map_by_id = {}

        for data in controls_data:
            cid = str(data.get('id', '')).strip()
            calias = str(data.get('calias', '')).strip()
            if cid and calias:
                self.id_to_calias_map[cid] = calias
                self.node_map_by_id[cid] = data

        # ======================================================================
        # ШАГ 1: ТОПОЛОГИЧЕСКАЯ СОРТИРОВКА (по parentid)
        # ======================================================================
        sorted_ids = []
        visited = set()
        temp_mark = set()

        def visit(node_id):
            if node_id in temp_mark or node_id in visited:
                return
            temp_mark.add(node_id)

            node = self.node_map_by_id.get(node_id)
            if node:
                pid = str(node.get('parentid', '')).strip()
                if pid and pid != "form_root" and pid in self.node_map_by_id:
                    visit(pid)

            temp_mark.discard(node_id)
            visited.add(node_id)
            sorted_ids.append(node_id)

        for d in controls_data:
            visit(str(d['id']))

        ordered_controls_data = [self.node_map_by_id[sid] for sid in sorted_ids
                                 if sid in self.node_map_by_id]
        print(f"[LOADER_SORT] Отсортировано {len(ordered_controls_data)} элементов для загрузки.")

        # ======================================================================
        # ШАГ 2: ФИЗИЧЕСКАЯ ГЕНЕРАЦИЯ И МАСКИРОВАНИЕ
        # ======================================================================
        for data in ordered_controls_data:
            try:
                cclass = str(data.get('cclass', 'textbox')).lower()
                control_id = str(data.get('id', ''))
                calias = str(data.get('calias', '')).strip()
                props = data.get('properties', {})

                # Пропускаем системные элементы
                if cclass in ('formbackground', 'formbackgroundsignals') or \
                        control_id in ('1', '840') or calias == 'control_840':
                    print(f"[LOADER_SKIP] Пропускаем системный элемент: ID={control_id}, Class={cclass}")
                    continue

                # ==================== ФАЗА 2: ЗАМЕНА ВРЕМЕННОГО ID ФОРМЫ НА РЕАЛЬНЫЙ ====================
                if cclass == 'form':
                    real_db_id = str(control_id)
                    print(f"[LOADER_FORM] ФАЗА 2: Замена временного ID='0' на реальный ID='{real_db_id}'")

                    if hasattr(self, 'background') and self.background:
                        # 1. Обновляем геометрию и свойства визуального объекта
                        form_width = props.get('width', 967)
                        form_height = props.get('height', 438)
                        form_title = props.get('title', calias)
                        form_x = props.get('x', 0)
                        form_y = props.get('y', 0)

                        self.background.update_geometry(form_x, form_y, form_width, form_height)
                        self.background.title = form_title
                        self.background.form_alias = calias

                        # ✅ КРИТИЧЕСКИ ВАЖНО: Обновляем атрибут control_id у самого виджета
                        self.background.control_id = real_db_id

                        if hasattr(self.background, 'update'):
                            self.background.update()

                        # 2. АТОМАРНАЯ ЗАМЕНА ЗАПИСИ В РЕЕСТРЕ
                        old_wid = id(self.background)

                        # Удаляем старую запись с ID="0"
                        if "0" in registry._registry:
                            del registry._registry["0"]
                            print(f"[LOADER_FORM] Удалена временная запись ID='0' из _registry")

                        # Удаляем старый маппинг wid->cid
                        if old_wid in registry._wid_to_cid_map:
                            del registry._wid_to_cid_map[old_wid]

                        # Удаляем старый индекс по пути (если был создан для "0")
                        path_key = ("None", "OrdinaryDictionary")
                        if path_key in registry._index_by_path:
                            del registry._index_by_path[path_key]

                        # Создаем новую запись с реальным ID
                        registry.register_object(
                            control_id=real_db_id,
                            widget_obj=self.background,
                            parentid=None,
                            full_path="form_root",
                            calias=calias,
                            cclass="form"
                        )
                        print(f"[LOADER_FORM] Создана новая запись ID='{real_db_id}' в реестре")

                        # 3. Переносим свойства в модель с новым ключом
                        model.set_value(real_db_id, "width", str(int(form_width)))
                        model.set_value(real_db_id, "height", str(int(form_height)))
                        model.set_value(real_db_id, "x", str(int(form_x)))
                        model.set_value(real_db_id, "y", str(int(form_y)))
                        model.set_value(real_db_id, "title", str(form_title))
                        model.set_value(real_db_id, "form_alias", calias)

                        # Удаляем старые свойства с ключом "0"
                        for prop_key in ["width", "height", "x", "y", "title", "form_alias"]:
                            if ("0", prop_key) in model.properties_instances:
                                del model.properties_instances[("0", prop_key)]

                        # 4. Добавляем в map для родительских связей дочерних элементов
                        created_items_map[real_db_id] = self.background

                        print(f"[LOADER_FORM] Форма успешно обновлена: ID='0' -> ID='{real_db_id}', "
                              f"Size={form_width}x{form_height}, Title={form_title}")
                    continue

                # ==================== ОСТАЛЬНЫЕ КОНТРОЛЫ ====================

                # Извлекаем геометрию
                x = int(float(props.pop('x', 50)))
                y = int(float(props.pop('y', 50)))
                width = int(float(props.pop('width', 150)))
                height = int(float(props.pop('height', 30)))

                # Находим родителя
                parent_id = data.get('parentid')
                parent_item = None

                if parent_id:
                    # Сначала ищем в created_items_map (там теперь есть форма с реальным ID)
                    parent_item = created_items_map.get(str(parent_id))

                    # Если не нашли - ищем в controls (для ранее созданных контролов)
                    if not parent_item:
                        for cid, item in self.controls.items():
                            if cid == str(parent_id):
                                parent_item = item
                                break

                widget = None

                print(f"[LOADER_PROC] Обработка: ID={control_id}, Alias={calias}, "
                      f"Class={cclass}, Parent={parent_id}")

                # ------------------------------------------------------------------
                # ПУНКТ 4.1.1.2: ВОССТАНОВЛЕНИЕ СУЩЕСТВУЮЩИХ ПОДКОНТРОЛОВ
                # ------------------------------------------------------------------
                if parent_item and hasattr(parent_item, 'widget') and parent_item.widget():
                    parent_widget = parent_item.widget()
                    for child in parent_widget.findChildren(QWidget):
                        child_calias = getattr(child, 'calias', child.objectName()).strip()

                        if child_calias == calias and child.parent() is parent_widget:
                            widget = child
                            # Обновляем регистрацию с правильным ID
                            self._register_internal_widget(
                                child,
                                parent_id,
                                calias,
                                explicit_id=control_id,
                                full_path=self._build_full_path_from_ids(control_id)
                            )

                            # Применяем сохраненные свойства
                            if hasattr(child, 'properties') and isinstance(child.properties, dict):
                                child.properties.update(props)

                            print(f"[LOADER_FOUND] Найден и обновлен: {calias} "
                                  f"для Parent={parent_id}")
                            break

                # Если внутренний элемент найден и обработан — переходим к следующему
                if parent_item and widget:
                    continue

                # ------------------------------------------------------------------
                # ПУНКТ 4.1.1.1: ГЕНЕРАЦИЯ НОВЫХ ПОДКОНТРОЛОВ ДЛЯ REFERENCE
                # ------------------------------------------------------------------
                if cclass == 'reference':
                    # Сначала создаем основной виджет
                    widget = create_control(cclass, parent=None, db=self.db)
                    if not widget:
                        continue

                    # Применяем свойства к основному виджету
                    if hasattr(widget, 'properties'):
                        widget.properties = props

                    # Создаем подконтролы (если их нет)
                    if hasattr(widget, 'findChildren'):
                        created = self._ensure_internal_controls_exist(control_id, widget)
                        if created > 0:
                            print(f"[LOADER_CREATE] Создано {created} подконтролов "
                                  f"для референса {calias} (ID={control_id})")

                    # Переключаем в режим дизайна
                    if hasattr(widget, 'set_design_mode'):
                        widget.set_design_mode(True)
                        if hasattr(widget, 'edit_design') and widget.edit_design:
                            widget.edit_design.setVisible(True)

                # ------------------------------------------------------------------
                # СОЗДАНИЕ ОБЫЧНОГО КОНТРОЛА
                # ------------------------------------------------------------------
                else:
                    widget = create_control(cclass, parent=None, db=self.db)
                    if not widget:
                        continue

                    if hasattr(widget, 'properties'):
                        widget.properties = props

                    if hasattr(widget, 'set_design_mode'):
                        widget.set_design_mode(True)

                # Устанавливаем атрибуты
                if widget:
                    widget.calias = calias
                    widget.setObjectName(calias)
                    try:
                        widget.setFixedSize(width, height)
                    except:
                        pass

                    # Регистрируем в реестре
                    full_path = self._build_full_path_from_ids(control_id)
                    registry.register_object(
                        control_id=control_id,
                        widget_obj=widget,
                        parentid=parent_id,
                        full_path=full_path,
                        calias=calias,
                        cclass=cclass
                    )

                    # Добавляем на сцену
                    item = self.add_control(
                        widget,
                        control_id,
                        cclass,
                        x, y,
                        parent_item=parent_item,
                        calias=calias,
                        full_path=full_path
                    )

                    if item and parent_item:
                        item.setZValue(1.0)
                        item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, True)
                        item.setFlag(item.GraphicsItemFlag.ItemIsFocusable, True)

                    if item:
                        created_items_map[str(control_id)] = item
                        item.updateGeometry()

            except Exception as e:
                print(f"[SceneLoaderMixin] Ошибка загрузки контрола: {e}")
                import traceback
                traceback.print_exc()

        # ======================================================================
        # ШАГ 3: ВЫВОД ДИАГНОСТИКИ
        # ======================================================================
        print(f"[DIAG] ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ДАМПОМ: registry._registry.keys() = {list(registry._registry.keys())}")

        self._dump_registry()

    def _dump_registry(self):
        """
        Выводит полную карту реестра для отладки.
        """
        registry = FormObjectsRegistry()
        print("\n" + "=" * 120)
        print(f"🗺️  ПОЛНАЯ КАРТА РЕЕСТРА ({len(registry._registry)} объектов):")
        print(f"{'CONTROL_ID (KEY)':<20} | {'CALIAS':<30} | {'PARENTID':<15} | {'CCLASS':<15} | {'FULL_PATH'}")
        print("-" * 120)
        for cid, meta in registry._registry.items():
            calias = meta.get('calias', 'N/A')
            parentid = meta.get('parentid', 'None')
            cclass = meta.get('cclass', 'N/A')
            path = meta.get('full_path', 'N/A')
            print(f"{cid:<20} | {calias:<30} | {str(parentid):<15} | {cclass:<15} | {path}")
        print("=" * 120 + "\n")

    def delete_control(self, control_id):
        """
        Удаление контрола с каскадным удалением дочерних элементов.

        Args:
            control_id: str - ID контрола для удаления
        """
        cid_str = str(control_id).strip()
        if cid_str not in self.controls:
            return

        item = self.controls[cid_str]

        # Удаляем дочерние элементы сначала
        registry = FormObjectsRegistry()
        children_to_delete = []
        for cid, meta in registry._registry.items():
            if meta.get("parentid") == cid_str:
                children_to_delete.append(cid)

        for child_id in children_to_delete:
            self.delete_control(child_id)

        # Удаляем сам контрол
        if self.selected_control == item:
            self.selected_control = None
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

        if item and item.scene() == self:
            self.removeItem(item)

        del self.controls[cid_str]

        # Помечаем на удаление в UOW
        if hasattr(self, 'deleted_control_ids'):
            self.deleted_control_ids.add(cid_str)

        # Удаляем из реестра
        if cid_str in registry._registry:
            del registry._registry[cid_str]

        if hasattr(self, 'control_deleted'):
            self.control_deleted.emit(cid_str)