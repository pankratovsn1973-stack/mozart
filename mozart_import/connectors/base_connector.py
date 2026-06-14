# mozart_import/connectors/base_connector.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Generator
from ..core.models import SourceSchema, SourceTable, SourceField, FieldType, SourceType


class BaseConnector(ABC):
    """Абстрактный базовый класс для всех коннекторов к источникам данных."""

    def __init__(self, source_path: str, **kwargs):
        self.source_path = source_path
        self.options = kwargs

    @abstractmethod
    def connect(self) -> bool:
        """Устанавливает соединение с источником. Возвращает True при успехе."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Закрывает соединение."""
        pass

    @abstractmethod
    def get_schema(self) -> SourceSchema:
        """Извлекает схему источника (таблицы, поля, типы, связи)."""
        pass

    @abstractmethod
    def get_table_sample(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает первые `limit` записей из указанной таблицы."""
        pass

    @abstractmethod
    def iter_records(self, table_name: str, batch_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        """Генератор, возвращающий записи пакетами для итеративной обработки."""
        pass

    @abstractmethod
    def get_row_count(self, table_name: str) -> Optional[int]:
        """Возвращает приблизительное количество записей в таблице."""
        pass