# /home/sergey/Documents/configurate/utils/json_to_ui.py
# -*- coding: utf-8 -*-
# Утилита для конвертации JSON обратно в .ui файл

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Optional


class JSONtoUIConverter:
    """
    Конвертирует JSON-структуру формы обратно в .ui файл.
    Используется для редактирования существующих форм.
    Поддерживает пустые/битые данные — всегда создаёт валидный .ui файл.
    """

    def __init__(self):
        self.namespaces = {
            'ui': 'http://schemas.qt.io/qt/designer/ui/5.0'
        }

    def convert(self, json_data: Optional[Dict[str, Any]] = None, json_file_path: str = None,
                output_file_path: str = None) -> str:
        """
        Конвертирует JSON в .ui файл.

        Args:
            json_data: JSON-структура формы (опционально)
            json_file_path: путь к JSON файлу (опционально)
            output_file_path: путь для сохранения .ui файла (опционально)

        Returns:
            XML-строка .ui файла
        """
        # Загружаем данные
        if json_file_path:
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            except:
                json_data = None

        # Если данные не загрузились, создаём пустую форму
        if not json_data:
            json_data = self._get_empty_form()

        # Создаём корневой элемент
        root = ET.Element('ui', {
            'version': '5.0'
        })

        # Добавляем класс формы
        class_elem = ET.SubElement(root, 'class')
        class_elem.text = json_data.get('class', 'MozartForm')

        # Добавляем имя объекта
        object_name_elem = ET.SubElement(root, 'objectName')
        object_name_elem.text = json_data.get('objectName', 'Form')

        # Добавляем заголовок окна
        window_title_elem = ET.SubElement(root, 'windowTitle')
        window_title_elem.text = json_data.get('windowTitle', 'Новая форма')

        # Добавляем геометрию
        self._add_geometry(root, json_data.get('geometry', {}))

        # Добавляем свойства
        self._add_properties(root, json_data.get('custom_properties', {}))

        # Добавляем виджеты
        widgets_elem = ET.SubElement(root, 'widget', {
            'class': json_data.get('class', 'MozartForm'),
            'name': json_data.get('objectName', 'Form')
        })
        for widget_data in json_data.get('widgets', []):
            self._add_widget(widgets_elem, widget_data)

        # Добавляем связи
        self._add_connections(root, json_data.get('connections', []))

        # Форматируем XML
        xml_str = self._prettify_xml(root)

        # Сохраняем в файл
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            print(f"Конвертация завершена: {output_file_path}")

        return xml_str

    def _get_empty_form(self) -> Dict[str, Any]:
        """Возвращает структуру пустой формы"""
        return {
            "class": "MozartForm",
            "objectName": "Form",
            "windowTitle": "Новая форма",
            "geometry": {"x": 0, "y": 0, "width": 800, "height": 600},
            "widgets": [],
            "connections": [],
            "custom_properties": {}
        }

    def _add_geometry(self, parent, geometry: Dict[str, int]):
        """Добавляет геометрию в элемент"""
        rect = ET.SubElement(parent, 'rect')

        x = ET.SubElement(rect, 'x')
        x.text = str(geometry.get('x', 0))

        y = ET.SubElement(rect, 'y')
        y.text = str(geometry.get('y', 0))

        width = ET.SubElement(rect, 'width')
        width.text = str(geometry.get('width', 800))

        height = ET.SubElement(rect, 'height')
        height.text = str(geometry.get('height', 600))

    def _add_properties(self, parent, properties: Dict[str, Any]):
        """Добавляет свойства в элемент"""
        for name, value in properties.items():
            prop = ET.SubElement(parent, 'property', {'name': name})

            if isinstance(value, bool):
                bool_elem = ET.SubElement(prop, 'bool')
                bool_elem.text = 'true' if value else 'false'
            elif isinstance(value, int):
                number_elem = ET.SubElement(prop, 'number')
                number_elem.text = str(value)
            else:
                string_elem = ET.SubElement(prop, 'string')
                string_elem.text = str(value)

    def _add_widget(self, parent, widget_data: Dict[str, Any]):
        """Добавляет виджет в дерево"""
        widget_class = widget_data.get('class', 'QWidget')
        widget_name = widget_data.get('name', '')

        if not widget_name:
            return

        widget = ET.SubElement(parent, 'widget', {'class': widget_class, 'name': widget_name})

        # Добавляем геометрию
        self._add_geometry(widget, widget_data.get('geometry', {}))

        # Добавляем свойства
        self._add_properties(widget, widget_data.get('properties', {}))

        # Добавляем кастомные свойства
        for name, value in widget_data.get('custom_properties', {}).items():
            self._add_properties(widget, {name: value})

        # Добавляем дочерние виджеты
        for child in widget_data.get('children', []):
            self._add_widget(widget, child)

    def _add_connections(self, parent, connections: list):
        """Добавляет связи сигнал-слот"""
        if not connections:
            return

        conns_elem = ET.SubElement(parent, 'connections')
        for conn_data in connections:
            conn = ET.SubElement(conns_elem, 'connection')

            sender = ET.SubElement(conn, 'sender')
            sender.text = conn_data.get('sender', '')

            signal = ET.SubElement(conn, 'signal')
            signal.text = conn_data.get('signal', '')

            receiver = ET.SubElement(conn, 'receiver')
            receiver.text = conn_data.get('receiver', '')

            slot = ET.SubElement(conn, 'slot')
            slot.text = conn_data.get('slot', '')

    def _prettify_xml(self, element) -> str:
        """Форматирует XML с отступами"""
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent='  ')


def json_to_ui(json_file_path: str = None, json_data: Dict = None, output_ui_path: str = None) -> str:
    """
    Утилитарная функция для конвертации JSON в .ui файл.

    Args:
        json_file_path: путь к JSON файлу (опционально)
        json_data: JSON-структура (опционально)
        output_ui_path: путь для сохранения .ui файла (опционально)

    Returns:
        XML-строка .ui файла
    """
    converter = JSONtoUIConverter()

    if json_file_path:
        return converter.convert(json_file_path=json_file_path, output_file_path=output_ui_path)
    else:
        return converter.convert(json_data=json_data, output_file_path=output_ui_path)


def create_empty_ui(output_ui_path: str = None) -> str:
    """
    Создаёт пустой .ui файл для новой формы.

    Args:
        output_ui_path: путь для сохранения .ui файла

    Returns:
        XML-строка пустого .ui файла
    """
    converter = JSONtoUIConverter()
    empty_form = converter._get_empty_form()
    return converter.convert(json_data=empty_form, output_file_path=output_ui_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        ui_file = sys.argv[2] if len(sys.argv) > 2 else json_file.replace('.json', '.ui')
        json_to_ui(json_file, output_ui_path=ui_file)
    else:
        # Создаём пустой .ui файл для примера
        create_empty_ui("empty_form.ui")