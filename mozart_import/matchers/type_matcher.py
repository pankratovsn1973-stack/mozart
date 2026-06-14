# mozart_import/matchers/type_matcher.py
from ..core.models import FieldType


class TypeMatcher:
    """Сопоставление типов данных источника и Mozart."""

    # Маппинг типов источника -> коды типов Mozart (C, I, N, D, T, L, M, R)
    TYPE_MAPPING = {
        FieldType.STRING: 'C',
        FieldType.INTEGER: 'I',
        FieldType.FLOAT: 'N',
        FieldType.BOOLEAN: 'L',
        FieldType.DATE: 'D',
        FieldType.DATETIME: 'T',
        FieldType.TIME: 'T',
        FieldType.BINARY: 'F',
    }

    @classmethod
    def get_mozart_type(cls, source_type: FieldType) -> str:
        return cls.TYPE_MAPPING.get(source_type, 'C')

    @classmethod
    def is_compatible(cls, source_type: FieldType, mozart_type: str) -> bool:
        target = cls.get_mozart_type(source_type)
        if target == mozart_type:
            return True
        # Дополнительные совместимости
        if source_type == FieldType.INTEGER and mozart_type == 'N':
            return True
        if source_type == FieldType.FLOAT and mozart_type == 'N':
            return True
        if source_type == FieldType.STRING and mozart_type == 'C':
            return True
        return False