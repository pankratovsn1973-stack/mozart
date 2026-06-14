# mozart_import/wizards/wizard_pages.py (полностью, с новым MappingPage и предпросмотром)
from PySide6.QtWidgets import (QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,                              QLineEdit, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,                              QHeaderView, QProgressBar, QMessageBox, QGroupBox, QTextEdit,                              QCheckBox, QSpinBox, QFrame, QTabWidget, QWidget)
from PySide6.QtCore import Qt, QEvent
from lang.local_translator import LocalTranslator
from database import DatabaseService
from PySide6.QtWidgets import QStyledItemDelegate
from ..core.models import SourceType, FileFormat, MatchedField, MatchedEntity, MappingProposal
from ..connectors.file_connector import FileConnector
from ..connectors.db_connector import DBConnector
from ..connectors.url_connector import URLConnector
from ..utils.field_creator import FieldCreator

class ComboBoxDelegate(QStyledItemDelegate):
    pass  # не используется, т.к. мы вставляем виджеты напрямую

class SourcePage(QWizardPage):
    # ... (без изменений, как в предыдущей версии)
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = wizard.translator
        self.setTitle(self.translator.tr('source_page_title'))
        self.setSubTitle(self.translator.tr('source_page_subtitle'))
        layout = QVBoxLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItem(self.translator.tr('source_type_file'), SourceType.FILE)
        self.type_combo.addItem(self.translator.tr('source_type_db'), SourceType.DATABASE)
        self.type_combo.addItem(self.translator.tr('source_type_url'), SourceType.URL)
        self.type_combo.currentIndexChanged.connect(self.toggle_groups)
        layout.addWidget(QLabel(self.translator.tr('source_type_label')))
        layout.addWidget(self.type_combo)

        self.file_group = QGroupBox(self.translator.tr('file_group'))
        file_layout = QVBoxLayout(self.file_group)
        self.format_combo = QComboBox()
        for fmt in [FileFormat.JSON, FileFormat.XML, FileFormat.DBF, FileFormat.CSV, FileFormat.EXCEL]:
            self.format_combo.addItem(fmt.value, fmt)
        file_layout.addWidget(QLabel(self.translator.tr('file_format_label')))
        file_layout.addWidget(self.format_combo)
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton(self.translator.tr('browse_button'))
        self.browse_btn.clicked.connect(self.browse_file)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        file_layout.addLayout(path_layout)
        layout.addWidget(self.file_group)

        self.db_group = QGroupBox(self.translator.tr('db_group'))
        db_layout = QVBoxLayout(self.db_group)
        self.db_type = QComboBox()
        self.db_type.addItems(["postgresql", "mysql", "mssql", "oracle"])
        db_layout.addWidget(QLabel(self.translator.tr('db_type_label')))
        db_layout.addWidget(self.db_type)
        self.db_host = QLineEdit("localhost")
        self.db_port = QLineEdit()
        self.db_name = QLineEdit()
        self.db_user = QLineEdit()
        self.db_pass = QLineEdit()
        self.db_pass.setEchoMode(QLineEdit.Password)
        db_layout.addWidget(QLabel(self.translator.tr('db_host_label')))
        db_layout.addWidget(self.db_host)
        db_layout.addWidget(QLabel(self.translator.tr('db_port_label')))
        db_layout.addWidget(self.db_port)
        db_layout.addWidget(QLabel(self.translator.tr('db_name_label')))
        db_layout.addWidget(self.db_name)
        db_layout.addWidget(QLabel(self.translator.tr('db_user_label')))
        db_layout.addWidget(self.db_user)
        db_layout.addWidget(QLabel(self.translator.tr('db_pass_label')))
        db_layout.addWidget(self.db_pass)
        layout.addWidget(self.db_group)

        self.url_group = QGroupBox(self.translator.tr('url_group'))
        url_layout = QVBoxLayout(self.url_group)
        self.url_edit = QLineEdit()
        url_layout.addWidget(QLabel(self.translator.tr('url_label')))
        url_layout.addWidget(self.url_edit)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        url_layout.addWidget(QLabel(self.translator.tr('http_method_label')))
        url_layout.addWidget(self.method_combo)
        layout.addWidget(self.url_group)

        layout.addStretch()
        self.toggle_groups()

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('source_page_title'))
        self.setSubTitle(self.translator.tr('source_page_subtitle'))
        self.type_combo.setItemText(0, self.translator.tr('source_type_file'))
        self.type_combo.setItemText(1, self.translator.tr('source_type_db'))
        self.type_combo.setItemText(2, self.translator.tr('source_type_url'))
        self.file_group.setTitle(self.translator.tr('file_group'))
        self.browse_btn.setText(self.translator.tr('browse_button'))
        self.db_group.setTitle(self.translator.tr('db_group'))
        self.url_group.setTitle(self.translator.tr('url_group'))

    def toggle_groups(self):
        st = self.type_combo.currentData()
        self.file_group.setVisible(st == SourceType.FILE)
        self.db_group.setVisible(st == SourceType.DATABASE)
        self.url_group.setVisible(st == SourceType.URL)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.translator.tr('select_file_dialog'))
        if path:
            self.path_edit.setText(path)

    def validatePage(self):
        st = self.type_combo.currentData()
        try:
            if st == SourceType.FILE:
                self.wizard.connector = FileConnector(self.path_edit.text(), self.format_combo.currentData())
            elif st == SourceType.DATABASE:
                params = {
                    'db_type': self.db_type.currentText(),
                    'host': self.db_host.text(),
                    'port': self.db_port.text() or None,
                    'database': self.db_name.text(),
                    'user': self.db_user.text(),
                    'password': self.db_pass.text()
                }
                self.wizard.connector = DBConnector("", **params)
            else:
                self.wizard.connector = URLConnector(self.url_edit.text())
            self.wizard.connector.connect()
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))
            return False


class SchemaPage(QWizardPage):
    # ... (без изменений)
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = wizard.translator
        self.setTitle(self.translator.tr('schema_page_title'))
        self.setSubTitle(self.translator.tr('schema_page_subtitle'))
        layout = QVBoxLayout(self)

        self.table_combo = QComboBox()
        self.table_combo.currentIndexChanged.connect(self.table_selected)
        layout.addWidget(QLabel(self.translator.tr('table_label')))
        layout.addWidget(self.table_combo)

        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        self.fields_table = QTableWidget(0, 2)
        self.fields_table.setHorizontalHeaderLabels([self.translator.tr('field_name_header'), self.translator.tr('field_type_header')])
        layout.addWidget(self.fields_table)

        self.loading = QLabel(self.translator.tr('loading_message'))
        layout.addWidget(self.loading)

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('schema_page_title'))
        self.setSubTitle(self.translator.tr('schema_page_subtitle'))
        self.fields_table.setHorizontalHeaderLabels([self.translator.tr('field_name_header'), self.translator.tr('field_type_header')])

    def initializePage(self):
        self.loading.show()
        self.wizard.schema = self.wizard.connector.get_schema()
        self.table_combo.clear()
        for t in self.wizard.schema.tables:
            self.table_combo.addItem(t.name, t.name)
        if self.wizard.schema.tables:
            self.table_selected(0)
        self.loading.hide()

    def table_selected(self, idx):
        table_name = self.table_combo.currentData()
        if not table_name:
            return
        for t in self.wizard.schema.tables:
            if t.name == table_name:
                self.current_table = t
                self.info_label.setText(f"{self.translator.tr('rows_count_label')}: {t.row_count or self.translator.tr('unknown')}, {self.translator.tr('samples_label')}: {len(t.sample_rows or [])}")
                self.fields_table.setRowCount(len(t.fields))
                for i, f in enumerate(t.fields):
                    self.fields_table.setItem(i, 0, QTableWidgetItem(f.name))
                    self.fields_table.setItem(i, 1, QTableWidgetItem(f.field_type.name))
                break

    def validatePage(self):
        self.wizard.selected_table_name = self.table_combo.currentData()
        return True


class MappingPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = wizard.translator
        self.setTitle(self.translator.tr('mapping_page_title'))
        self.setSubTitle(self.translator.tr('mapping_page_subtitle'))
        self.current_entity_id = None
        self.pending_fields = {}   # {row: {name, type, length, alias, ref}}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: выбор/создание сущности
        h_layout = QHBoxLayout()
        self.entity_combo = QComboBox()
        self.entity_combo.setEditable(True)
        self.entity_combo.addItem(self.translator.tr('create_new_entity'), None)
        self.entity_combo.currentIndexChanged.connect(self.on_entity_selected)
        h_layout.addWidget(QLabel(self.translator.tr('target_entity_label')))
        h_layout.addWidget(self.entity_combo)
        self.btn_create_entity = QPushButton(self.translator.tr('create_entity_button'))
        self.btn_create_entity.clicked.connect(self.create_new_entity)
        h_layout.addWidget(self.btn_create_entity)
        layout.addLayout(h_layout)

        # Таблица маппинга (исходные поля -> целевые поля)
        self.mapping_table = QTableWidget(0, 5)
        self.mapping_table.setHorizontalHeaderLabels([
            self.translator.tr('source_field_header'),
            self.translator.tr('target_field_header'),
            self.translator.tr('type_header'),
            self.translator.tr('length_header'),
            self.translator.tr('ref_header')
        ])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setItemDelegateForColumn(1, ComboBoxDelegate(self))  # Кастомный делегат
        layout.addWidget(self.mapping_table)

        # Кнопки действий
        btn_layout = QHBoxLayout()
        self.btn_apply_structure = QPushButton(self.translator.tr('apply_structure_button'))
        self.btn_apply_structure.clicked.connect(self.apply_structure)
        self.btn_import_data = QPushButton(self.translator.tr('import_data_button'))
        self.btn_import_data.clicked.connect(self.import_data)
        self.btn_import_data.setEnabled(False)
        btn_layout.addWidget(self.btn_apply_structure)
        btn_layout.addWidget(self.btn_import_data)
        layout.addLayout(btn_layout)

        # Вкладка предпросмотра данных
        self.preview_tab = QTabWidget()
        self.preview_table = QTableWidget()
        self.preview_tab.addTab(self.preview_table, self.translator.tr('data_preview_tab'))
        layout.addWidget(self.preview_tab)

        self.loading = QLabel(self.translator.tr('loading_message'))
        layout.addWidget(self.loading)
        self.refresh_entity_list()

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('mapping_page_title'))
        self.setSubTitle(self.translator.tr('mapping_page_subtitle'))
        self.entity_combo.setItemText(0, self.translator.tr('create_new_entity'))
        self.btn_create_entity.setText(self.translator.tr('create_entity_button'))
        self.btn_apply_structure.setText(self.translator.tr('apply_structure_button'))
        self.btn_import_data.setText(self.translator.tr('import_data_button'))
        self.preview_tab.setTabText(0, self.translator.tr('data_preview_tab'))
        self.mapping_table.setHorizontalHeaderLabels([
            self.translator.tr('source_field_header'),
            self.translator.tr('target_field_header'),
            self.translator.tr('type_header'),
            self.translator.tr('length_header'),
            self.translator.tr('ref_header')
        ])

    def refresh_entity_list(self):
        self.entity_combo.clear()
        self.entity_combo.addItem(self.translator.tr('create_new_entity'), None)
        rows = self.wizard.db.execute_query("SELECT id, cname, calias FROM meta.entitytypes ORDER BY cname")
        for eid, cname, calias in rows:
            self.entity_combo.addItem(f"{cname} ({calias})", eid)

    def on_entity_selected(self):
        self.current_entity_id = self.entity_combo.currentData()
        self.load_mapping_table()

    def load_mapping_table(self):
        if not self.wizard.schema:
            return
        source_table = None
        for t in self.wizard.schema.tables:
            if t.name == self.wizard.selected_table_name:
                source_table = t
                break
        if not source_table:
            self.mapping_table.setRowCount(0)
            return

        self.mapping_table.setRowCount(len(source_table.fields))
        for row, sf in enumerate(source_table.fields):
            self.mapping_table.setItem(row, 0, QTableWidgetItem(sf.name))
            # В колонке 1 – комбобокс с существующими полями + опция создания нового
            combo = QComboBox()
            combo.addItem("-- " + self.translator.tr('ignore_field') + " --", "")
            if self.current_entity_id:
                fields = self.wizard.db.execute_query(
                    "SELECT cfieldname, calias FROM meta.fields WHERE entitytypeid=%s",
                    (self.current_entity_id,)
                )
                for fname, calias in fields:
                    combo.addItem(f"{calias} ({fname})", fname)
            combo.addItem("++ " + self.translator.tr('create_new_field') + " ++", "__NEW__")
            combo.currentIndexChanged.connect(lambda idx, r=row: self.on_new_field_selected(r, combo))
            self.mapping_table.setCellWidget(row, 1, combo)
            self.mapping_table.setItem(row, 2, QTableWidgetItem(sf.field_type.name))
            self.mapping_table.setItem(row, 3, QTableWidgetItem(""))
            self.mapping_table.setItem(row, 4, QTableWidgetItem(""))
            # Если есть pending поля для этой строки, восстановить
            if row in self.pending_fields:
                self.show_pending_editor(row, self.pending_fields[row])

        # Загрузить предпросмотр данных
        self.load_preview(source_table)

    def on_new_field_selected(self, row, combo):
        if combo.currentData() == "__NEW__":
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            # Показываем редактор в строке
            self.show_pending_editor(row)

    def show_pending_editor(self, row, pending=None):
        # Создаём виджеты для ввода параметров нового поля
        # Временно сохраним в self.pending_fields и отобразим в дополнительных колонках
        # Для простоты используем QLineEdit в ячейках колонок 2-4
        name_edit = QLineEdit()
        if pending and pending.get('name'):
            name_edit.setText(pending['name'])
        else:
            source_field = self.mapping_table.item(row, 0).text()
            name_edit.setText(self.to_field_name(source_field))
        name_edit.textChanged.connect(lambda t, r=row: self.update_pending(r, 'name', t))
        self.mapping_table.setCellWidget(row, 2, name_edit)

        type_combo = QComboBox()
        type_combo.addItems(["C", "N", "I", "D", "T", "L", "M", "R"])
        if pending and pending.get('type'):
            idx = type_combo.findText(pending['type'])
            if idx >= 0:
                type_combo.setCurrentIndex(idx)
        type_combo.currentIndexChanged.connect(lambda idx, r=row: self.update_pending(r, 'type', type_combo.currentText()))
        self.mapping_table.setCellWidget(row, 3, type_combo)

        length_spin = QSpinBox()
        length_spin.setRange(1, 10000)
        length_spin.setValue(pending.get('length', 255) if pending else 255)
        length_spin.valueChanged.connect(lambda v, r=row: self.update_pending(r, 'length', v))
        self.mapping_table.setCellWidget(row, 4, length_spin)

        # Сохраняем pending
        self.pending_fields[row] = {
            'name': name_edit.text(),
            'type': type_combo.currentText(),
            'length': length_spin.value(),
            'alias': name_edit.text()
        }

    def update_pending(self, row, key, value):
        if row not in self.pending_fields:
            self.pending_fields[row] = {}
        self.pending_fields[row][key] = value

    def to_field_name(self, source_field):
        # Преобразует имя исходного поля в допустимое имя поля MySQL/CamelCase
        import re
        name = re.sub(r'[^a-zA-Z0-9_]', '_', source_field)
        if name[0].isdigit():
            name = '_' + name
        return name.lower()

    def apply_structure(self):
        if not self.current_entity_id:
            QMessageBox.warning(self, self.translator.tr('warning'), self.translator.tr('select_entity_first'))
            return
        # Собираем все новые поля из pending_fields
        fields_to_create = []
        for row, pending in self.pending_fields.items():
            if not pending.get('name'):
                continue
            fields_to_create.append({
                'cfieldname': pending['name'],
                'cfieldtype': pending.get('type', 'C'),
                'calias': pending.get('alias', pending['name']),
                'nlength': pending.get('length', 255),
                'lisindexed': True
            })
        if not fields_to_create:
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('no_fields_to_create'))
            return
        # Транзакция через FieldCreator
        creator = FieldCreator(self.wizard.db)
        try:
            created_ids = creator.create_fields(self.current_entity_id, fields_to_create)
            QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('structure_created', len(created_ids)))
            self.btn_import_data.setEnabled(True)
            # Обновить таблицу маппинга: убрать редакторы, загрузить существующие поля
            self.load_mapping_table()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('error'), str(e))

    def import_data(self):
        # Собрать маппинг для импорта
        matched_fields = []
        for row in range(self.mapping_table.rowCount()):
            source_field = self.mapping_table.item(row, 0).text()
            combo = self.mapping_table.cellWidget(row, 1)
            target_field = combo.currentData()
            if target_field and target_field != "__NEW__":
                matched_fields.append(MatchedField(
                    source_field=source_field,
                    target_field=target_field,
                    confidence=1.0,
                    is_reference=False
                ))
        # Создаём MatchedEntity
        matched_entity = MatchedEntity(
            source_table=self.wizard.selected_table_name,
            target_entity_id=self.current_entity_id,
            target_entity_name="",
            confidence=1.0,
            fields=matched_fields,
            is_new=False
        )
        self.wizard.matching_proposal = MappingProposal(
            source_schema=self.wizard.schema,
            entities=[matched_entity],
            unresolved_tables=[],
            suggestions_for_new_entities=[]
        )
        # Переходим на страницу импорта (ExecutePage)
        self.wizard.next()

    def load_preview(self, source_table):
        if not source_table.sample_rows:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return
        sample = source_table.sample_rows
        if not sample:
            return
        headers = list(sample[0].keys())
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(sample))
        for i, row in enumerate(sample):
            for j, col in enumerate(headers):
                val = row.get(col, '')
                self.preview_table.setItem(i, j, QTableWidgetItem(str(val)))
        self.preview_table.resizeColumnsToContents()

    def create_new_entity(self):
        from .wizard_dialogs import NewEntityDialog
        dlg = NewEntityDialog(self, self.wizard.db)
        if dlg.exec_():
            data = dlg.get_data()
            res = self.wizard.db.execute_query(
                """INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisversioned, isecuritystrategy, status_id)
                   VALUES (%s, %s, %s, '', true, 1, 1) RETURNING id""",
                (data['cname'], data['calias'], data['class_id'])
            )
            if res:
                entity_id = res[0][0]
                QMessageBox.information(self, self.translator.tr('info'), self.translator.tr('entity_created'))
                self.refresh_entity_list()
                idx = self.entity_combo.findData(entity_id)
                if idx >= 0:
                    self.entity_combo.setCurrentIndex(idx)
                self.current_entity_id = entity_id
                self.load_mapping_table()


class ExecutePage(QWizardPage):
    # ... (без изменений, как в предыдущей версии)
    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.translator = wizard.translator
        self.setTitle(self.translator.tr('execute_page_title'))
        self.setSubTitle(self.translator.tr('execute_page_subtitle'))
        layout = QVBoxLayout(self)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.import_thread = None

    def retranslate_ui(self):
        self.setTitle(self.translator.tr('execute_page_title'))
        self.setSubTitle(self.translator.tr('execute_page_subtitle'))

    def initializePage(self):
        from ..core.models import ImportProfile
        from ..core.profile_manager import ProfileManager
        profile = ImportProfile(
            name=f"Import {self.wizard.connector.source_path}",
            source_type=self.wizard.connector.source_type,
            source_path=self.wizard.connector.source_path,
            mapping_proposal=self.wizard.matching_proposal
        )
        prof_mgr = ProfileManager(self.wizard.db)
        prof_mgr.save_profile(profile)
        self.wizard.profile = profile

        from ..core.import_engine import ImportEngine
        from .import_wizard import ImportThread
        self.import_thread = ImportThread(self.wizard.db, self.wizard.connector, profile)
        self.import_thread.progress.connect(self.update_progress)
        self.import_thread.finished.connect(self.on_finished)
        self.import_thread.error.connect(self.on_error)
        self.import_thread.start()

    def update_progress(self, current, total):
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        self.log.append(f"{self.translator.tr('processed_records')}: {current} / {total}")

    def on_finished(self, stats):
        self.log.append(f"{self.translator.tr('import_finished')}. {self.translator.tr('inserted')}: {stats['inserted']}, {self.translator.tr('updated')}: {stats['updated']}, {self.translator.tr('errors')}: {stats['errors']}")
        QMessageBox.information(self, self.translator.tr('import_finished_title'), self.translator.tr('import_finished'))

    def on_error(self, msg):
        self.log.append(f"{self.translator.tr('error')}: {msg}")
        QMessageBox.critical(self, self.translator.tr('error'), msg)