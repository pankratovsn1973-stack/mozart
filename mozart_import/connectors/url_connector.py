# mozart_import/connectors/url_connector.py
import requests
import json
from typing import List, Dict, Any, Optional, Generator, Callable, Union
from .base_connector import BaseConnector
#from ..core.models import SourceSchema, SourceTable, SourceField, FieldType, SourceType
import zipfile
import tempfile
import os
import io
from ..core.models import SourceSchema, SourceTable, SourceField, FieldType, SourceType, FileFormat

class URLConnector(BaseConnector):
    """
    Коннектор для HTTP/HTTPS источников (REST API, RSS, веб-страницы).
    Параметры:
        headers: dict с HTTP-заголовками
        pagination: dict с настройками пагинации
            - type: 'offset', 'page', 'cursor', 'next_url'
            - param_name: имя параметра (page, offset, cursor)
            - page_size: количество записей на страницу
            - next_url_path: JSONPath до URL следующей страницы
        data_path: JSONPath до массива данных (например, 'data.items')
        method: 'GET' или 'POST'
        body: dict для POST-запроса
    """
    def __init__(self, source_path: str, **kwargs):
        super().__init__(source_path, **kwargs)
        self.method = kwargs.get('method', 'GET')
        self.headers = kwargs.get('headers', {})
        self.pagination = kwargs.get('pagination', {})
        self.data_path = kwargs.get('data_path', None)
        self.body = kwargs.get('body', None)
        self.session = None

    def connect(self) -> bool:
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        return True

    def disconnect(self) -> None:
        if self.session:
            self.session.close()
            self.session = None

    def _get_json_path(self, data: Any, path: str) -> Any:
        if not path:
            return data
        parts = path.split('.')
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            elif isinstance(data, list) and part.isdigit() and int(part) < len(data):
                data = data[int(part)]
            else:
                return None
        return data

    def _extract_records(self, response_json: Dict) -> List[Dict]:
        if self.data_path:
            data = self._get_json_path(response_json, self.data_path)
            if isinstance(data, list):
                return data
            else:
                return []
        # Если data_path не задан, предполагаем, что JSON сам является массивом
        if isinstance(response_json, list):
            return response_json
        # Или смотрим первый ключ, который содержит список
        for value in response_json.values():
            if isinstance(value, list):
                return value
        return []

    def _get_next_url(self, response_json: Dict) -> Optional[str]:
        if self.pagination.get('type') == 'next_url':
            next_path = self.pagination.get('next_url_path')
            if next_path:
                return self._get_json_path(response_json, next_path)
        return None

    def fetch_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        results = []
        url = self.source_path
        page = 1
        offset = 0
        while True:
            paginated_url = self._build_paginated_url(url, page, offset)
            response = self.session.request(self.method, paginated_url, json=self.body)
            response.raise_for_status()
            data = response.json()
            records = self._extract_records(data)
            results.extend(records)
            if limit and len(results) >= limit:
                results = results[:limit]
                break
            next_url = self._get_next_url(data)
            if next_url:
                url = next_url
                continue
            if self.pagination.get('type') == 'page':
                page += 1
                continue
            if self.pagination.get('type') == 'offset':
                offset += self.pagination.get('page_size', 100)
                continue
            break
        return results

    def _build_paginated_url(self, base_url: str, page: int, offset: int) -> str:
        pag_type = self.pagination.get('type')
        if pag_type == 'page':
            param = self.pagination.get('param_name', 'page')
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}{param}={page}"
        elif pag_type == 'offset':
            param = self.pagination.get('param_name', 'offset')
            page_size = self.pagination.get('page_size', 100)
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}{param}={offset}&limit={page_size}"
        else:
            return base_url

    def get_schema(self) -> SourceSchema:
        # Для URL-источников схему получаем из первой страницы
        sample_data = self.fetch_all(limit=10)
        if not sample_data:
            return SourceSchema(source_type=SourceType.URL, source_path=self.source_path)
        sample = sample_data[0]
        fields = []
        for name, value in sample.items():
            if isinstance(value, str):
                ftype = FieldType.STRING
            elif isinstance(value, int):
                ftype = FieldType.INTEGER
            elif isinstance(value, float):
                ftype = FieldType.FLOAT
            elif isinstance(value, bool):
                ftype = FieldType.BOOLEAN
            elif isinstance(value, dict) or isinstance(value, list):
                ftype = FieldType.STRING
            else:
                ftype = FieldType.STRING
            fields.append(SourceField(name=name, field_type=ftype, nullable=True))
        source_table = SourceTable(
            name="data",
            fields=fields,
            sample_rows=sample_data[:5]
        )
        return SourceSchema(
            source_type=SourceType.URL,
            source_path=self.source_path,
            tables=[source_table]
        )

    def get_table_sample(self, table_name: str = "data", limit: int = 100) -> List[Dict[str, Any]]:
        return self.fetch_all(limit=limit)

    def iter_records(self, table_name: str = "data", batch_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        all_data = self.fetch_all()
        for i in range(0, len(all_data), batch_size):
            yield all_data[i:i+batch_size]

    def get_row_count(self, table_name: str = "data") -> Optional[int]:
        # Для API точное количество получить сложно, возвращаем None
        return None