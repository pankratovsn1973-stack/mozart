# mozart_import/designer/designer_utils.py
# -*- coding: utf-8 -*-

import re

def to_field_name(source_name: str) -> str:
    """Преобразует имя исходного поля в допустимое имя поля PostgreSQL (латиница, подчёркивания)."""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', source_name)
    if name[0].isdigit():
        name = '_' + name
    return name.lower()[:63]