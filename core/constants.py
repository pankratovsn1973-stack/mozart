# core/constants.py
# -*- coding: utf-8 -*-
"""
Глобальные константы ядра Mozart ERP.

Вынесены отдельно, чтобы избежать циклических импортов между
CollectionManager, ObjectPropertyCollection, BridgeResolver и UI-слоем.
"""

# --- Геометрия ---------------------------------------------------------
# Свойства, менять которые разрешено ТОЛЬКО через сцену (визивиг).
GEOMETRY_PROPS = frozenset({'myx', 'myy', 'mywidth', 'myheight'})

# Источники, из которых допустима запись геометрии в модель.
# 'vizivig' — из хендлов на сцене; 'init' — при первичной загрузке.
ALLOWED_GEOMETRY_SOURCES = frozenset({'vizivig', 'init'})

# Источники, при которых UI-реактивность не должна срабатывать.
# 'silent' — программная запись в silent_mode; 'init' — первичная загрузка.
SILENT_SOURCES = frozenset({'silent', 'init'})

# --- Типы объектов в индексе idCol -------------------------------------
IDCOL_KIND_ELEMENT = 'element'
IDCOL_KIND_PROP    = 'prop'
IDCOL_KIND_METHOD  = 'method'
IDCOL_KIND_SIGNAL  = 'signal'

# --- Прочее ------------------------------------------------------------
LEGACY_LOG_FILENAME = 'legacy_set_value_calls.log'