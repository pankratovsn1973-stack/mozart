# Полный путь: tabs/entity_classes_tab.py
"""
Вкладка управления классами ERP в конфигураторе.
Отображает иерархический классификатор на основе категорий из базы данных.
Фильтрует подобъекты (is_class = true). Выводит интерактивное описание.
"""
from ide_core import goProject  # Подключаем наш единственный глобальный синглтон
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QHeaderView, QSplitter, QTextEdit, QLabel, QWidget,
    QPushButton, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from tabs.base_tab import BaseTab
from services.class_data_service import ClassDataService
from dialogs.base_class_selector import BaseClassSelectorDialog
from dialogs.class_edit_dialog import ClassEditDialog
from crud_buttons import CrudButtons

from typing import Optional

class EntityClassesTab(BaseTab):
    """
    Главная вкладка иерархического классификатора low-code классов Mozart ERP.
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self.class_service = ClassDataService(db) if db else None
        self.current_version_id = None
        self.current_selected_type = None  # 'category' или 'class'
        self.current_selected_db_id = None  # Физический ID из БД
        self.category_comments = {}
        self.setup_ui()
        self.load_classes()

    def setup_ui(self):
        """Настройка интерфейса вкладки и якорение элементов."""
        self.clear_layout()

        # Вертикальный сплиттер разделяет дерево и подложку документации
        v_splitter = QSplitter(Qt.Vertical)
        self.layout.addWidget(v_splitter)

        # --- Верхний контейнер: Инструменты CRUD + Дерево ---
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Горизонтальная панель инструментов
        hbox_crud = QHBoxLayout()
        self.crud = CrudButtons(self)
        self.crud.add_clicked.connect(self.add_class)
        self.crud.edit_clicked.connect(self.edit_class)
        self.crud.delete_clicked.connect(self.delete_class)
        hbox_crud.addWidget(self.crud)

        # Жестко якорим кнопку структуры групп у правого края панели
        hbox_crud.addStretch()
        self.btn_edit_group_class = QPushButton()
        self.btn_edit_group_class.clicked.connect(self.open_group_manager_dialog)
        hbox_crud.addWidget(self.btn_edit_group_class)
        top_layout.addLayout(hbox_crud)

        # Иерархическое дерево классов
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setColumnWidth(0, 80)  # ID версии
        self.tree.setColumnWidth(1, 320)  # Категория / Класс
        self.tree.setColumnWidth(2, 150)  # Базовый класс Qt
        self.tree.setColumnWidth(3, 90)  # Источник (PYTHON/ERP)
        self.tree.setColumnWidth(4, 80)  # Визуальный (Да/Нет)
        self.tree.header().setStretchLastSection(True)
        self.tree.itemDoubleClicked.connect(self.edit_class)
        self.tree.itemSelectionChanged.connect(self.on_item_selected)
        top_layout.addWidget(self.tree)

        v_splitter.addWidget(top_container)

        # --- Нижний контейнер: Документация ---
        doc_container = QWidget()
        doc_layout = QVBoxLayout(doc_container)
        doc_layout.setContentsMargins(0, 5, 0, 0)

        doc_header_layout = QHBoxLayout()
        self.lbl_doc_title = QLabel()
        doc_header_layout.addWidget(self.lbl_doc_title)
        doc_header_layout.addStretch()
        self.btn_edit_doc = QPushButton()
        self.btn_edit_doc.setEnabled(False)
        self.btn_edit_doc.clicked.connect(self.quick_edit_description)
        doc_header_layout.addWidget(self.btn_edit_doc)
        doc_layout.addLayout(doc_header_layout)

        self.doc_viewer = QTextEdit()
        self.doc_viewer.setReadOnly(True)
        self.doc_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                color: #222222;
                font-family: 'Segoe UI', 'Arial';
                font-size: 11pt;
            }
        """)
        doc_layout.addWidget(self.doc_viewer)
        v_splitter.addWidget(doc_container)
        v_splitter.setSizes([500, 200])

        self.retranslate_ui()

    def clear_layout(self):
        """Очистка layout при перестроении UI."""
        if self.layout:
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def load_classes(self):
        """Загрузка дерева классов на основе скомпилированной функции Постгреса и ClassRegistry."""
        self.tree.clear()
        if not self.db:
            return

        # 🚀 ФИКС: Передаем дату сессии в хранимую функцию для поддержки "Машины времени"
        session_date = goProject.system_date.toString("yyyy-MM-dd HH:mm:ss")
        sql = "SELECT * FROM class_erp.f_get_active_classes_tree(%s);"

        try:
            rows = self.db.execute_query(sql, (session_date,)) or []
        except Exception as e:
            print(f"[ERROR] Ошибка вызова хранимой функции дерева классов: {e}")
            rows = []

        category_items = {}  # Кэш папок {category_id: QTreeWidgetItem}

        # 1. Первым проходом создаем узлы папок-категорий
        # Новая сигнатура f_get_active_classes_tree возвращает 18 полей:
        # version_id, class_id, c_name, i_load_order, is_visible, c_base_class, c_base_source,
        # i_parent_id, level, root_class_id, category_id, category_name, category_alias,
        # category_parent_id, category_comment, class_comment, c_execution_env, is_preload
        for row in rows:
            (v_id, c_id, c_name, _load_order, is_vis, b_class, b_source,
             _pid, _level, _root, cat_id, cat_name, cat_alias, cat_pid,
             cat_comment, cls_comment, _exec_env, _preload) = row

            dict_cat_id = cat_id if cat_id is not None else 0
            if dict_cat_id not in category_items:
                folder = QTreeWidgetItem()
                folder.setText(1, f"📁 {cat_name}")

                # Стилизация папки
                font = folder.font(1)
                font.setBold(True)
                folder.setFont(1, font)
                if cat_alias and "system" in cat_alias:
                    folder.setForeground(1, QBrush(QColor(0, 102, 204)))
                else:
                    folder.setForeground(1, QBrush(QColor(0, 150, 50)))

                # Подшиваем метаданные папки
                folder.setData(0, Qt.UserRole, -1)  # Маркер папки
                folder.setData(0, Qt.UserRole + 1, dict_cat_id)
                folder.setData(0, Qt.UserRole + 2, cat_comment or "Описание категории отсутствует.")
                category_items[dict_cat_id] = folder

        # 2. Связываем папки между собой (поддерживаем вложенные подкатегории групп)
        for row in rows:
            (_, _, _, _, _, _, _, _, _, _, cat_id, _, _, cat_pid, _, _, _, _) = row

            dict_cat_id = cat_id if cat_id is not None else 0
            folder = category_items.get(dict_cat_id)

            if folder and folder.parent() is None and self.tree.indexOfTopLevelItem(folder) == -1:
                if cat_pid and cat_pid in category_items:
                    category_items[cat_pid].addChild(folder)
                else:
                    self.tree.addTopLevelItem(folder)

        # 3. Наполнение папок конечными low-code классами
        self._fill_classes_into_main_tree(rows, category_items)

    def _fill_classes_into_main_tree(self, rows: list, category_items: dict):
        """Раскладывает low-code классы по папкам, считывая топологию запуска из ОЗУ Машины классов."""
        for row in rows:
            # 🎯 ФИКС: Полная распаковка всех 18 полей новой функции
            (v_id, c_id, c_name, _load_order, is_vis, b_class, b_source,
             _pid, _level, _root, cat_id, _, _, _, _, cls_comment, exec_env, preload) = row

            dict_cat_id = cat_id if cat_id is not None else 0
            parent_folder = category_items.get(dict_cat_id)
            if not parent_folder:
                continue

            item = QTreeWidgetItem(parent_folder)
            item.setText(0, str(v_id))

            # Читаем теги среды выполнения и предзагрузки из реестра классов
            class_node = goProject.class_registry.get_class_version(v_id)
            env_tag = f" [{class_node.c_execution_env}]" if class_node else ""
            preload_tag = " ⚡" if (class_node and class_node.is_preload) else ""

            item.setText(1, f"{c_name}{env_tag}{preload_tag}")
            item.setText(2, b_class or '---')
            item.setText(3, b_source or 'ERP')
            item.setText(4, self.translator.tr('yes') if is_vis else self.translator.tr('no'))

            item.setData(0, Qt.UserRole, v_id)
            item.setData(0, Qt.UserRole + 1, c_id)
            item.setData(0, Qt.UserRole + 2, cls_comment or "Описание класса отсутствует.")

            if not is_vis:
                item.setForeground(1, QBrush(QColor(120, 120, 120)))
                font_child = item.font(1)
                font_child.setItalic(True)
                item.setFont(1, font_child)

        self.tree.expandAll()

    def retranslate_ui(self):
        """Смена языковой локализации элементов интерфейса на лету."""
        self.tree.setHeaderLabels([
            self.translator.tr('field_id'),
            self.translator.tr('field_class_name'),
            self.translator.tr('field_base_class'),
            self.translator.tr('field_type'),
            self.translator.tr('field_visible')
        ])
        if hasattr(self, 'crud') and self.crud:
            self.crud.retranslate_ui()
        if hasattr(self, 'btn_edit_group_class') and self.btn_edit_group_class:
            self.btn_edit_group_class.setText(self.translator.tr('btn_edit_group_class'))
        if hasattr(self, 'lbl_doc_title') and self.lbl_doc_title:
            self.lbl_doc_title.setText(f"<b>ℹ️ {self.translator.tr('label_interactive_doc')}:</b>")
        if hasattr(self, 'btn_edit_doc') and self.btn_edit_doc:
            translated_btn = self.translator.tr('btn_edit')
            translated_desc = self.translator.tr('field_description').lower()
            self.btn_edit_doc.setText(f"✏️ {translated_btn} {translated_desc}")

    def on_item_selected(self):
        """Контроль выбора элементов и рендеринг локализованных карточек документации."""
        current = self.tree.currentItem()
        if current:
            v_id = current.data(0, Qt.UserRole)
            db_id = current.data(0, Qt.UserRole + 1)
            description = current.data(0, Qt.UserRole + 2)

            self.current_selected_db_id = db_id
            self.btn_edit_doc.setEnabled(True)

            if v_id == -1 or v_id is None:
                self.current_version_id = None
                self.current_selected_type = 'category'
                self.crud.btn_edit.setEnabled(False)
                self.crud.btn_del.setEnabled(False)
                label_cat = "Category:" if self.translator.current_language == 'en' else "Категория:"
                self.doc_viewer.setHtml(f"<b>{label_cat}</b><br/><p style='color:#0055aa;'>{description}</p>")
            else:
                self.current_version_id = v_id
                self.current_selected_type = 'class'
                self.crud.btn_edit.setEnabled(True)
                self.crud.btn_del.setEnabled(True)

                c_name = current.text(1)
                b_class = current.text(2)
                b_source = current.text(3)

                label_class = "Class:" if self.translator.current_language == 'en' else "Класс:"
                label_sub = (f"Base Qt Component: {b_class} | Source: {b_source}"
                             if self.translator.current_language == 'en'
                             else f"Базовый компонент Qt: {b_class} | Источник: {b_source}")

                html_card = f"""
                    <b style='font-size:12pt; color:#111;'>{label_class} {c_name}</b><br/>
                    <small style='color:gray;'>{label_sub}</small>
                    <hr style='border:0; border-top:1px solid #ccc;'/>
                    <p style='line-height:140%;'>{description}</p>
                """
                self.doc_viewer.setHtml(html_card)
        else:
            self.current_version_id = None
            self.current_selected_type = None
            self.current_selected_db_id = None
            self.crud.btn_edit.setEnabled(False)
            self.crud.btn_del.setEnabled(False)
            self.btn_edit_doc.setEnabled(False)
            self.doc_viewer.clear()

    def quick_edit_description(self):
        """Вызывает компактное модальное окно быстрого редактирования описания в СУБД."""
        if not self.current_selected_type or self.current_selected_db_id is None:
            return
        current_item = self.tree.currentItem()
        if not current_item:
            return

        old_description = current_item.data(0, Qt.UserRole + 2)
        if "отсутствует" in old_description:
            old_description = ""

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit: {current_item.text(1).strip()}")
        dlg.resize(500, 250)
        dlg_layout = QVBoxLayout(dlg)
        edit_area = QTextEdit()
        edit_area.setPlainText(old_description)
        dlg_layout.addWidget(edit_area)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        dlg_layout.addWidget(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            new_description = edit_area.toPlainText().strip()
            try:
                if self.current_selected_type == 'category':
                    sql = "UPDATE class_erp.class_category SET mcomment = %s WHERE id = %s"
                else:
                    sql = "UPDATE class_erp.mozartclasses SET mcomment = %s WHERE id = %s"
                self.db.execute_query(sql, (new_description, self.current_selected_db_id), fetch=False)
                self.load_classes()
                self.on_item_selected()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def open_group_manager_dialog(self):
        """Вызов модального окна конфигуратора групп."""
        from dialogs.class_group_manager_dialog import ClassGroupManagerDialog
        dlg = ClassGroupManagerDialog(self, db=self.db)
        dlg.exec_()
        self.load_classes()

    def add_class(self):
        """Добавление нового класса: выбор базового → имя → физическое создание root → edit."""
        from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

        # 1. Выбор базового класса
        selector = BaseClassSelectorDialog(self, db=self.db)
        if selector.exec_() != BaseClassSelectorDialog.Accepted:
            return
        base_version_id = selector.get_selected_version_id()
        if not base_version_id or base_version_id <= 0:
            QMessageBox.warning(self, "Ошибка", "Базовый класс не выбран")
            return

        # 2. Данные базового класса
        if not self.class_service:
            QMessageBox.warning(self, "Ошибка", "ClassDataService не инициализирован")
            return
        base_data = self.class_service.get_class_version(base_version_id)
        if not base_data:
            QMessageBox.warning(self, "Ошибка", f"Базовый класс {base_version_id} не найден")
            return
        base_version = base_data.get('version', {})
        base_name = base_version.get('c_name', 'Class')
        base_c_base_class = base_version.get('c_base_class', 'QWidget')
        base_c_base_source = base_version.get('c_base_source', 'QT')
        base_c_base_library = base_version.get('c_base_library', 'PySide6.QtWidgets')

        # 3. Предложить имя (с проверкой на дубли)
        suggested_name = f"New_{base_name}"
        final_name = self._get_unique_class_name(suggested_name)
        if final_name is None:
            return  # пользователь отменил

        # 4. Физически создать root в БД
        try:
            new_version_id = self._create_new_class_root(
                class_name=final_name,
                base_version_id=base_version_id,
                c_base_class=base_c_base_class,
                c_base_source=base_c_base_source,
                c_base_library=base_c_base_library,
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать класс: {e}")
            return
        if not new_version_id:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать класс (нет id)")
            return

        # 5. Открыть ClassEditDialog в режиме edit с реальным version_id
        editor = ClassEditDialog(self, db=self.db, version_id=new_version_id, mode='edit')
        editor.exec_()
        self.load_classes()

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def _get_unique_class_name(self, suggested: str) -> Optional[str]:
        """
        Показывает QInputDialog с предложенным именем.
        Если имя занято — предлагает добавить _1, _2, ...
        Возвращает финальное имя или None (отмена).
        """
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        candidate = suggested
        # Проверяем на дубли и подбираем свободное имя
        suffix = 1
        while self._class_name_exists(candidate):
            candidate = f"{suggested}_{suffix}"
            suffix += 1

        name, ok = QInputDialog.getText(
            self,
            "Новый класс",
            "Имя нового класса:",
            QLineEdit.EchoMode.Normal,
            candidate,
        )
        if not ok:
            return None
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым")
            return None
        # Проверка на дубли введённого имени
        if self._class_name_exists(name):
            QMessageBox.warning(self, "Ошибка", f"Имя «{name}» уже занято. Выберите другое.")
            return None
        return name

    def _class_name_exists(self, class_name: str) -> bool:
        """Проверяет, есть ли уже класс с таким c_name в mozartclasses (dt_end IS NULL)."""
        if not self.db:
            return False
        try:
            res = self.db.execute_query(
                "SELECT 1 FROM class_erp.mozartclasses "
                "WHERE c_name = %s AND dt_end IS NULL LIMIT 1",
                (class_name,)
            )
            return bool(res)
        except Exception as e:
            print(f"[EntityClassesTab] Ошибка проверки имени: {e}")
            return False

    def _create_new_class_root(self, class_name: str, base_version_id: int,
                               c_base_class: str, c_base_source: str,
                               c_base_library: str) -> Optional[int]:
        """
        Физически создаёт root нового класса в БД:
          - INSERT mozartclasses → id_mozart_class
          - INSERT class_version (root) → id_class_version
        Возвращает id_class_version или None.
        """
        if not self.db:
            return None
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                # 1. mozartclasses
                cur.execute(
                    """INSERT INTO class_erp.mozartclasses
                       (c_name, mcomment, is_class, owner_class_id, dt_start, dt_end)
                       VALUES (%s, NULL, TRUE, NULL, now(), NULL) RETURNING id;""",
                    (class_name,)
                )
                id_mozart_class = cur.fetchone()[0]

                # 2. class_version (root)
                cur.execute(
                    """INSERT INTO class_erp.class_version
                       (id_mozart_class, is_visible, c_base_class, c_base_source,
                        i_base_class, i_parent_id, txt_properties, dt_start, dt_end,
                        c_execution_env, is_preload, status_id, donor_object_id,
                        first_ancestor_class_id, c_base_library, i_load_order)
                       VALUES (%s, TRUE, %s, %s, %s, NULL, '{}', now(), NULL,
                               'HYBRID', TRUE, 1, NULL, NULL, %s, 100) RETURNING id;""",
                    (id_mozart_class, c_base_class, c_base_source,
                     base_version_id, c_base_library)
                )
                id_class_version = cur.fetchone()[0]
                conn.commit()
                return id_class_version
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise

    def edit_class(self):
        """Редактирование выбранной версии класса."""
        if self.current_version_id is None or self.current_version_id <= 0:
            return
        editor = ClassEditDialog(self, db=self.db, version_id=self.current_version_id, mode='edit')
        if editor.exec_() == ClassEditDialog.Accepted:
            self.load_classes()

    def delete_class(self):
        """Удаление выбранной версии класса."""
        if self.current_version_id is None or self.current_version_id <= 0:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('warning_select_class'))
            return
        if QMessageBox.question(self, self.translator.tr('confirm_delete'), self.translator.tr('confirm_delete_class'),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self.class_service:
                self.class_service.soft_delete_class_version(self.current_version_id)
                self.load_classes()
                self.current_version_id = None

    def refresh(self):
        """Обновление данных."""
        self.load_classes()