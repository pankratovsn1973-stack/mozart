# /home/sergey/Documents/configurate/utils/ui_to_json.py
# -*- coding: utf-8 -*-
# Утилита для конвертации .ui файлов в JSON для хранения в meta.forms

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional


class UItoJSONConverter:
    """
    Конвертирует .ui файл (XML) в JSON-структуру для хранения в meta.forms.
    Сохраняет геометрию, свойства виджетов, связи событий.
    Поддерживает пустые/битые файлы — всегда возвращает валидный JSON.
    """

    def __init__(self):
        self.namespaces = {'ui': 'http://schemas.qt.io/qt/designer/ui/5.0'}

    def convert(self, ui_file_path: Optional[str] = None, xml_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Конвертирует .ui файл или XML-строку в JSON.

        Args:
            ui_file_path: путь к .ui файлу (опционально)
            xml_content: XML-строка (опционально)

        Returns:
            JSON-структура формы (всегда валидная)
        """
        # Базовый пустой результат
        result = self._get_empty_result()

        try:
            if ui_file_path:
                tree = ET.parse(ui_file_path)
            elif xml_content:
                tree = ET.ElementTree(ET.fromstring(xml_content))
            else:
                return result

            root = tree.getroot()

            result["class"] = self._get_text(root, 'class', 'MozartForm')
            result["objectName"] = self._get_text(root, 'objectName', 'Form')
            result["windowTitle"] = self._get_text(root, 'windowTitle', 'Новая форма')
            result["geometry"] = self._get_geometry(root)
            result["widgets"] = self._get_widgets(root)
            result["connections"] = self._get_connections(root)
            result["custom_properties"] = self._get_custom_properties(root)

        except Exception as e:
            print(f"Ошибка при конвертации: {e}. Возвращена пустая форма.")

        return result

    def _get_empty_result(self) -> Dict[str, Any]:
        """Возвращает пустую валидную структуру формы"""
        return {
            "class": "MozartForm",
            "objectName": "Form",
            "windowTitle": "Новая форма",
            "geometry": {"x": 0, "y": 0, "width": 800, "height": 600},
            "widgets": [],
            "connections": [],
            "custom_properties": {}
        }

    def _get_text(self, element, tag, default=''):
        """Возвращает текст дочернего элемента"""
        child = element.find(f'.//ui:{tag}', self.namespaces)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def _get_geometry(self, root) -> Dict[str, int]:
        """Извлекает геометрию формы"""
        try:
            geometry = root.find('.//ui:geometry', self.namespaces)
            if geometry is None:
                return {"x": 0, "y": 0, "width": 800, "height": 600}

            x = geometry.find('.//ui:x', self.namespaces)
            y = geometry.find('.//ui:y', self.namespaces)
            width = geometry.find('.//ui:width', self.namespaces)
            height = geometry.find('.//ui:height', self.namespaces)

            return {
                "x": int(x.text) if x is not None and x.text else 0,
                "y": int(y.text) if y is not None and y.text else 0,
                "width": int(width.text) if width is not None and width.text else 800,
                "height": int(height.text) if height is not None and height.text else 600
            }
        except:
            return {"x": 0, "y": 0, "width": 800, "height": 600}

    def _get_widgets(self, root) -> List[Dict[str, Any]]:
        """Извлекает все виджеты формы"""
        widgets = []
        try:
            items = root.findall('.//ui:widget', self.namespaces)
            for item in items:
                widget = self._parse_widget(item)
                if widget:
                    widgets.append(widget)
        except:
            pass
        return widgets

    def _parse_widget(self, widget_elem) -> Optional[Dict[str, Any]]:
        """Парсит отдельный виджет"""
        try:
            class_name = self._get_text(widget_elem, 'class', 'QWidget')
            name = self._get_text(widget_elem, 'objectName', '')

            if not name:
                return None

            result = {
                "class": class_name,
                "name": name,
                "geometry": self._get_widget_geometry(widget_elem),
                "properties": self._get_widget_properties(widget_elem),
                "custom_properties": self._get_widget_custom_properties(widget_elem)
            }

            # Рекурсивно обрабатываем дочерние виджеты
            children = widget_elem.findall('.//ui:widget', self.namespaces)
            if children:
                result["children"] = [self._parse_widget(child) for child in children if
                                      self._get_text(child, 'objectName', '')]

            return result
        except:
            return None

    def _get_widget_geometry(self, widget_elem) -> Dict[str, int]:
        """Извлекает геометрию виджета"""
        try:
            rect = widget_elem.find('.//ui:rect', self.namespaces)
            if rect is None:
                return {"x": 0, "y": 0, "width": 100, "height": 30}

            x = rect.find('.//ui:x', self.namespaces)
            y = rect.find('.//ui:y', self.namespaces)
            width = rect.find('.//ui:width', self.namespaces)
            height = rect.find('.//ui:height', self.namespaces)

            return {
                "x": int(x.text) if x is not None and x.text else 0,
                "y": int(y.text) if y is not None and y.text else 0,
                "width": int(width.text) if width is not None and width.text else 100,
                "height": int(height.text) if height is not None and height.text else 30
            }
        except:
            return {"x": 0, "y": 0, "width": 100, "height": 30}

    def _get_widget_properties(self, widget_elem) -> Dict[str, Any]:
        """Извлекает стандартные свойства виджета"""
        properties = {}
        try:
            props = widget_elem.findall('.//ui:property', self.namespaces)
            for prop in props:
                name = prop.get('name')
                if name in ('geometry', 'objectName'):
                    continue

                value_elem = prop.find('.//ui:string', self.namespaces)
                if value_elem is not None and value_elem.text:
                    properties[name] = value_elem.text
                    continue

                bool_elem = prop.find('.//ui:bool', self.namespaces)
                if bool_elem is not None and bool_elem.text:
                    properties[name] = bool_elem.text.lower() == 'true'
                    continue

                number_elem = prop.find('.//ui:number', self.namespaces)
                if number_elem is not None and number_elem.text:
                    properties[name] = int(number_elem.text)
                    continue
        except:
            pass
        return properties

    def _get_widget_custom_properties(self, widget_elem) -> Dict[str, Any]:
        """Извлекает кастомные свойства виджета"""
        custom_properties = {}
        try:
            props = widget_elem.findall('.//ui:property', self.namespaces)
            for prop in props:
                name = prop.get('name')
                if name in ('geometry', 'objectName', 'text', 'windowTitle', 'enabled', 'visible'):
                    continue

                string_val = prop.find('.//ui:string', self.namespaces)
                if string_val is not None and string_val.text:
                    custom_properties[name] = string_val.text
                    continue

                bool_val = prop.find('.//ui:bool', self.namespaces)
                if bool_val is not None and bool_val.text:
                    custom_properties[name] = bool_val.text.lower() == 'true'
                    continue

                number_val = prop.find('.//ui:number', self.namespaces)
                if number_val is not None and number_val.text:
                    custom_properties[name] = int(number_val.text)
                    continue
        except:
            pass
        return custom_properties

    def _get_connections(self, root) -> List[Dict[str, str]]:
        """Извлекает связи сигнал-слот"""
        connections = []
        try:
            conns = root.findall('.//ui:connection', self.namespaces)
            for conn in conns:
                sender = conn.find('.//ui:sender', self.namespaces)
                signal = conn.find('.//ui:signal', self.namespaces)
                receiver = conn.find('.//ui:receiver', self.namespaces)
                slot = conn.find('.//ui:slot', self.namespaces)

                if sender is not None and signal is not None:
                    connections.append({
                        "sender": sender.text.strip() if sender.text else "",
                        "signal": signal.text.strip() if signal.text else "",
                        "receiver": receiver.text.strip() if receiver and receiver.text else "",
                        "slot": slot.text.strip() if slot and slot.text else ""
                    })
        except:
            pass
        return connections

    def _get_custom_properties(self, root) -> Dict[str, Any]:
        """Извлекает кастомные свойства формы"""
        custom = {}
        try:
            props = root.findall('.//ui:property', self.namespaces)
            for prop in props:
                name = prop.get('name')
                if name in ('geometry', 'objectName', 'windowTitle', 'enabled', 'visible'):
                    continue

                string_val = prop.find('.//ui:string', self.namespaces)
                if string_val is not None and string_val.text:
                    custom[name] = string_val.text
                    continue

                bool_val = prop.find('.//ui:bool', self.namespaces)
                if bool_val is not None and bool_val.text:
                    custom[name] = bool_val.text.lower() == 'true'
                    continue

                number_val = prop.find('.//ui:number', self.namespaces)
                if number_val is not None and number_val.text:
                    custom[name] = int(number_val.text)
                    continue
        except:
            pass
        return custom


def convert_ui_to_json(ui_file_path: str = None, xml_content: str = None, output_file_path: str = None) -> Dict[
    str, Any]:
    """
    Утилитарная функция для конвертации .ui файла или XML в JSON.

    Args:
        ui_file_path: путь к .ui файлу (опционально)
        xml_content: XML-строка (опционально)
        output_file_path: путь для сохранения JSON (опционально)

    Returns:
        JSON-структура формы (всегда валидная)
    """
    converter = UItoJSONConverter()
    result = converter.convert(ui_file_path, xml_content)

    if output_file_path:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Конвертация завершена: {output_file_path}")

    return result


def create_empty_form_json(output_file_path: str = None) -> Dict[str, Any]:
    """
    Создаёт JSON для пустой формы.

    Args:
        output_file_path: путь для сохранения JSON (опционально)

    Returns:
        JSON-структура пустой формы
    """
    converter = UItoJSONConverter()
    result = converter._get_empty_result()

    if output_file_path:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Пустая форма создана: {output_file_path}")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        ui_file = sys.argv[1]
        json_file = sys.argv[2] if len(sys.argv) > 2 else ui_file.replace('.ui', '.json')
        convert_ui_to_json(ui_file, output_file_path=json_file)
    else:
        # Создаём пустую форму для примера
        create_empty_form_json("empty_form.json")