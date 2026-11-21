# -*- coding: utf-8 -*-
"""
Встроенные функции трансляции low-code свойств в Qt/Python и обратно.
Регистрируются в BridgeFunctionRegistry при старте приложения.

Имена функций совпадают с тем, что записано в БД:
  class_property_bridge.bridgecalcset / bridgecalcget / fuuncselectionvalue
"""
import json
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QFileDialog, QFontDialog, QColorDialog

from core.bridge_function_registry import BridgeFunctionKind, BridgeFunctionRegistry


# =========================================================================
# Универсальные DIRECT-трансляторы (text, number, boolean, choice, json)
# =========================================================================
def direct_to_qt(widget: QWidget, prop_key: str, value: str):
    if value is None:
        return
    s = str(value)
    if s.lower() in ("true", "false"):
        widget.setProperty(prop_key, s.lower() == "true")
    elif s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        widget.setProperty(prop_key, int(s))
    else:
        try:
            widget.setProperty(prop_key, float(s))
        except ValueError:
            widget.setProperty(prop_key, s)


def direct_from_qt(widget: QWidget, prop_key: str) -> str:
    val = widget.property(prop_key)
    return "" if val is None else str(val)


# =========================================================================
# Шрифт
# =========================================================================
def font_to_qt(widget: QWidget, prop_key: str, value: str):
    if not value:
        return
    if value.count(",") == 1:
        family, size_str = value.split(",", 1)
        try:
            size = int(size_str.strip())
        except ValueError:
            size = 11
        f = QFont(family.strip(), size)
    else:
        f = QFont()
        f.fromString(value)
    widget.setFont(f)


def font_from_qt(widget: QWidget, prop_key: str) -> str:
    f = widget.font()
    size = f.pointSize() if f.pointSize() > 0 else f.pixelSize()
    return f"{f.family()},{size}"


def select_font_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    font, ok = QFontDialog.getFont(parent)
    if not ok:
        return None
    size = font.pointSize() if font.pointSize() > 0 else font.pixelSize()
    return f"{font.family()},{size}"


# =========================================================================
# Цвет (CSS)
# =========================================================================
def color_to_css(widget: QWidget, prop_key: str, value: str):
    if not value:
        return
    css_prop = "background-color" if "back" in prop_key else "color"
    current = widget.styleSheet() or ""
    import re
    pattern = rf"{css_prop}\s*:\s*[^;]+;"
    replacement = f"{css_prop}: {value};"
    if re.search(pattern, current):
        new_css = re.sub(pattern, replacement, current)
    else:
        new_css = current + (" " if current else "") + replacement
    widget.setStyleSheet(new_css)


def color_from_css(widget: QWidget, prop_key: str) -> str:
    import re
    css = widget.styleSheet() or ""
    css_prop = "background-color" if "back" in prop_key else "color"
    m = re.search(rf"{css_prop}\s*:\s*([^;]+);", css)
    return m.group(1).strip() if m else ""


def select_color_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    color = QColorDialog.getColor(parent=parent)
    return color.name() if color.isValid() else None


# =========================================================================
# Размер (QSize) — для minimumSize / maximumSize
# =========================================================================
def size_to_qt(widget: QWidget, prop_key: str, value: str):
    if not value:
        return
    import re
    nums = [int(n) for n in re.findall(r"-?\d+", value)]
    if len(nums) >= 2:
        widget.setProperty(prop_key, QSize(nums[0], nums[1]))


def size_from_qt(widget: QWidget, prop_key: str) -> str:
    size = widget.property(prop_key)
    if isinstance(size, QSize):
        return f"{size.width()};{size.height()}"
    return ""


def select_size_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    from PySide6.QtWidgets import QInputDialog
    text, ok = QInputDialog.getText(parent, "Размер", "Ширина;Высота (например 100;30):")
    return text.strip() if ok else None


# =========================================================================
# Картинка
# =========================================================================
def image_to_qt(widget: QWidget, prop_key: str, value: str):
    if not value:
        return
    if prop_key == "pixmap" and hasattr(widget, "setPixmap"):
        widget.setPixmap(QPixmap(value))
    elif prop_key == "icon" and hasattr(widget, "setIcon"):
        widget.setIcon(QIcon(value))
    elif prop_key == "c_background_image":
        css = widget.styleSheet() or ""
        import re
        pattern = r"background-image\s*:\s*[^;]+;"
        replacement = f"background-image: url({value});"
        if re.search(pattern, css):
            css = re.sub(pattern, replacement, css)
        else:
            css = css + (" " if css else "") + replacement
        widget.setStyleSheet(css)


def image_from_qt(widget: QWidget, prop_key: str) -> str:
    if prop_key == "c_background_image":
        import re
        css = widget.styleSheet() or ""
        m = re.search(r"background-image\s*:\s*url\(([^)]+)\);", css)
        return m.group(1).strip() if m else ""
    return ""


def select_image_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    path, _ = QFileDialog.getOpenFileName(
        parent, "Выбор изображения", "",
        "Images (*.png *.jpg *.jpeg *.bmp *.svg);;All files (*)"
    )
    return path or None


# =========================================================================
# Список (QComboBox / QListWidget) — JSON-список
# =========================================================================
def items_to_qt(widget: QWidget, prop_key: str, value: str):
    if not value:
        return
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return
    if not isinstance(items, list):
        return
    if hasattr(widget, "clear") and hasattr(widget, "addItem"):
        widget.clear()
        for item in items:
            if isinstance(item, dict):
                widget.addItem(
                    str(item.get("display", item.get("value", ""))),
                    item.get("value")
                )
            else:
                widget.addItem(str(item))


def items_from_qt(widget: QWidget, prop_key: str) -> str:
    items = []
    if hasattr(widget, "count") and hasattr(widget, "itemText"):
        for i in range(widget.count()):
            text = widget.itemText(i)
            data = widget.itemData(i) if hasattr(widget, "itemData") else text
            items.append({"value": data if data is not None else text, "display": text})
    return json.dumps(items, ensure_ascii=False)


# =========================================================================
# Метаданные (ERP-поля, не транслируются в виджет)
# =========================================================================
def metadata_to_qt(widget: QWidget, prop_key: str, value: str):
    """binding_entity, display_field, selector_form — только в коллекции, не в Qt."""
    pass


def metadata_from_qt(widget: QWidget, prop_key: str) -> str:
    return ""


# =========================================================================
# Диалоги выбора: сущность / поле / форма
# =========================================================================
def select_entity_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    """Выбор сущности из meta.entitytypes. Возвращает str(id) или None."""
    from dialogs.select_entity_dialog import SelectEntityDialog
    from database import DatabaseService
    dlg = SelectEntityDialog(parent, db=DatabaseService(), current_value=current_value)
    if dlg.exec_() == dlg.Accepted:
        return dlg.get_selected_id()
    return None


def select_field_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    """
    Выбор поля сущности (вшитого или расширения).
    entity_id задан  → только эта сущность;
    entity_id=None   → дерево всех сущностей.
    Возвращает str(id) поля или None.
    """
    from dialogs.select_field_dialog import SelectFieldDialog
    from database import DatabaseService
    dlg = SelectFieldDialog(parent, db=DatabaseService(),
                            current_value=current_value, entity_id=entity_id)
    if dlg.exec_() == dlg.Accepted:
        return dlg.get_selected_id()
    return None


def select_form_dialog(parent: QWidget, current_value=None, entity_id=None) -> Optional[str]:
    """TODO: формы отложены до отдельной задачи. Пока no-op."""
    return None


# =========================================================================
# Регистрация
# =========================================================================
def register_builtin_bridges(registry: BridgeFunctionRegistry):
    """Регистрирует все встроенные функции в реестре."""
    # DIRECT
    registry.register("direct_to_qt",   BridgeFunctionKind.TO_RUNTIME,   direct_to_qt)
    registry.register("direct_from_qt", BridgeFunctionKind.FROM_RUNTIME, direct_from_qt)

    # Шрифт
    registry.register("font_to_qt",         BridgeFunctionKind.TO_RUNTIME,   font_to_qt)
    registry.register("font_from_qt",       BridgeFunctionKind.FROM_RUNTIME, font_from_qt)
    registry.register("select_font_dialog", BridgeFunctionKind.SELECT,       select_font_dialog)

    # Цвет
    registry.register("color_to_css",        BridgeFunctionKind.TO_RUNTIME,   color_to_css)
    registry.register("color_from_css",      BridgeFunctionKind.FROM_RUNTIME, color_from_css)
    registry.register("select_color_dialog", BridgeFunctionKind.SELECT,       select_color_dialog)

    # Размер
    registry.register("size_to_qt",         BridgeFunctionKind.TO_RUNTIME,   size_to_qt)
    registry.register("size_from_qt",       BridgeFunctionKind.FROM_RUNTIME, size_from_qt)
    registry.register("select_size_dialog", BridgeFunctionKind.SELECT,       select_size_dialog)

    # Картинка
    registry.register("image_to_qt",         BridgeFunctionKind.TO_RUNTIME,   image_to_qt)
    registry.register("image_from_qt",       BridgeFunctionKind.FROM_RUNTIME, image_from_qt)
    registry.register("select_image_dialog", BridgeFunctionKind.SELECT,       select_image_dialog)

    # Список
    registry.register("items_to_qt",   BridgeFunctionKind.TO_RUNTIME,   items_to_qt)
    registry.register("items_from_qt", BridgeFunctionKind.FROM_RUNTIME, items_from_qt)

    # Метаданные (no-op)
    registry.register("metadata_to_qt",   BridgeFunctionKind.TO_RUNTIME,   metadata_to_qt)
    registry.register("metadata_from_qt", BridgeFunctionKind.FROM_RUNTIME, metadata_from_qt)

    # Выбор сущности / поля / формы
    registry.register("select_entity_dialog", BridgeFunctionKind.SELECT, select_entity_dialog)
    registry.register("select_field_dialog",  BridgeFunctionKind.SELECT, select_field_dialog)
    registry.register("select_form_dialog",   BridgeFunctionKind.SELECT, select_form_dialog)