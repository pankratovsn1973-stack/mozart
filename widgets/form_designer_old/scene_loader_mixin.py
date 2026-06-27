# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/widgets/form_designer_old/scene_loader_mixin.py

import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QPushButton
from .form_objects_registry import FormObjectsRegistry
from .designer_data_model import DesignerDataModel


class SceneLoaderMixin:
    """Миксин сцены: загрузка из meta.form_elements с поддержкой Unit of Work (ID=0)."""

    def _build_full_path_from_ids(self, parent_id):
        """Строит путь ИЗ CALIAS, но навигацию ведет ПО ID (parentid)."""
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

            alias = self.id_to_calias_map.get(current_pid)
            if alias:
                path_parts.append(alias)

            parent_data = self.node_map_by_id.get(current_pid)
            if parent_data:
                current_pid = str(parent_data.get('parentid', '')).strip()
            else:
                break

        path_parts.reverse()
        return ".".join(path_parts)

    def _register_internal_widget(self, widget, ref_id, base_alias, explicit_id=None):
        """
        Централизованная регистрация внутреннего элемента.
        ВАЖНО: calias остается БАЗОВЫМ (без суффикса ID) для корректного поиска.
        """
        registry = FormObjectsRegistry()
        full_path = self._build_full_path_from_ids(ref_id)

        # Уникальное имя ТОЛЬКО для Qt (чтобы не было коллизий внутри формы)
        unique_qt_name = f"{base_alias}_{ref_id}"
        if widget.objectName() != unique_qt_name:
            widget.setObjectName(unique_qt_name)

        # Присваиваем БАЗОВЫЙ calias как бизнес-атрибут
        widget.calias = base_alias

        # ✅ РЕГИСТРАЦИЯ В ГЛОБАЛЬНОЙ КОЛЛЕКЦИИ С ЧИСТЫМ CALIAS
        registry.register_object(
            widget,
            parent_container_id=str(ref_id),
            explicit_id=explicit_id,
            full_path=f"{full_path}.{base_alias}",
            calias=base_alias
        )

        print(
            f"[LOADER_REG] Зарегистрирован внутренний элемент: {base_alias} (QtName: {unique_qt_name}) | ParentID={ref_id} | DB_ID={explicit_id}")

    def _ensure_internal_controls_exist(self, ref_id, ref_widget):
        """Создает внутренние элементы референса, если их нет в БД."""
        internal_types = [
            ('txt_of_ref', 'textbox'),
            ('btn_select_of_ref', 'button'),
            ('btn_clear_of_ref', 'button'),
            ('lbl_of_ref', 'label')
        ]

        existing_children = {
            getattr(child, 'calias', child.objectName()): child
            for child in ref_widget.findChildren(QWidget)
        }

        created_count = 0
        model = DesignerDataModel()

        for base_alias, cclass in internal_types:
            # Проверяем наличие по базовому алиасу или уникальному имени Qt
            found = False
            for child in ref_widget.findChildren(QWidget):
                c_calias = getattr(child, 'calias', None)
                c_objname = child.objectName()
                if c_calias == base_alias or c_objname.startswith(base_alias + '_'):
                    found = True
                    break

            if not found:
                if cclass == 'textbox':
                    widget = QLabel(ref_widget)
                    widget.setStyleSheet("border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px; ")
                    widget.setText("[TEXTBOX]")
                elif cclass == 'button':
                    widget = QPushButton("...", ref_widget)
                else:
                    widget = QLabel(ref_widget)
                    widget.setText(base_alias.upper())

                temp_uuid = str(uuid.uuid4())[:8]
                model.set_value(temp_uuid, "control_type", cclass)
                model.set_value(temp_uuid, "form_calias", base_alias)
                model.set_value(temp_uuid, "parent_id", ref_id)

                # ✅ РЕГИСТРИРУЕМ СРАЗУ ПРИ СОЗДАНИИ
                self._register_internal_widget(widget, ref_id, base_alias, explicit_id=temp_uuid)

                created_count += 1

        return created_count

    def _dump_registry(self):
        """Выводит полную карту реестра для отладки."""
        registry = FormObjectsRegistry()
        print("\n" + "=" * 120)
        print(f"🗺️  ПОЛНАЯ КАРТА РЕЕСТРА ({len(registry._registry)} объектов):")
        print(
            f"{'WIDGET ID (KEY)':<20} | {'CALIAS (SEARCH KEY)':<30} | {'PARENT_ID':<10} | {'DB_ID':<10} | {'FULL_PATH'}")
        print("-" * 120)
        for wid, meta in registry._registry.items():
            calias = meta.get('calias', 'N/A')
            pid = meta.get('parent_id', 'None')
            db_id = meta.get('control_id', 'N/A')
            path = meta.get('full_path', 'N/A')
            print(f"{wid:<20} | {calias:<30} | {str(pid):<10} | {str(db_id):<10} | {path}")
        print("=" * 120 + "\n")

    def load_controls(self, controls_data):
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

        for data in controls_data:
            cclass = str(data.get('cclass', 'textbox')).lower()
            cid = str(data.get('id', '')).strip()
            pid = str(data.get('parentid', '')).strip() if data.get('parentid') else "form_root"
            calias = str(data.get('calias', '')).strip()

            if cclass in ('formbackground', 'formbackgroundsignals') or cid in ('1', '840'):
                continue

            if cid:
                model.set_value(cid, "control_type", cclass)
                model.set_value(cid, "form_calias", calias)
                props = data.get('properties', {})
                for p_name, p_val in props.items():
                    model.set_value(cid, p_name, str(p_val))

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

        ordered_controls_data = [self.node_map_by_id[sid] for sid in sorted_ids if sid in self.node_map_by_id]
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

                if cclass in ('formbackground', 'formbackgroundsignals') or control_id in ('1',
                                                                                           '840') or calias == 'control_840':
                    continue

                x = int(float(props.pop('x', 50)))
                y = int(float(props.pop('y', 50)))
                width = int(float(props.pop('width', 150)))
                height = int(float(props.pop('height', 30)))

                if cclass == 'form':
                    if hasattr(self, 'background') and self.background:
                        registry.register_object(self.background, explicit_id=control_id)
                    continue

                parent_id = data.get('parentid')
                parent_item = created_items_map.get(str(parent_id)) if parent_id else None
                widget = None

                print(f"[LOADER_PROC] Обработка: ID={control_id}, Alias={calias}, Class={cclass}, Parent={parent_id}")

                # ------------------------------------------------------------------
                # А. ДЕДУПЛИКАЦИЯ И УНИКАЛИЗАЦИЯ ВНУТРЕННИХ ЭЛЕМЕНТОВ
                # ------------------------------------------------------------------
                if parent_item and hasattr(parent_item, 'widget') and parent_item.widget():
                    parent_widget = parent_item.widget()
                    for child in parent_widget.findChildren(QWidget):
                        child_calias = getattr(child, 'calias', child.objectName()).strip()

                        # ✅ ПРОВЕРЯЕМ СОВПАДЕНИЕ ПО CALIAS И РОДИТЕЛЮ
                        # Если calias совпадает, но родитель другой - это НЕ тот элемент
                        if child_calias == calias:
                            # Дополнительно проверяем, что этот ребенок действительно принадлежит этому родителю
                            if child.parent() is parent_widget:
                                widget = child

                                # Обновляем регистрацию с правильным ID и ParentID
                                self._register_internal_widget(child, parent_id, calias, explicit_id=control_id)

                                if hasattr(widget, 'properties') and isinstance(widget.properties, dict):
                                    widget.properties.update(props)

                                print(f"[LOADER_FOUND] Найден и обновлен: {calias} для Parent={parent_id}")
                                break

                # Если внутренний элемент найден и обработан — переходим к следующему
                if parent_item and widget:
                    continue

                # ------------------------------------------------------------------
                # Б. СОЗДАНИЕ НЕЗАВИСИМОГО КОНТРОЛА
                # ------------------------------------------------------------------
                if not widget:
                    if cclass in ('textbox', 'numberbox', 'datebox', 'memo', 'list'):
                        widget = QLabel(parent=None)
                        widget.setStyleSheet(
                            "border: 1px solid #b0b0b0; background-color: #ffffff; padding-left: 5px; ")
                        widget.setText(f"[{cclass.upper()}] {calias} ")
                    elif cclass == 'combobox':
                        widget = create_control(cclass, parent=None, db=self.db)
                        if widget:
                            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                    else:
                        widget = create_control(cclass, parent=None, db=self.db)

                    if not widget:
                        continue

                    widget.calias = calias
                    widget.setObjectName(calias)
                    if hasattr(widget, 'properties'):
                        widget.properties = props
                # ✅ КРИТИЧЕСКИ ВАЖНО: Регистрация ВСЕХ контролов (и корневых, и внутренних) в реестре
                # Для корневых элементов parent_container_id = None (или form_root, если нужно)
                full_path = self._build_full_path_from_ids(control_id)
                # registry.register_object(
                #     widget,
                #     parent_container_id=None,  # Корневые элементы не имеют родителя-контейнера на форме
                #     explicit_id=control_id,
                #     full_path=full_path,
                #     calias=calias
                # )



                # ------------------------------------------------------------------
                # В. МАСКИРОВАНИЕ СОСТАВНОГО РЕФЕРЕНСА
                # ------------------------------------------------------------------
                if cclass == 'reference' or hasattr(widget, 'edit_runtime'):
                    # ✅ ДО-СОЗДАНИЕ ВНУТРЕННИХ ЭЛЕМЕНТОВ ЕСЛИ ИХ НЕТ В БД
                    if hasattr(widget, 'findChildren'):
                        created = self._ensure_internal_controls_exist(control_id, widget)
                        if created > 0:
                            print(
                                f"[LOADER_CREATE] До-создано {created} внутренних элементов для референса {calias} (ID={control_id})")

                    # Переключение в режим дизайна: QLineEdit -> QLabel
                    if hasattr(widget, 'edit_runtime') and widget.edit_runtime:
                        widget.edit_runtime.setVisible(False)
                    if hasattr(widget, 'edit_design') and widget.edit_design:
                        widget.edit_design.setVisible(True)

                        # ✅ РЕГИСТРИРУЕМ ЗАГЛУШКУ TXT_OF_REF С БАЗОВЫМ ИМЕНЕМ
                        #self._register_internal_widget(
                        #     widget.edit_design,
                        #     control_id,
                        #     'txt_of_ref',
                        #     explicit_id=None  # Будет обновлено при обработке дочерней строки из БД
                        #)

                try:
                    widget.setFixedSize(width, height)
                except:
                    pass

                item = self.add_control(widget, control_id, cclass, x, y, parent_item=parent_item, calias=calias, full_path=full_path)

                if item and parent_item:
                    item.setZValue(1.0)
                    item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, True)
                    item.setFlag(item.GraphicsItemFlag.ItemIsFocusable, True)

                if item:
                    created_items_map[str(control_id)] = item
                    item.updateGeometry()

            except Exception as e:
                print(f"[SceneLoaderMixin] Ошибка каскадной загрузки контрола: {e}")
                import traceback
                traceback.print_exc()

        # ✅ ВЫВОДИМ ПОЛНУЮ КАРТУ ПОСЛЕ ЗАГРУЗКИ
        self._dump_registry()

    def delete_control(self, control_id):
        cid_str = str(control_id).strip()
        if cid_str not in self.controls:
            return

        item = self.controls[cid_str]
        if self.selected_control == item:
            self.selected_control = None
            if hasattr(self, 'control_selected'):
                self.control_selected.emit(None)

        if item and item.scene() == self:
            self.removeItem(item)

        del self.controls[cid_str]

        # ✅ Помечаем на удаление вместо немедленного стирания из всех структур
        if hasattr(self, 'deleted_control_ids'):
            self.deleted_control_ids.add(cid_str)
        else:
            # Fallback для старых версий
            for obj_ptr, meta in list(FormObjectsRegistry()._registry.items()):
                if str(meta["control_id"]).strip() == cid_str:
                    del FormObjectsRegistry()._registry[obj_ptr]

            model = DesignerDataModel()
            for key in list(model.properties_instances.keys()):
                if key == cid_str:
                    del model.properties_instances[key]

        if hasattr(self, 'control_deleted'):
            self.control_deleted.emit(cid_str)

    def clear_selection(self):
        self.clearSelection()
        self.selected_control = None
        if hasattr(self, 'control_selected'):
            self.control_selected.emit(None)