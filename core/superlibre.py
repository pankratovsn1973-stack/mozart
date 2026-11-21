# -*- coding: utf-8 -*-
# core/superlibre.py
"""
Библиотека SuperLibre — методы трансляции low-code свойств в Qt/Python и обратно,
а также функции выбора значений.

Контракты:
  TO_RUNTIME:   fn(self, widget, collection, cname, value)
  FROM_RUNTIME: fn(self, widget, collection, cname)
  SELECT:       fn(self, widget, collection, cname, current_value=None, db=None)

Ядро не знает специфику свойств. Всё — здесь.
Поддержка BLOB: если prop.is_blob = True, value может быть bytes.
"""
isDebug = 0

import base64
import json
import re
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QColor, QPixmap, QIcon, QImage
from PySide6.QtWidgets import (
    QWidget, QFontDialog, QColorDialog, QFileDialog, QInputDialog, QDialog, QApplication
)

from core.system_fields import get_system_field, is_system_field_id


class SuperLibre:
    # =====================================================================
    # DIRECT (text, number, boolean, choice, json)
    # =====================================================================
    def direct_to_qt(self, widget, collection, cname, value):
        if value is None:
            return
        s = str(value)

        if cname == "text" and hasattr(widget, "setText"):
            widget.setText(s)
            return
        if cname == "checked" and hasattr(widget, "setChecked"):
            widget.setChecked(s.lower() in ("true", "1", "yes", "да"))
            return
        if cname == "title" and hasattr(widget, "setTitle"):
            widget.setTitle(s)
            return

        if s.lower() in ("true", "false"):
            widget.setProperty(cname, s.lower() == "true")
        elif s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            widget.setProperty(cname, int(s))
        else:
            try:
                widget.setProperty(cname, float(s))
            except ValueError:
                widget.setProperty(cname, s)

    def direct_from_qt(self, widget, collection, cname):
        val = widget.property(cname)
        return "" if val is None else str(val)

    # =====================================================================
    # ГЕОМЕТРИЯ
    # =====================================================================
    def geometry_get(self, collection, cname: str, default: int = 0) -> int:
        prop = collection.get(cname) if collection else None
        if prop is None or prop.value == "" or prop.value is None:
            return default
        try:
            return int(float(str(prop.value)))
        except (ValueError, TypeError):
            return default

    def geometry_to_qt(self, widget, collection, cname, value):
        if not value:
            return
        try:
            v = int(float(str(value)))
        except (ValueError, TypeError):
            return

        proxy = widget.graphicsProxyWidget()
        if not proxy:
            return

        parent_item = proxy.parentItem()
        if not parent_item:
            return

        if cname == "myx":
            parent_item.setPos(v, parent_item.pos().y())
        elif cname == "myy":
            parent_item.setPos(parent_item.pos().x(), v)
        elif cname == "mywidth":
            widget.resize(max(1, v), widget.height())
            proxy.resize(widget.size())
        elif cname == "myheight":
            widget.resize(widget.width(), max(1, v))
            proxy.resize(widget.size())
        else:
            return

        proxy.update()
        if proxy.scene():
            proxy.scene().update()
        if hasattr(parent_item, 'refresh_from_widget'):
            parent_item.blockSignals(True)
            parent_item.refresh_from_widget()
            parent_item.blockSignals(False)



    def geometry_from_qt(self, widget, collection, cname,
                         prop_id_col=None, element_id_col=None):
        """
        Читает геометрию с холста Mozart.

        v9 FIX (STRICT IDCOL):
        Раньше метод искал графику через QApplication.topLevelWidgets() +
        goProject.current_element_id. Это нарушало контракт idCol, ломалось
        при нескольких открытых окнах конфигуратора и когда current_element_id
        был не установлен. Теперь поиск идёт напрямую через
        CollectionManager.get_graphic_item(element_id_col).

        Контракт вызова (после v7.2):
          fn(self, widget, collection, cname,
             prop_id_col=None, element_id_col=None)
        BridgeResolver._safe_call фильтрует kwargs по сигнатуре, поэтому
        старые вызовы без element_id_col не падают — просто уходят в fallback.

        Приоритет источников:
        1. Графический элемент сцены по element_id_col → pos()/rect();
        2. Fallback на widget.x()/y()/width()/height() (фаза загрузки,
           когда прокси-виджет ещё не добавлен на сцену).
        """
        # --- Приоритет 1: графический элемент по idCol -------------------
        if element_id_col is not None and collection is not None:
            mgr = getattr(collection, '_collection_manager', None)
            if mgr is not None:
                item = mgr.get_graphic_item(element_id_col)
                if item is not None:
                    if cname == "myx":
                        return str(int(item.pos().x()))
                    if cname == "myy":
                        return str(int(item.pos().y()))
                    if cname == "mywidth":
                        rect = item.rect() if hasattr(item, 'rect') else None
                        w = int(rect.width() - 4) if rect else widget.width()
                        return str(max(1, w))
                    if cname == "myheight":
                        rect = item.rect() if hasattr(item, 'rect') else None
                        h = int(rect.height() - 4) if rect else widget.height()
                        return str(max(1, h))

        # --- Fallback: виджет (фаза загрузки / нет сцены) ----------------
        if cname == "myx":
            return str(int(widget.x()))
        if cname == "myy":
            return str(int(widget.y()))
        if cname == "mywidth":
            return str(int(widget.width()))
        if cname == "myheight":
            return str(int(widget.height()))

        return ""

    def select_geometry_dialog(self, widget, collection, cname, current_value=None,
                               prop_id_col=None, element_id_col=None):
        text, ok = QInputDialog.getText(
            widget, "Геометрия",
            "Формат: Ш;В или X;Y;Ш;В",
            text=str(current_value or "")
        )
        return text.strip() if ok else None

    # =====================================================================
    # Шрифт
    # =====================================================================
    def font_to_qt(self, widget, collection, cname, value):
        if not value:
            return
        if str(value).count(",") == 1:
            family, size_str = str(value).split(",", 1)
            try:
                size = int(size_str.strip())
            except ValueError:
                size = 11
            if size <= 0: size = 11
            f = QFont(family.strip(), size)
        else:
            f = QFont()
            f.fromString(str(value))

        widget.setFont(f)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.ensurePolished()
        widget.update()
        if widget.graphicsProxyWidget():
            widget.graphicsProxyWidget().update()

    def font_from_qt(self, widget, collection, cname):
        f = widget.font()
        size = f.pointSize() if f.pointSize() > 0 else f.pixelSize()
        if size <= 0: size = 11
        return f"{f.family()},{size}"

    def select_font_dialog(self, widget, collection, cname, current_value=None,
                           prop_id_col=None, element_id_col=None):
        initial = QFont()
        if current_value:
            try:
                if str(current_value).count(",") == 1:
                    family, size_str = str(current_value).split(",", 1)
                    initial = QFont(family.strip(), int(size_str.strip()))
                else:
                    initial.fromString(str(current_value))
            except (ValueError, TypeError):
                pass

        result = QFontDialog.getFont(initial, widget)
        font, ok = None, False
        for item in result or ():
            if isinstance(item, QFont):
                font = item
            elif isinstance(item, bool):
                ok = item

        if not ok or font is None: return None

        size = font.pointSize() if font.pointSize() > 0 else font.pixelSize()
        if size <= 0: size = 11
        return f"{font.family()},{size}"

    # =====================================================================
    # ЦВЕТ (CSS)
    # =====================================================================

    # core/superlibre.py

    # core/superlibre.py

    # ... (весь код выше без изменений) ...

    # =====================================================================
    # ЦВЕТ (CSS) — С ОТЛАДКОЙ
    # =====================================================================
    def color_to_backcss(self, widget, collection, cname, value):
        """Устанавливает или удаляет background-color через styleSheet."""
        obj_name = getattr(widget, 'objectName', '?')
        if callable(obj_name):
            obj_name = obj_name() or '?'

        print(f"[DEBUG SL] >>> color_to_backcss | Widget: {obj_name} | CName: {cname}")
        print(f"[DEBUG SL]     Value received: '{value}' (type: {type(value).__name__})")

        current_css = widget.styleSheet() or ""
        print(f"[DEBUG SL]     Current CSS length: {len(current_css)} chars")

        # Сценарий удаления: если значение пустое
        if not value:
            print(f"[DEBUG SL]     ⚠️ DELETE SCENARIO: Empty value detected. Removing rule.")
            new_css = re.sub(r'(background-color\s*:\s*[^;]+;)', '', current_css, flags=re.IGNORECASE).strip()
            new_css = re.sub(r';\s*;', ';', new_css).strip().rstrip(';')

            if new_css != current_css:
                print(f"[DEBUG SL]     ✅ CSS Updated. New length: {len(new_css)} chars")
                widget.setStyleSheet(new_css)
                widget.update()
                proxy = widget.graphicsProxyWidget()
                if proxy:
                    proxy.update()
            else:
                print(f"[DEBUG SL]     ℹ️ No changes needed. Rule not found in CSS.")
            return

        # Сценарий установки
        new_color = str(value).strip()
        pattern = r'(background-color\s*:\s*)([^;]+)(;)'

        if re.search(pattern, current_css, re.IGNORECASE):
            print(f"[DEBUG SL]     🔄 Updating existing background-color to: {new_color}")
            new_css = re.sub(pattern, rf'\1{new_color}\3', current_css, flags=re.IGNORECASE)
        else:
            sep = "; " if current_css and not current_css.endswith(";") else ""
            new_css = f"{current_css}{sep}background-color: {new_color};"
            print(f"[DEBUG SL]     ➕ Appending new background-color: {new_color}")

        if new_css != current_css:
            widget.setStyleSheet(new_css)
            widget.update()
            proxy = widget.graphicsProxyWidget()
            if proxy:
                proxy.update()
            print(f"[DEBUG SL]     ✅ Applied successfully.")
        else:
            print(f"[DEBUG SL]     ℹ️ Color already set correctly.")


    def color_to_textcss(self, widget, collection, cname, value):
        """Устанавливает или удаляет color (текст) через styleSheet."""
        obj_name = getattr(widget, 'objectName', '?')
        if callable(obj_name):
            obj_name = obj_name() or '?'

        print(f"[DEBUG SL] >>> color_to_textcss | Widget: {obj_name} | CName: {cname}")
        print(f"[DEBUG SL]     Value received: '{value}' (type: {type(value).__name__})")

        saved_w = widget.width()
        saved_h = widget.height()
        current_css = widget.styleSheet() or ""

        # Сценарий удаления
        if not value:
            print(f"[DEBUG SL]     ⚠️ DELETE SCENARIO: Empty value detected. Removing rule.")
            new_css = re.sub(r'(?<!-)(color\s*:\s*[^;]+;)', '', current_css, flags=re.IGNORECASE).strip()
            new_css = re.sub(r';\s*;', ';', new_css).strip().rstrip(';')

            if new_css != current_css:
                print(f"[DEBUG SL]     ✅ Text color removed from CSS.")
                widget.setStyleSheet(new_css)
                widget.update()
                proxy = widget.graphicsProxyWidget()
                if proxy:
                    proxy.update()
            else:
                print(f"[DEBUG SL]     ℹ️ Text color rule not found in CSS.")
            return

        # Сценарий установки
        new_color = str(value).strip()
        pattern = r'(?<!-)(color\s*:\s*)([^;]+)(;)'

        if re.search(pattern, current_css, re.IGNORECASE):
            print(f"[DEBUG SL]      Updating existing text color to: {new_color}")
            new_css = re.sub(pattern, rf'\1{new_color}\3', current_css, flags=re.IGNORECASE)
        else:
            sep = "; " if current_css and not current_css.endswith(";") else ""
            new_css = f"{current_css}{sep}color: {new_color};"
            print(f"[DEBUG SL]     ➕ Appending new text color: {new_color}")

        if new_css != current_css:
            widget.setStyleSheet(new_css)
            actual_w = widget.width()
            actual_h = widget.height()
            if actual_w != saved_w and collection:
                w_prop = collection.get('mywidth')
                if w_prop:
                    collection.set_value('mywidth', str(actual_w), source='auto_sync')
            if actual_h != saved_h and collection:
                h_prop = collection.get('myheight')
                if h_prop:
                    collection.set_value('myheight', str(actual_h), source='auto_sync')

            widget.update()
            proxy = widget.graphicsProxyWidget()
            if proxy:
                proxy.update()
            print(f"[DEBUG SL]     ✅ Applied successfully.")
        else:
            print(f"[DEBUG SL]     ️ Text color already set correctly.")



    def color_to_bordercss(self, widget, collection, cname, value):
        """Устанавливает или удаляет border-color через styleSheet."""
        obj_name = getattr(widget, 'objectName', '?')
        if callable(obj_name):
            obj_name = obj_name() or '?'

        print(f"[DEBUG SL] >>> color_to_bordercss | Widget: {obj_name} | CName: {cname}")
        print(f"[DEBUG SL]     Value received: '{value}' (type: {type(value).__name__})")

        current_css = widget.styleSheet() or ""

        # Сценарий удаления
        if not value:
            print(f"[DEBUG SL]     ⚠️ DELETE SCENARIO: Empty value detected. Removing rule.")
            new_css = re.sub(r'(border-color\s*:\s*[^;]+;)', '', current_css, flags=re.IGNORECASE).strip()
            new_css = re.sub(r';\s*;', ';', new_css).strip().rstrip(';')

            if new_css != current_css:
                print(f"[DEBUG SL]     ✅ Border color removed from CSS.")
                widget.setStyleSheet(new_css)
                widget.update()
                proxy = widget.graphicsProxyWidget()
                if proxy:
                    proxy.update()
            else:
                print(f"[DEBUG SL]     ℹ️ Border color rule not found in CSS.")
            return

        # Сценарий установки
        new_color = str(value).strip()
        pattern = r'(border-color\s*:\s*)([^;]+)(;)'

        if re.search(pattern, current_css, re.IGNORECASE):
            print(f"[DEBUG SL]     🔄 Updating existing border color to: {new_color}")
            new_css = re.sub(pattern, rf'\1{new_color}\3', current_css, flags=re.IGNORECASE)
        else:
            sep = "; " if current_css and not current_css.endswith(";") else ""
            new_css = f"{current_css}{sep}border-color: {new_color};"
            print(f"[DEBUG SL]     ➕ Appending new border color: {new_color}")

        if new_css != current_css:
            widget.setStyleSheet(new_css)
            widget.update()
            proxy = widget.graphicsProxyWidget()
            if proxy:
                proxy.update()
            print(f"[DEBUG SL]     ✅ Applied successfully.")
        else:
            print(f"[DEBUG SL]     ℹ️ Border color already set correctly.")
    # ... (остальной код файла без изменений) ...





    def color_from_backcss(self, widget, collection, cname):
        css = widget.styleSheet() or ""
        m = re.search(r'background-color\s*:\s*([^;]+);', css, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def color_from_textcss(self, widget, collection, cname):
        css = widget.styleSheet() or ""
        m = re.search(r'(?<!-)(color\s*:\s*)([^;]+);', css, re.IGNORECASE)
        return m.group(2).strip() if m else ""


    def color_from_bordercss(self, widget, collection, cname):
        css = widget.styleSheet() or ""
        m = re.search(r'border-color\s*:\s*([^;]+);', css, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def select_color_dialog(self, widget, collection, cname, current_value=None,
                            prop_id_col=None, element_id_col=None):
        initial = QColor(current_value) if current_value else QColor(Qt.white)
        parent_window = widget.window() if widget else None
        if cname == "c_text_color":
            title = "Выбор цвета текста"
        elif cname == "c_border_color":
            title = "Выбор цвета рамки"
        elif cname == "c_back_color":
            title = "Выбор цвета фона"
        else:
            title = "Выбор цвета"
        color = QColorDialog.getColor(initial, parent_window, title)
        return color.name() if color.isValid() else None

    # =====================================================================
    # Размер (QSize)
    # =====================================================================
    def size_to_qt(self, widget, collection, cname, value):
        if not value: return
        nums = [int(n) for n in re.findall(r"-?\d+", str(value))]
        if len(nums) >= 2:
            widget.setProperty(cname, QSize(nums[0], nums[1]))
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def size_from_qt(self, widget, collection, cname):
        size = widget.property(cname)
        if isinstance(size, QSize):
            return f"{size.width()};{size.height()}"
        return ""

    def select_size_dialog(self, widget, collection, cname, current_value=None,
                           prop_id_col=None, element_id_col=None):
        text, ok = QInputDialog.getText(
            widget, "Размер",
            "Ширина;Высота (например 100;30):",
            text=str(current_value or "")
        )
        return text.strip() if ok else None

    # =====================================================================
    # КАРТИНКА + BLOB
    # =====================================================================
    def image_to_qt(self, widget, collection, cname, value):
        """
        Если prop.is_blob = True и blob_value не None → рисуем из bytes.
        Иначе — из пути (str).
        """
        # Проверяем, это блоб?
        prop = collection.get(cname) if collection else None
        if prop is not None and getattr(prop, 'is_blob', False) and prop.blob_value:
            try:
                image = QImage.fromData(bytes(prop.blob_value))
                if not image.isNull():
                    if cname == "pixmap" and hasattr(widget, "setPixmap"):
                        widget.setPixmap(QPixmap.fromImage(image))
                        return
                    elif cname == "icon" and hasattr(widget, "setIcon"):
                        widget.setIcon(QIcon(QPixmap.fromImage(image)))
                        return
                    elif cname == "c_background_image":
                        # Для фонового изображения — сохраняем во временный файл и ставим url
                        # (или пропускаем — если не критично)
                        pass
            except Exception as e:
                if isDebug:
                    print(f"[SuperLibre] Ошибка декодирования BLOB для {cname}: {e}")

        # Fallback: путь
        if not value: return
        if cname == "pixmap" and hasattr(widget, "setPixmap"):
            widget.setPixmap(QPixmap(value))
        elif cname == "icon" and hasattr(widget, "setIcon"):
            widget.setIcon(QIcon(value))
        elif cname == "c_background_image":
            css = widget.styleSheet() or ""
            pattern = r"background-image\s*:\s*[^;]+;"
            replacement = f"background-image: url({value});"
            if re.search(pattern, css):
                css = re.sub(pattern, replacement, css)
            else:
                css = css + (" " if css else "") + replacement
            widget.setStyleSheet(css)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def image_from_qt(self, widget, collection, cname):
        prop = collection.get(cname) if collection else None
        if prop is not None and getattr(prop, 'is_blob', False):
            return f"[BLOB:{prop.blob_name or ''}]"
        if cname == "c_background_image":
            css = widget.styleSheet() or ""
            m = re.search(r"background-image\s*:\s*url\(([^)]+)\);", css)
            return m.group(1).strip() if m else ""
        return ""

    def select_image_dialog(self, widget, collection, cname, current_value=None,
                            prop_id_col=None, element_id_col=None):
        """
        Открывает файл, читает в bytes, сохраняет в prop.blob_value (is_blob=True).
        Возвращает имя файла (для отображения в c_value).
        """
        path, _ = QFileDialog.getOpenFileName(
            widget, "Выбор изображения",
            str(current_value or ""),
            "Images (*.png *.jpg *.jpeg *.bmp *.svg);;All files (*)"
        )
        if not path:
            return None

        # Читаем файл в bytes
        try:
            with open(path, "rb") as f:
                blob_data = f.read()
        except Exception as e:
            if isDebug:
                print(f"[SuperLibre] Ошибка чтения файла {path}: {e}")
            return path  # fallback — хотя бы путь

        # Сохраняем в prop.blob_value
        if collection is not None:
            import os
            blob_name = os.path.basename(path)
            collection.set_blob(cname, blob_data, blob_name)
            return blob_name  # отображаемое значение

        return path

    # =====================================================================
    # Список (QComboBox / QListWidget)
    # =====================================================================
    def items_to_qt(self, widget, collection, cname, value):
        if not value: return
        try:
            items = json.loads(value)
        except json.JSONDecodeError:
            return
        if not isinstance(items, list): return

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

    def items_from_qt(self, widget, collection, cname):
        items = []
        if hasattr(widget, "count") and hasattr(widget, "itemText"):
            for i in range(widget.count()):
                text = widget.itemText(i)
                data = widget.itemData(i) if hasattr(widget, "itemData") else text
                items.append({"value": data if data is not None else text, "display": text})
        return json.dumps(items, ensure_ascii=False)

    # =====================================================================
    # МЕТАДАННЫЕ
    # =====================================================================
    def metadata_to_qt(self, widget, collection, cname, value):
        if widget is None or value is None:
            return
        str_val = str(value).strip()
        try:
            if str_val.isdigit() or (str_val.startswith('-') and str_val[1:].isdigit()):
                val = int(str_val)
            else:
                val = str_val
            widget.setProperty(cname, val)
        except Exception as e:
            if isDebug:
                print(f"[SuperLibre] Ошибка записи метаданных '{cname}': {e}")

    def metadata_from_qt(self, widget, collection, cname):
        if widget is None:
            return ""
        val = widget.property(cname)
        return str(val).strip() if val is not None else ""

    def entity_id_to_name(self, widget, collection, cname):
        if not collection:
            return ""
        prop = collection.get(cname)
        if not prop or not prop.value:
            return ""
        try:
            eid = int(str(prop.value).strip())
        except (ValueError, TypeError):
            return str(prop.value).strip()

        from ide_core import goProject
        db_service = getattr(goProject.property_bridge_manager, 'db', None)
        if db_service is None:
            return f"[ID:{eid}]"

        sql = "SELECT cname FROM meta.entitytypes WHERE id = %s"
        try:
            res = db_service.execute_query(sql, (eid,))
            if res and len(res) > 0 and res[0][0]:
                return str(res[0][0])
        except Exception as e:
            if isDebug:
                print(f"[SuperLibre] SQL Error in entity_id_to_name: {e}")
        return f"[ID:{eid}]"

    def field_id_to_name(self, widget, collection, cname):
        if not collection:
            return ""
        prop = collection.get(cname)
        if not prop or not prop.value:
            return ""
        try:
            fid = int(str(prop.value).strip())
        except (ValueError, TypeError):
            return str(prop.value).strip()

        if is_system_field_id(fid):
            info = get_system_field(fid)
            if info:
                return info['calias'] or info['cname']
            return f"[Field ID:{fid}]"

        from ide_core import goProject
        db_service = getattr(goProject.property_bridge_manager, 'db', None)
        if db_service is None:
            return f"[Field ID:{fid}]"

        sql = "SELECT calias FROM meta.fields WHERE id = %s"
        try:
            res = db_service.execute_query(sql, (fid,))
            if res and len(res) > 0 and res[0][0]:
                return str(res[0][0])
        except Exception as e:
            if isDebug:
                print(f"[SuperLibre] SQL Error in field_id_to_name: {e}")
        return f"[Field ID:{fid}]"

    # =====================================================================
    # ДИАЛОГИ ВЫБОРА
    # =====================================================================
    def select_entity_dialog(self, widget, collection, cname, current_value=None, db=None,
                             prop_id_col=None, element_id_col=None):
        from dialogs.select_entity_dialog import SelectEntityDialog
        if db is None:
            if isDebug:
                print("[SuperLibre] ОШИБКА: db=None в select_entity_dialog!")
            return None

        dlg = SelectEntityDialog(parent=None, db=db, current_value=current_value)
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        dlg.setWindowModality(Qt.ApplicationModal)

        main_win = QApplication.activeWindow()
        if main_win:
            geo = main_win.geometry()
            x = geo.x() + (geo.width() - dlg.width()) // 2
            y = geo.y() + (geo.height() - dlg.height()) // 2
            dlg.move(x, y)

        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_selected_id()
        return None

    def select_field_dialog(self, widget, collection, cname, current_value=None, db=None,
                            prop_id_col=None, element_id_col=None):
        from dialogs.select_field_dialog import SelectFieldDialog

        entity_id = None
        if collection:
            binding = collection.get('binding_entity')
            if binding and binding.value:
                try:
                    entity_id = int(binding.value)
                except:
                    pass

        if db is None:
            if isDebug:
                print("[SuperLibre] ОШИБКА: db=None в select_field_dialog!")
            return None

        dlg = SelectFieldDialog(
            parent=None, db=db, current_value=current_value, entity_id=entity_id
        )
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        dlg.setWindowModality(Qt.ApplicationModal)

        main_win = QApplication.activeWindow()
        if main_win:
            geo = main_win.geometry()
            dlg.move(
                geo.x() + (geo.width() - dlg.width()) // 2,
                geo.y() + (geo.height() - dlg.height()) // 2
            )

        if dlg.exec_() == QDialog.Accepted:
            return dlg.get_selected_id()
        return None

    def select_form_dialog(self, widget, collection, cname, current_value=None, db=None,
                           prop_id_col=None, element_id_col=None):
        """Заглушка для выбора формы."""
        return None