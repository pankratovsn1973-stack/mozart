

# import_tab.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,                              QLabel, QComboBox, QLineEdit, QPushButton,                              QTableWidget, QTableWidgetItem, QHeaderView,                              QMessageBox, QFileDialog, QGroupBox, QCheckBox,                              QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt
from database import DatabaseService
from crud_buttons import CrudButtons
from import_models import SourceSettings, Mapping
from import_engine import ImportEngine
from import_utils import load_source_settings
from lang.local_translator import LocalTranslator

try:
    from dbfread import DBF
    DBF_AVAILABLE = True
except ImportError:
    DBF_AVAILABLE = False


class SourceCheckDialog(QDialog):
    """Диалог для проверки источника и выбора полей для маппинга."""
    def __init__(self, parent=None, db=None, entity_id=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.entity_id = entity_id
        self.source_fields = []      # список полей из источника
        self.mappings = []            # список объектов Mapping
        self.setWindowTitle("Проверка источника и сопоставление полей")
        self.resize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Выбор файла/URL и формата
        form = QFormLayout()
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItem("Файл", 'F')
        self.source_type_combo.addItem("URL", 'U')
        self.source_type_combo.currentIndexChanged.connect(self.on_source_type_changed)
        form.addRow("Тип источника:", self.source_type_combo)

        self.source_path_edit = QLineEdit()
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self.browse_file)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.source_path_edit)
        path_layout.addWidget(self.btn_browse)
        form.addRow("Путь/URL:", path_layout)

        self.format_combo = QComboBox()
        self.format_combo.addItem("JSON", 'J')
        self.format_combo.addItem("XML", 'X')
        self.format_combo.addItem("DBF", 'D')
        form.addRow("Формат:", self.format_combo)

        self.id_field_combo = QComboBox()
        self.id_field_combo.setEnabled(False)
        form.addRow("Поле-идентификатор (sourceid):", self.id_field_combo)

        self.btn_check = QPushButton("Проверить источник")
        self.btn_check.clicked.connect(self.check_source)
        form.addRow(self.btn_check)

        layout.addLayout(form)

        # Таблица сопоставления полей
        self.mapping_table = QTableWidget(0, 4)
        self.mapping_table.setHorizontalHeaderLabels(["Поле сущности", "Поле источника", "Ссылка", "Целевая сущность"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Сопоставление полей:"))
        layout.addWidget(self.mapping_table)

        # Кнопки OK/Cancel
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def on_source_type_changed(self, index):
        is_file = self.source_type_combo.currentData() == 'F'
        self.btn_browse.setEnabled(is_file)
        if not is_file:
            self.source_path_edit.clear()

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл источника")
        if path:
            self.source_path_edit.setText(path)

    def check_source(self):
        source_type = self.source_type_combo.currentData()
        path = self.source_path_edit.text().strip()
        fmt = self.format_combo.currentData()

        if not path:
            QMessageBox.warning(self, translator.tr("error"), "Укажите путь к источнику")
            return

        try:
            if fmt == 'J':
                self.source_fields = self.read_json_structure(path)
            elif fmt == 'X':
                self.source_fields = self.read_xml_structure(path)
            elif fmt == 'D':
                self.source_fields = self.read_dbf_structure(path)
            else:
                QMessageBox.critical(self, translator.tr("error"), "Неподдерживаемый формат")
                return
        except Exception as e:
            QMessageBox.critical(self, translator.tr("error"), f"Не удалось прочитать источник: {str(e)}")
            return

        if not self.source_fields:
            QMessageBox.warning(self, translator.tr("warning"), "Не удалось получить поля источника")
            return

        # Обновляем комбобокс для идентификатора
        self.id_field_combo.clear()
        self.id_field_combo.addItem("-- не выбрано --", None)
        for f in self.source_fields:
            self.id_field_combo.addItem(f, f)
        self.id_field_combo.setEnabled(True)

        # Получаем список полей сущности (системные + из meta.fields)
        entity_fields = self.get_entity_fields()
        self.mapping_table.setRowCount(len(entity_fields))
        for row, (field_name, display_name) in enumerate(entity_fields):
            # Колонка 0: название поля сущности (только для чтения)
            self.mapping_table.setItem(row, 0, QTableWidgetItem(display_name))
            # Колонка 1: выпадающий список полей источника
            combo = QComboBox()
            combo.addItem("-- не сопоставлено --", None)
            for sf in self.source_fields:
                combo.addItem(sf, sf)
            self.mapping_table.setCellWidget(row, 1, combo)
            # Колонка 2: чекбокс "Ссылка"
            chk = QCheckBox()
            chk.stateChanged.connect(lambda state, r=row: self.on_reference_toggled(r, state))
            self.mapping_table.setCellWidget(row, 2, chk)
            # Колонка 3: выпадающий список целевых сущностей (изначально disabled)
            ref_combo = QComboBox()
            ref_combo.setEnabled(False)
            ref_combo.addItem("-- не выбрано --", None)
            entity_types = self.get_entity_types_list()
            for etid, etname in entity_types:
                ref_combo.addItem(f"{etname} ({etid})", etid)
            self.mapping_table.setCellWidget(row, 3, ref_combo)
            # Сохраняем имя поля для дальнейшего использования
            self.mapping_table.item(row, 0).setData(Qt.UserRole, field_name)

        QMessageBox.information(self, translator.tr("info"), f"Найдено {len(self.source_fields)} полей в источнике")

    def on_reference_toggled(self, row, state):
        """При включении чекбокса активируем выбор целевой сущности."""
        ref_combo = self.mapping_table.cellWidget(row, 3)
        ref_combo.setEnabled(state == Qt.Checked)

    def read_json_structure(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            return list(data[0].keys())
        elif isinstance(data, dict):
            return list(data.keys())
        else:
            return []

    def read_xml_structure(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        if len(root) > 0:
            return [child.tag for child in root[0]]
        return []

    def read_dbf_structure(self, path):
        if not DBF_AVAILABLE:
            raise ImportError("Библиотека dbfread не установлена")
        table = DBF(path, ignore_missing_memofile=True)
        return [field.name for field in table.fields]

    def get_entity_fields(self):
        """Возвращает список полей сущности в формате [(field_name, display_name), ...]."""
        fields = []
        # Системные поля
        fields.append(('cname', 'Наименование (cname)'))
        fields.append(('parentinstanceid', 'Родитель (parentinstanceid)'))
        # Поля из meta.fields
        sql = """SELECT cfieldname, calias FROM meta.fields
                 WHERE entitytypeid = %s ORDER BY isortorder"""
        rows = self.db.execute_query(sql, (self.entity_id,))
        for cfieldname, calias in rows:
            fields.append((cfieldname, f"{calias} ({cfieldname})"))
        return fields

    def get_entity_types_list(self):
        sql = "SELECT id, cname FROM meta.entitytypes ORDER BY cname"
        return self.db.execute_query(sql)

    def get_mappings(self):
        """Возвращает список объектов Mapping."""
        mappings = []
        # sourceid
        id_field = self.id_field_combo.currentData()
        if id_field:
            mappings.append(Mapping(target_field='sourceid', source_field=id_field))

        for row in range(self.mapping_table.rowCount()):
            target = self.mapping_table.item(row, 0).data(Qt.UserRole)
            combo = self.mapping_table.cellWidget(row, 1)
            source = combo.currentData()
            if source is None:
                continue
            chk = self.mapping_table.cellWidget(row, 2)
            is_ref = (chk.checkState() == Qt.Checked)
            ref_entitytype_id = None
            ref_field_name = None
            if is_ref:
                ref_combo = self.mapping_table.cellWidget(row, 3)
                ref_entitytype_id = ref_combo.currentData()
                # Генерируем имя ссылочного поля автоматически
                ref_field_name = f"ref_{source}"
            mappings.append(Mapping(
                target_field=target,
                source_field=source,
                is_reference=is_ref,
                ref_entitytype_id=ref_entitytype_id,
                ref_field_name=ref_field_name
            ))
        return mappings


class ImportTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db or DatabaseService()
        self.current_entity_id = None
        self.source_id = None   # id записи в import_sources для текущей сущности
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Группа параметров источника
        self.source_group = QGroupBox("Настройки источника")
        source_layout = QFormLayout(self.source_group)

        self.source_name_edit = QLineEdit()
        source_layout.addRow("Название источника:", self.source_name_edit)

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItem("Файл", 'F')
        self.source_type_combo.addItem("URL", 'U')
        self.source_type_combo.currentIndexChanged.connect(self.on_source_type_changed)
        source_layout.addRow("Тип:", self.source_type_combo)

        self.source_path_edit = QLineEdit()
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self.browse_file)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.source_path_edit)
        path_layout.addWidget(self.btn_browse)
        source_layout.addRow("Путь/URL:", path_layout)

        self.format_combo = QComboBox()
        self.format_combo.addItem("JSON", 'J')
        self.format_combo.addItem("XML", 'X')
        self.format_combo.addItem("DBF", 'D')
        source_layout.addRow("Формат:", self.format_combo)

        self.btn_check = QPushButton("Проверить и настроить сопоставление")
        self.btn_check.clicked.connect(self.check_source)
        source_layout.addRow(self.btn_check)

        layout.addWidget(self.source_group)

        # Кнопки сохранения и импорта
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить настройки")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_import = QPushButton("Запустить импорт")
        self.btn_import.clicked.connect(self.run_import)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Статус последнего импорта
        self.status_label = QLabel("Последний импорт: никогда")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def on_source_type_changed(self, index):
        is_file = self.source_type_combo.currentData() == 'F'
        self.btn_browse.setEnabled(is_file)
        if not is_file:
            self.source_path_edit.clear()

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл источника")
        if path:
            self.source_path_edit.setText(path)

    def set_entity_id(self, entity_id):
        self.current_entity_id = entity_id
        self.load_settings()

    def load_settings(self):
        """Загружает настройки импорта для текущей сущности."""
        if not self.current_entity_id:
            return
        sql = """SELECT id, source_name, source_type, source_path, format, id_field, last_import
                 FROM meta.import_sources WHERE entitytypeid = %s"""
        rows = self.db.execute_query(sql, (self.current_entity_id,))
        if rows:
            self.source_id = rows[0][0]
            self.source_name_edit.setText(rows[0][1] or "")
            self.source_type_combo.setCurrentIndex(self.source_type_combo.findData(rows[0][2]))
            self.source_path_edit.setText(rows[0][3])
            self.format_combo.setCurrentIndex(self.format_combo.findData(rows[0][4]))
            if rows[0][6]:
                self.status_label.setText(f"Последний импорт: {rows[0][6]}")
            else:
                self.status_label.setText("Последний импорт: никогда")
        else:
            self.source_id = None
            self.source_name_edit.clear()
            self.source_path_edit.clear()
            self.format_combo.setCurrentIndex(0)
            self.status_label.setText("Последний импорт: никогда")

    def check_source(self):
        if not self.current_entity_id:
            QMessageBox.warning(self, "Внимание", "Сначала выберите сущность")
            return
        dlg = SourceCheckDialog(self, db=self.db, entity_id=self.current_entity_id)
        # Передаём текущие параметры, если есть
        dlg.source_type_combo.setCurrentIndex(self.source_type_combo.currentIndex())
        dlg.source_path_edit.setText(self.source_path_edit.text())
        dlg.format_combo.setCurrentIndex(self.format_combo.currentIndex())
        if dlg.exec_() == QDialog.Accepted:
            self.last_mappings = dlg.get_mappings()
            QMessageBox.information(self, translator.tr("info"), "Сопоставление полей выполнено. Нажмите 'Сохранить настройки' для сохранения.")

    def save_settings(self):
        if not self.current_entity_id:
            QMessageBox.warning(self, "Внимание", "Сначала выберите сущность")
            return
        if not hasattr(self, 'last_mappings') or not self.last_mappings:
            QMessageBox.warning(self, "Внимание", "Сначала выполните проверку источника и сопоставление полей")
            return

        source_type = self.source_type_combo.currentData()
        source_path = self.source_path_edit.text().strip()
        fmt = self.format_combo.currentData()
        source_name = self.source_name_edit.text().strip()

        if not source_path:
            QMessageBox.warning(self, translator.tr("error"), "Укажите путь к источнику")
            return

        try:
            # Находим id_field (первый маппинг с target='sourceid')
            id_field = None
            for m in self.last_mappings:
                if m.target_field == 'sourceid':
                    id_field = m.source_field
                    break

            # Сохраняем или обновляем запись в import_sources
            if self.source_id:
                sql = """UPDATE meta.import_sources SET
                         source_name=%s, source_type=%s, source_path=%s, format=%s, id_field=%s, updated_at=now()
                         WHERE id=%s"""
                self.db.execute_query(sql, (source_name, source_type, source_path, fmt, id_field, self.source_id), fetch=False)
            else:
                sql = """INSERT INTO meta.import_sources
                         (entitytypeid, source_name, source_type, source_path, format, id_field)
                         VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"""
                res = self.db.execute_query(sql, (self.current_entity_id, source_name, source_type, source_path, fmt, id_field))
                if res:
                    self.source_id = res[0][0]

            # Удаляем старые маппинги
            self.db.execute_query("DELETE FROM meta.import_mappings WHERE import_source_id = %s", (self.source_id,), fetch=False)

            # Для каждого маппинга создаём или обновляем поле в meta.fields (если нужно) и вставляем запись в import_mappings
            for mapping in self.last_mappings:
                if mapping.target_field == 'sourceid':
                    # sourceid уже создаётся автоматически, просто сохраняем маппинг
                    pass
                elif mapping.is_reference:
                    # Для ссылочного поля: убеждаемся, что поле с именем ref_field_name существует и имеет тип 'R'
                    # Проверяем, есть ли уже такое поле
                    sql_check = "SELECT id FROM meta.fields WHERE entitytypeid=%s AND cfieldname=%s"
                    exists = self.db.execute_query(sql_check, (self.current_entity_id, mapping.ref_field_name))
                    if not exists:
                        # Создаём поле типа 'R'
                        sql_insert = """INSERT INTO meta.fields
                                         (entitytypeid, cfieldname, cfieldtype, calias, nlength, ndecimals, lisindexed, ref_entitytypeid, status_id)
                                         VALUES (%s, %s, 'R', %s, 0, 0, false, %s, 1) RETURNING id"""
                        target_entity_name = self.db.execute_query("SELECT cname FROM meta.entitytypes WHERE id=%s", (mapping.ref_entitytype_id,))
                        alias = f"Ссылка на {target_entity_name[0][0]}" if target_entity_name else "Ссылка"
                        self.db.execute_query(sql_insert, (self.current_entity_id, mapping.ref_field_name, alias, mapping.ref_entitytype_id), fetch=False)
                    # Сохраняем маппинг с target = ref_field_name
                    target = mapping.ref_field_name
                else:
                    target = mapping.target_field

                # Вставляем запись в import_mappings (для sourceid тоже вставляем, но is_reference=false)
                sql_ins_map = """INSERT INTO meta.import_mappings
                                 (import_source_id, target_field, source_field, is_reference, ref_entitytypeid, ref_field_name)
                                 VALUES (%s, %s, %s, %s, %s, %s)"""
                self.db.execute_query(sql_ins_map, (self.source_id, target, mapping.source_field,
                                                    mapping.is_reference, mapping.ref_entitytype_id, mapping.ref_field_name), fetch=False)

            QMessageBox.information(self, translator.tr("info"), "Настройки импорта сохранены")
            self.load_settings()  # обновим статус
        except Exception as e:
            QMessageBox.critical(self, translator.tr("error"), f"Не удалось сохранить настройки: {str(e)}")

    def run_import(self):
        if not self.current_entity_id or not self.source_id:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните настройки импорта")
            return

        # Загружаем настройки из БД
        settings = load_source_settings(self.db, self.source_id)
        if not settings:
            QMessageBox.critical(self, translator.tr("error"), "Не удалось загрузить настройки импорта")
            return

        # Добавляем id в settings для использования в engine (для обновления last_import)
        settings.id = self.source_id

        engine = ImportEngine(self.db, settings, self.current_entity_id)
        try:
            # В будущем можно добавить прогресс-бар и выполнение в отдельном потоке
            engine.run()
            QMessageBox.information(self, translator.tr("info"), "Импорт успешно завершён")
            self.load_settings()  # обновим статус
        except Exception as e:
            QMessageBox.critical(self, translator.tr("error"), f"Импорт не удался: {str(e)}")