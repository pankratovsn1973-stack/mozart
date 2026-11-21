# dialogs/methods_dialog.py
# -*- coding: utf-8 -*-
"""
Диалог управления методами класса (модальный).
Работает напрямую с CollectionManager._elements[element_id]['method_collection'].

Правки под change_log:
  - add_method создаёт MethodItem через col.add_new(...) — ID берётся из
    CollectionManager.next_negative_id(), пишется change_log(method_add);
  - on_lang_changed вызывает col.set_lang(...) — пишется change_log(method_lang);
  - delete_method вызывает col.remove(...) — пишется change_log(method_delete);
  - никаких прямых m.i_lang = ... / m.is_deleted = ... в диалоге.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTextEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QSplitter, QMessageBox, QGroupBox, QFormLayout, QDateTimeEdit,
    QWidget, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from database import DatabaseService
from lang.local_translator import LocalTranslator
from dialogs.collection_manager import CollectionManager
from core.method_item import MethodItem


class MethodsDialog(QDialog):
    """
    Диалог управления методами класса (модальный).
    Работает напрямую с CollectionManager._elements[element_id]['method_collection'].
    """

    def __init__(self, parent=None, db: DatabaseService = None,
                 version_id: int = -1, element_id: int = -1,
                 class_name: str = "", collection: CollectionManager = None):
        super().__init__(parent)
        self.setModal(True)
        self.db = db
        self.translator = LocalTranslator()
        self.version_id = version_id
        self.element_id = element_id
        self.class_name = class_name
        self.collection = collection
        self.current_element_id = None
        self.current_method_name = None

        self.setWindowTitle(f"{self.translator.tr('title_methods')}: {class_name}")
        self.resize(950, 680)
        self.setup_ui()
        self.load_object_tree()

    # =====================================================================
    # UI
    # =====================================================================
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # ─── Верхняя панель: дата актуализации ───
        top = QHBoxLayout()
        top.addWidget(QLabel(self.translator.tr('label_actual_date')))
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateTimeChanged.connect(self.on_date_changed)
        top.addWidget(self.date_edit)
        top.addStretch()
        layout.addLayout(top)

        # ─── Сплиттер: дерево объектов | методы ───
        splitter = QSplitter(Qt.Horizontal)

        # ЛЕВАЯ ПАНЕЛЬ: дерево объектов
        left = QGroupBox(self.translator.tr('group_class_objects'))
        left_layout = QVBoxLayout(left)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self.translator.tr('field_alias'),
            self.translator.tr('field_class')
        ])
        self.tree.setColumnWidth(0, 200)
        self.tree.itemClicked.connect(self.on_object_selected)
        left_layout.addWidget(self.tree)
        splitter.addWidget(left)

        # ПРАВАЯ ПАНЕЛЬ: методы
        right = QGroupBox(self.translator.tr('group_methods'))
        right_layout = QVBoxLayout(right)
        form = QFormLayout()

        self.method_combo = QComboBox()
        self.method_combo.currentIndexChanged.connect(self.on_method_selected)
        form.addRow(self.translator.tr('label_method'), self.method_combo)

        # i_lang (1-GSQL, 2-Python-сервер, 3-Python-клиент)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem(self.translator.tr('lang_gsql'), 1)
        self.lang_combo.addItem(self.translator.tr('lang_python_server'), 2)
        self.lang_combo.addItem(self.translator.tr('lang_python_client'), 3)
        self.lang_combo.setCurrentIndex(2)  # по умолчанию 3
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        form.addRow(self.translator.tr('label_lang_env'), self.lang_combo)

        right_layout.addLayout(form)

        # Время версии
        self.version_label = QLabel(self.translator.tr('label_version_dash'))
        self.version_label.setStyleSheet("color: gray; font-style: italic;")
        right_layout.addWidget(self.version_label)

        # Редактор кода
        right_layout.addWidget(QLabel(self.translator.tr('label_method_code')))
        self.code_edit = QTextEdit()
        self.code_edit.setFont(self._get_mono_font())
        right_layout.addWidget(self.code_edit)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(self.translator.tr('btn_add_method'))
        self.btn_add.clicked.connect(self.add_method)
        self.btn_delete = QPushButton(self.translator.tr('btn_delete_method'))
        self.btn_delete.clicked.connect(self.delete_method)
        self.btn_save = QPushButton(self.translator.tr('btn_save_code'))
        self.btn_save.clicked.connect(self.save_method)
        self.btn_close = QPushButton(self.translator.tr('btn_close'))
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_close)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right)
        splitter.setSizes([300, 650])
        layout.addWidget(splitter)

    def _get_mono_font(self):
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.Monospace)
        return font

    # =====================================================================
    # Дерево объектов
    # =====================================================================
    def load_object_tree(self):
        self.tree.clear()
        if not self.collection:
            return

        root_item = QTreeWidgetItem()
        root_item.setText(0, self.class_name or f"{self.translator.tr('label_class')} {self.version_id}")
        root_item.setText(1, self.translator.tr('class_type_root'))
        root_item.setData(0, Qt.UserRole, self.version_id)
        root_item.setData(0, Qt.UserRole + 1, "class")
        self.tree.addTopLevelItem(root_item)

        items = {self.version_id: root_item}
        for eid, elem in self.collection._elements.items():
            if eid == self.version_id:
                continue
            parent_id = elem.get('parent_id')
            alias = elem.get('calias', f"obj_{eid}")
            cclass = elem.get('cclass', '?')

            item = QTreeWidgetItem()
            item.setText(0, alias)
            item.setText(1, cclass)
            item.setData(0, Qt.UserRole, eid)
            item.setData(0, Qt.UserRole + 1, "object")

            if parent_id and parent_id in items:
                items[parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            items[eid] = item

        self.tree.expandAll()
        self.tree.setCurrentItem(root_item)
        self.on_object_selected(root_item, 0)

    # =====================================================================
    # Выбор объекта
    # =====================================================================
    def on_object_selected(self, item: QTreeWidgetItem, column: int):
        self.current_element_id = item.data(0, Qt.UserRole)
        self.load_methods_combo()

    def on_date_changed(self, _dt):
        self.load_methods_combo()

    # =====================================================================
    # Комбо методов
    # =====================================================================
    def load_methods_combo(self):
        self.method_combo.blockSignals(True)
        self.method_combo.clear()

        if not self.collection or not self.current_element_id:
            self.method_combo.blockSignals(False)
            return

        col = self.collection.get_method_collection(self.current_element_id)
        if col is None:
            self.method_combo.blockSignals(False)
            return

        for m in col.all_ordered():
            if m.order == 1:
                prefix = "🔹"
            else:
                prefix = f"⬆️ [hop {m.order}]"
            self.method_combo.addItem(f"{prefix} {m.c_name}", m.c_name)

        self.method_combo.blockSignals(False)

        if self.method_combo.count() > 0:
            self.method_combo.blockSignals(True)
            self.method_combo.setCurrentIndex(0)
            self.on_method_selected(0)
            self.method_combo.blockSignals(False)
        else:
            self.code_edit.clear()
            self.version_label.setText(self.translator.tr('label_version_dash'))

    # =====================================================================
    # Выбор метода
    # =====================================================================
    def on_method_selected(self, index: int):
        if index < 0:
            return

        c_name = self.method_combo.itemData(index)
        if not c_name:
            return

        is_programmatic = self.method_combo.signalsBlocked()
        self.current_method_name = c_name

        col = self.collection.get_method_collection(self.current_element_id)
        if col is None:
            return

        m = col.get(c_name)
        if m is None:
            return

        # Если унаследованный — вопрос «переопределить?» (только при ручном выборе)
        if m.order > 1 and not is_programmatic:
            reply = QMessageBox.question(
                self, self.translator.tr('title_inherited_method'),
                self.translator.tr('msg_override_method').format(c_name, m.order),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            # Создаём новый собственный MethodItem (order=1) через col.add_new —
            # он сам присвоит отрицательный ID и запишет change_log(method_add)
            new_m = col.add_new(MethodItem(
                id=-1, c_name=c_name, owner_class_id=m.owner_class_id,
                i_lang=m.i_lang, order=1
            ))
            if new_m is None:
                return
            self.current_method_name = c_name
            m = new_m

        # Синхронизация ID перед загрузкой кода
        if m.id <= 0:
            session_date = self.date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            sql_find = """
                SELECT mcr.id_method 
                FROM class_erp.method_class_relation mcr
                JOIN class_erp.method m ON mcr.id_method = m.id
                WHERE mcr.id_class_version = %s 
                  AND m.c_name = %s 
                  AND mcr.dt_end IS NULL
                  AND m.dt_end IS NULL
                  AND %s::timestamp BETWEEN 
                      COALESCE(mcr.dt_start, '-infinity'::timestamp) 
                      AND COALESCE(mcr.dt_end, 'infinity'::timestamp)
                LIMIT 1;
            """
            res = self.db.execute_query(sql_find, (self.current_element_id, m.c_name, session_date))
            if res:
                m.id = res[0][0]
                print(f"[UI] Найден реальный ID для {m.c_name}: {m.id}")
            else:
                print(f"[UI] Реальный ID для {m.c_name} не найден на дату {session_date}")

        # Обновляем UI языка
        idx = self.lang_combo.findData(m.i_lang)
        if idx >= 0:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(idx)
            self.lang_combo.blockSignals(False)

        self.load_method_code(m.id)

    def load_method_code(self, method_id: int):
        if not method_id or method_id <= 0:
            self.code_edit.clear()
            self.version_label.setText(self.translator.tr('label_version_dash'))
            return

        sql = """
            SELECT mv.txt_method, mv.dt_start, mv.dt_end
            FROM class_erp.method_version mv
            WHERE mv.id_method = %s AND mv.dt_end IS NULL
            ORDER BY mv.dt_start DESC LIMIT 1
        """
        try:
            rows = self.db.execute_query(sql, (method_id,)) or []
        except Exception:
            rows = []

        if rows:
            txt, dt_start, dt_end = rows[0]
            self.code_edit.setPlainText(str(txt or ""))
            s = dt_start.strftime("%Y-%m-%d %H:%M") if dt_start else "—"
            e = dt_end.strftime("%Y-%m-%d %H:%M") if dt_end else self.translator.tr('version_active')
            self.version_label.setText(f"{self.translator.tr('label_version')} {s} → {e}")
        else:
            self.code_edit.clear()
            self.version_label.setText(self.translator.tr('label_version_new'))

    # =====================================================================
    # i_lang — через col.set_lang, чтобы записался change_log(method_lang)
    # =====================================================================
    def on_lang_changed(self, _index):
        if not self.current_method_name or not self.current_element_id:
            return
        col = self.collection.get_method_collection(self.current_element_id)
        if col is None:
            return
        new_lang = self.lang_combo.currentData()
        col.set_lang(self.current_method_name, new_lang)

    # =====================================================================
    # Добавление / удаление
    # =====================================================================
    def add_method(self):
        name, ok = QInputDialog.getText(
            self, self.translator.tr('title_new_method'),
            self.translator.tr('msg_enter_method_name')
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        col = self.collection.get_method_collection(self.current_element_id)
        if col is None:
            return
        if name in col:
            QMessageBox.warning(
                self, self.translator.tr('warning'),
                self.translator.tr('msg_method_exists').format(name)
            )
            return
        new_m = col.add_new(MethodItem(
            id=-1, c_name=name, owner_class_id=self.current_element_id,
            i_lang=3, order=1
        ))
        if new_m is None:
            return
        self.load_methods_combo()

    def delete_method(self):
        if not self.current_method_name or not self.current_element_id:
            return
        reply = QMessageBox.question(
            self, self.translator.tr('title_delete_method'),
            self.translator.tr('msg_delete_method').format(self.current_method_name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        col = self.collection.get_method_collection(self.current_element_id)
        if col is not None:
            col.remove(self.current_method_name)
        self.load_methods_combo()

    # =====================================================================
    # Сохранение кода
    # =====================================================================
    def save_method(self):
        if not self.current_method_name or not self.current_element_id:
            return

        col = self.collection.get_method_collection(self.current_element_id)
        if col is None:
            return

        m = col.get(self.current_method_name)
        if m is None:
            return

        code = self.code_edit.toPlainText()
        if not code.strip():
            QMessageBox.warning(
                self, self.translator.tr('warning'),
                self.translator.tr('msg_empty_code')
            )
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.translator.tr('title_save_method'))
        msg_box.setText(self.translator.tr('msg_save_method_version'))
        msg_box.setInformativeText(self.translator.tr('msg_save_method_info'))

        btn_new = msg_box.addButton(self.translator.tr('btn_new_version'), QMessageBox.AcceptRole)
        btn_update = msg_box.addButton(self.translator.tr('btn_update_current'), QMessageBox.ActionRole)
        btn_cancel = msg_box.addButton(self.translator.tr('btn_cancel'), QMessageBox.RejectRole)
        msg_box.setDefaultButton(btn_new)
        msg_box.exec_()

        clicked = msg_box.clickedButton()
        if clicked == btn_cancel:
            return

        force_new = (clicked == btn_new)
        session_date = self.date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        try:
            real_method_id = m.id

            if real_method_id <= 0:
                sql_find_rel = """
                    SELECT mcr.id_method 
                    FROM class_erp.method_class_relation mcr
                    JOIN class_erp.method m ON mcr.id_method = m.id
                    WHERE mcr.id_class_version = %s 
                      AND m.c_name = %s 
                      AND mcr.dt_end IS NULL
                      AND m.dt_end IS NULL
                      AND %s::timestamp BETWEEN 
                          COALESCE(mcr.dt_start, '-infinity'::timestamp) 
                          AND COALESCE(mcr.dt_end, 'infinity'::timestamp)
                    LIMIT 1;
                """
                res_rel = self.db.execute_query(
                    sql_find_rel,
                    (self.current_element_id, m.c_name, session_date)
                )

                if res_rel:
                    real_method_id = res_rel[0][0]
                    print(
                        f"[SAVE] Найдена активная связь для метода {m.c_name} "
                        f"и элемента {self.current_element_id}, ID={real_method_id}"
                    )
                    m.id = real_method_id
                else:
                    sql_ins_method = """
                        INSERT INTO class_erp.method (c_name, owner_class_id, dt_start, dt_end)
                        VALUES (%s, %s, NOW(), NULL) RETURNING id;
                    """
                    res_ins = self.db.execute_query(
                        sql_ins_method,
                        (m.c_name, self.current_element_id)
                    )
                    if not res_ins:
                        raise Exception("Не удалось создать запись метода")
                    real_method_id = res_ins[0][0]
                    m.id = real_method_id

                    self.db.execute_query(
                        "INSERT INTO class_erp.method_class_relation "
                        "(id_method, id_class_version, dt_start, dt_end) "
                        "VALUES (%s, %s, NOW(), NULL);",
                        (real_method_id, self.current_element_id), fetch=False
                    )
                    print(
                        f"[SAVE] Создан новый метод {m.c_name} и связь "
                        f"для элемента {self.current_element_id}, ID={real_method_id}"
                    )

            if force_new and m.dt_start:
                self.db.execute_query(
                    "UPDATE class_erp.method_version SET dt_end = NOW() "
                    "WHERE id_method = %s AND dt_end IS NULL;",
                    (real_method_id,), fetch=False
                )

            self.db.execute_query(
                "INSERT INTO class_erp.method_version "
                "(id_method, txt_method, i_lang, dt_start, dt_end) "
                "VALUES (%s, %s, %s, NOW(), NULL);",
                (real_method_id, code, m.i_lang), fetch=False
            )

            check_rel = """
                SELECT 1 FROM class_erp.method_class_relation 
                WHERE id_method = %s AND id_class_version = %s AND dt_end IS NULL
            """
            has_rel = self.db.execute_query(
                check_rel, (real_method_id, self.current_element_id)
            )

            if not has_rel:
                self.db.execute_query(
                    "INSERT INTO class_erp.method_class_relation "
                    "(id_method, id_class_version, dt_start, dt_end) "
                    "VALUES (%s, %s, NOW(), NULL);",
                    (real_method_id, self.current_element_id), fetch=False
                )
                print(f"[SAVE] Создана связь method_class_relation "
                      f"для метода {real_method_id}")
            else:
                print(f"[SAVE] Связь method_class_relation уже существует, пропуск")

            m.is_new = False
            m.is_changed = False
            m.dt_start = QDateTime.currentDateTime()

            QMessageBox.information(
                self, self.translator.tr('info'),
                self.translator.tr('msg_method_saved')
            )
            self.load_method_code(real_method_id)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, self.translator.tr('error'),
                f"{self.translator.tr('err_save_method')}: {e}"
            )