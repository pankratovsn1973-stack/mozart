# mozart_import/core/models.py
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class SourceType(Enum):
    FILE = "file"
    DATABASE = "database"
    URL = "url"


class FileFormat(Enum):
    JSON = "json"
    XML = "xml"
    DBF = "dbf"
    CSV = "csv"
    EXCEL = "excel"


class FieldType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    BINARY = "binary"


# Вспомогательные классы для визуализации графа
class NodeType(Enum):
    SOURCE_TABLE = "source_table"
    MOZART_ENTITY = "mozart_entity"


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"


class LinkType(Enum):
    IMPORT = "import"
    FK_SOURCE = "fk_source"
    COMPOSITION = "composition"


@dataclass
class Field:
    name: str
    data_type: DataType = DataType.STRING
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None


@dataclass
class Node:
    id: str
    name: str
    node_type: NodeType
    fields: List[Field] = field(default_factory=list)
    x: float = 0
    y: float = 0
    table_name: Optional[str] = None   # для таблиц источника
    entity_id: Optional[int] = None    # для сущностей Mozart
    class_alias: Optional[str] = None


@dataclass
class SourceField:
    name: str
    field_type: FieldType
    length: Optional[int] = None
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    refers_to: Optional[str] = None
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class SourceTable:
    name: str
    fields: List[SourceField] = field(default_factory=list)
    primary_key: Optional[List[str]] = None
    foreign_keys: Dict[str, str] = field(default_factory=dict)
    row_count: Optional[int] = None
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SourceSchema:
    source_type: SourceType
    source_path: str
    tables: List[SourceTable] = field(default_factory=list)


@dataclass
class MatchedField:
    source_field: str
    target_field: str
    confidence: float = 1.0
    transformation: Optional[str] = None
    is_reference: bool = False
    ref_entitytype_id: Optional[int] = None
    field_type: str = "C"
    field_length: int = 255
    is_source_id: bool = False


@dataclass
class MatchedEntity:
    source_table: str
    target_entity_id: Optional[int]
    target_entity_name: str
    confidence: float
    fields: List[MatchedField] = field(default_factory=list)
    is_new: bool = False
    is_document: bool = False
    source_id_field: Optional[str] = None


@dataclass
class MappingProposal:
    source_schema: SourceSchema
    entities: List[MatchedEntity] = field(default_factory=list)
    unresolved_tables: List[str] = field(default_factory=list)
    suggestions_for_new_entities: List[str] = field(default_factory=list)


@dataclass
class ImportProfile:
    id: Optional[int] = None
    name: str = ""
    source_type: SourceType = SourceType.FILE
    source_path: str = ""
    format: Optional[FileFormat] = None
    connection_params: Dict[str, str] = field(default_factory=dict)
    mapping_proposal: Optional[MappingProposal] = None
    scheduled: bool = False
    schedule_cron: Optional[str] = None
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    scene_json: Optional[str] = None

    # Нормализованные поля
    source_tables: List[Dict] = field(default_factory=list)
    target_entities: List[Dict] = field(default_factory=list)
    import_links: List[Dict] = field(default_factory=list)
    source_fk_links: List[Dict] = field(default_factory=list)
    source_references: List[Dict] = field(default_factory=list)  # ручные ссылки источника

    # Параметры подключения
    file_format: Optional[str] = None
    db_type: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_pass: Optional[str] = None

    # Режим импорта: 'append' - только новые, 'full_update' - обновление при изменении данных
    import_mode: str = 'append'   # 'append' или 'full_update'