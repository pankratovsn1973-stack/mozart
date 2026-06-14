

# import_readers.py
import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator

try:
    from dbfread import DBF
    DBF_AVAILABLE = True
except ImportError:
    DBF_AVAILABLE = False


class BaseReader(ABC):
    """Абстрактный читатель источника данных."""

    @abstractmethod
    def get_fields(self) -> List[str]:
        """Возвращает список имён полей в источнике."""
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Итератор по записям, каждая запись – словарь поле->значение."""
        pass


class JsonReader(BaseReader):
    def __init__(self, path: str):
        self.path = path
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            self.records = data
        else:
            self.records = [data]

    def get_fields(self) -> List[str]:
        if self.records:
            return list(self.records[0].keys())
        return []

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        for rec in self.records:
            yield rec


class XmlReader(BaseReader):
    def __init__(self, path: str):
        self.path = path
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        # Предполагаем, что записи – это дочерние элементы корня
        self.records = list(self.root)

    def get_fields(self) -> List[str]:
        if self.records:
            # Собираем все возможные теги из первого элемента
            return [child.tag for child in self.records[0]]
        return []

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        for elem in self.records:
            rec = {child.tag: child.text for child in elem}
            yield rec


class DbfReader(BaseReader):
    def __init__(self, path: str):
        if not DBF_AVAILABLE:
            raise ImportError("Библиотека dbfread не установлена. Установите: pip install dbfread")
        self.table = DBF(path, ignore_missing_memofile=True)
        self.records = list(self.table)

    def get_fields(self) -> List[str]:
        return [field.name for field in self.table.fields]

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        for rec in self.records:
            yield dict(rec)