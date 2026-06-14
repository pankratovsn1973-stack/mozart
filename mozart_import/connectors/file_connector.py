# mozart_import/connectors/file_connector.py
import os
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Generator
from .base_connector import BaseConnector
from ..core.models import SourceSchema, SourceTable, SourceField, FieldType, SourceType, FileFormat

try:
    from dbfread import DBF
    DBF_AVAILABLE = True
except ImportError:
    DBF_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from lxml import etree as lxml_etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


def _clean_key(key: str) -> str:
    """
    Очищает ключ от пространства имён XML и заменяет проблемные символы.
    Например: '{urn:cbr-ru:ed:v2.0}ParticipantInfo' -> 'ParticipantInfo'
    """
    if '}' in key:
        key = key.split('}', 1)[1]
    # Замена дефисов и точек на подчёркивания (опционально)
    key = key.replace('-', '_').replace('.', '_')
    return key


def flatten_xml_element(elem, prefix=''):
    """
    Рекурсивно преобразует XML-элемент lxml в плоский словарь.
    При повторяющихся тегах оставляет ТОЛЬКО ПЕРВОЕ вхождение.
    Ключи очищаются от пространств имён.
    """
    result = {}
    # Атрибуты элемента
    for attr, value in elem.attrib.items():
        clean_attr = _clean_key(attr)
        full_key = f"{prefix}{clean_attr}" if prefix else clean_attr
        result[full_key] = value

    # Текстовое содержимое, если нет дочерних элементов
    if not len(elem) and elem.text and elem.text.strip():
        text_key = f"{prefix}text" if prefix else "text"
        result[text_key] = elem.text.strip()

    # Дочерние элементы
    for child in elem:
        child_tag = _clean_key(child.tag)
        child_prefix = f"{prefix}{child_tag}_" if prefix else f"{child_tag}_"
        child_data = flatten_xml_element(child, child_prefix)
        for k, v in child_data.items():
            if k not in result:
                result[k] = v
    return result


class FileConnector(BaseConnector):
    def __init__(self, source_path: str, file_format: FileFormat, **kwargs):
        super().__init__(source_path, **kwargs)
        self.file_format = file_format
        self._data = None

    def connect(self) -> bool:
        if not os.path.exists(self.source_path):
            raise FileNotFoundError(f"Файл не найден: {self.source_path}")
        self._load_data()
        return True

    def disconnect(self) -> None:
        self._data = None

    def _load_data(self):
        if self.file_format == FileFormat.JSON:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
                if isinstance(self._data, dict):
                    self._data = [self._data]
        elif self.file_format == FileFormat.XML:
            if not LXML_AVAILABLE:
                raise ImportError("Установите lxml: pip install lxml")
            tree = lxml_etree.parse(self.source_path)
            root = tree.getroot()
            records = []
            for elem in root:
                record = flatten_xml_element(elem)
                records.append(record)
            self._data = records
        elif self.file_format == FileFormat.DBF:
            if not DBF_AVAILABLE:
                raise ImportError("Установите dbfread: pip install dbfread")
            table = DBF(self.source_path, ignore_missing_memofile=True)
            self._data = list(table)
        elif self.file_format in (FileFormat.CSV, FileFormat.EXCEL):
            if not PANDAS_AVAILABLE:
                raise ImportError("Установите pandas: pip install pandas")
            if self.file_format == FileFormat.CSV:
                df = pd.read_csv(self.source_path)
            else:
                df = pd.read_excel(self.source_path)
            self._data = df.to_dict(orient='records')
        else:
            raise ValueError(f"Неподдерживаемый формат: {self.file_format}")

    def get_schema(self) -> SourceSchema:
        if self._data is None:
            self._load_data()
        if not self._data:
            return SourceSchema(source_type=SourceType.FILE, source_path=self.source_path)
        sample = self._data[0]
        fields = []
        for name, value in sample.items():
            if isinstance(value, str):
                ftype = FieldType.STRING
                length = len(value)
            elif isinstance(value, int):
                ftype = FieldType.INTEGER
                length = None
            elif isinstance(value, float):
                ftype = FieldType.FLOAT
                length = None
            elif isinstance(value, bool):
                ftype = FieldType.BOOLEAN
                length = None
            else:
                ftype = FieldType.STRING
                length = None
            fields.append(SourceField(
                name=name,
                field_type=ftype,
                length=length,
                nullable=False,
                sample_values=[value]
            ))
        table = SourceTable(
            name=os.path.basename(self.source_path),
            fields=fields,
            sample_rows=self._data[:10]
        )
        return SourceSchema(
            source_type=SourceType.FILE,
            source_path=self.source_path,
            tables=[table]
        )

    def get_table_sample(self, table_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        if self._data is None:
            self._load_data()
        return self._data[:limit]

    def iter_records(self, table_name: str = None, batch_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        if self._data is None:
            self._load_data()
        for i in range(0, len(self._data), batch_size):
            yield self._data[i:i+batch_size]

    def get_row_count(self, table_name: str = None) -> Optional[int]:
        if self._data is None:
            self._load_data()
        return len(self._data)