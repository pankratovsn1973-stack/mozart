

# import_models.py
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Mapping:
    """Сопоставление одного поля."""
    target_field: str           # имя поля в сущности (или специальное 'sourceid')
    source_field: str           # поле в источнике
    is_reference: bool = False
    ref_entitytype_id: Optional[int] = None   # для ссылок
    ref_field_name: Optional[str] = None      # имя создаваемого ссылочного поля


@dataclass
class SourceSettings:
    """Настройки источника импорта."""
    source_type: str            # 'F' или 'U'
    source_path: str
    format: str                 # 'J', 'X', 'D'
    source_name: str = ""
    id_field: str = ""          # поле в источнике, которое будет sourceid
    mappings: List[Mapping] = None