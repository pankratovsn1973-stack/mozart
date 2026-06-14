# -*- coding: utf-8 -*-
# tabs/data_view_tab.py
# Модуль: Оперативный просмотр справочников
# Назначение: Вкладка для быстрого просмотра активных версий сущностей
#            (справочников, документов) с выводом всех полей ext-таблицы
# Исправление: исправлена ошибка использования calias вместо cname
#              для построения имени ext-таблицы

from PySide6.QtWidgets import QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QHeaderView
from PySide6.QtCore import Qt
from .base_tab import BaseTab


class DataViewTab(BaseTab):
    """Вкладка 5: Оперативный просмотр справочников.
    Позволяет выбрать тип сущности из выпадающего списка
    и отображает все активные версии с данными из ext-таблицы."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Тип сущности:"))
        self.combo_entity = QComboBox()
        self.combo_entity.currentIndexChanged.connect(self.on_entity_changed)
        h_layout.addWidget(self.combo_entity)
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.load_data)
        h_layout.addWidget(self.btn_refresh)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.load_entity_types()

    def load_entity_types(self):
        """Загружает список всех типов сущностей в выпадающий список."""
        sql = "SELECT id, cname, calias FROM meta.entitytypes ORDER BY cname"
        rows = self.db.execute_query(sql)
        self.combo_entity.clear()
        self.combo_entity.addItem("-- Выберите сущность --", None)
        for eid, name, alias in rows:
            self.combo_entity.addItem(f"{name} ({alias})", eid)

    def on_entity_changed(self, index):
        """Обработчик выбора сущности в комбобоксе."""
        if index > 0:
            self.load_data()

    def load_data(self):
        """Загружает и отображает активные версии выбранной сущности.
        Использует cname (латинское имя) для построения имени ext-таблицы,
        а не calias (который может содержать спецсимволы)."""
        entity_id = self.combo_entity.currentData()
        if not entity_id:
            return

        # Получаем cname (латинское имя) вместо calias для построения имени таблицы
        sql = "SELECT cname FROM meta.entitytypes WHERE id = %s"
        res = self.db.execute_query(sql, (entity_id,))
        if not res:
            return

        cname = res[0][0]
        ext_table = f"ext.ext_{cname.lower()}"

        # Проверяем существование ext-таблицы
        sql = "SELECT to_regclass(%s)"
        exists = self.db.execute_query(sql, (ext_table,))
        if not exists or not exists[0][0]:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.show_info(f"Таблица {ext_table} не найдена")
            return

        # Получаем поля сущности (только из meta.fields, не системные)
        sql_fields = """SELECT cfieldname, calias FROM meta.fields
                        WHERE entitytypeid = %s ORDER BY isortorder"""
        fields = self.db.execute_query(sql_fields, (entity_id,))
        if not fields:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.show_info("У сущности нет полей")
            return

        field_names = [f[0] for f in fields]
        field_aliases = [f[1] for f in fields]

        # Собираем запрос: ID версии, имя сущности, все поля из ext-таблицы
        select_cols = ["v.id as version_id", "v.cname as entity_name"] + [f"e.{fn}" for fn in field_names]
        sql = f"""
            SELECT {', '.join(select_cols)}
            FROM data.entity_instances i
            JOIN data.entity_versions v ON i.id = v.instanceid AND v.cversionstatus = 'Active'
            JOIN {ext_table} e ON v.id = e.versionid
            WHERE i.entitytypeid = %s
            LIMIT 1000
        """
        rows = self.db.execute_query(sql, (entity_id,))

        # Отображаем данные в таблице
        headers = ["ID версии", "Наименование"] + field_aliases
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)
        for r in rows:
            pos = self.table.rowCount()
            self.table.insertRow(pos)
            for c, val in enumerate(r):
                item = QTableWidgetItem(str(val) if val is not None else "")
                self.table.setItem(pos, c, item)