# /home/sergey/Documents/configurate/tabs/forms/form_designer_launcher.py
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import QObject, Signal, QTimer

from lang.local_translator import LocalTranslator


class FormDesignerLauncher(QObject):
    """Запуск Qt Designer с файловой синхронизацией"""

    form_saved = Signal(dict)

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.translator = LocalTranslator()
        self.ui_file_path = None
        self.form_alias = None

        # Каталог для хранения .ui файлов
        self.forms_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "forms")
        os.makedirs(self.forms_dir, exist_ok=True)

    def launch(self, form_json, form_alias):
        """Запускает Qt Designer с формой"""
        self.form_alias = form_alias
        self.ui_file_path = os.path.join(self.forms_dir, f"{form_alias}.ui")

        # 1. Создаём .ui файл из JSON (или пустой)
        self._create_ui_file(form_json)

        # 2. Запускаем Qt Designer и ждём
        try:
            subprocess.run(['designer', self.ui_file_path], check=False)

            # 3. После закрытия загружаем результат
            QTimer.singleShot(500, self._load_result)

        except FileNotFoundError:
            QMessageBox.critical(
                self.parent,
                self.translator.tr('error'),
                self.translator.tr('designer_not_found')
            )

    def _create_ui_file(self, form_json):
        """Создаёт .ui файл из JSON"""
        # Подготовка JSON
        if not form_json:
            ui_content = self._get_empty_ui()
        elif isinstance(form_json, str):
            try:
                form_dict = json.loads(form_json)
                ui_content = self._json_to_ui(form_dict)
            except json.JSONDecodeError:
                ui_content = self._get_empty_ui()
        else:
            ui_content = self._json_to_ui(form_json)

        # Записываем файл
        with open(self.ui_file_path, 'w', encoding='utf-8') as f:
            f.write(ui_content)

    def _get_empty_ui(self):
        """Возвращает пустой .ui файл"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="5.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>800</width>
    <height>600</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Новая форма</string>
  </property>
 </widget>
</ui>'''

    def _json_to_ui(self, form_json):
        """Конвертирует JSON в .ui XML"""
        form_name = form_json.get('objectName', 'Form')
        window_title = form_json.get('windowTitle', 'Новая форма')
        width = form_json.get('geometry', {}).get('width', 800)
        height = form_json.get('geometry', {}).get('height', 600)

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ui version="5.0">
 <class>{form_name}</class>
 <widget class="QWidget" name="{form_name}">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>{width}</width>
    <height>{height}</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>{window_title}</string>
  </property>
 </widget>
</ui>'''

    def _load_result(self):
        """Загружает результат из .ui файла в JSON"""
        if not self.ui_file_path or not os.path.exists(self.ui_file_path):
            return

        try:
            form_json = self._ui_to_json(self.ui_file_path)
            if form_json:
                self.form_saved.emit(form_json)
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                self.translator.tr('error'),
                f"{self.translator.tr('designer_reload_error')}: {str(e)}"
            )
        finally:
            # 4. Удаляем .ui файл
            self._cleanup()

    def _ui_to_json(self, ui_file_path):
        """Загружает JSON из .ui файла"""
        import xml.etree.ElementTree as ET

        tree = ET.parse(ui_file_path)
        root = tree.getroot()

        main_widget = root.find('.//widget')
        if main_widget is None:
            return None

        form_name = main_widget.get('name', 'Form')

        window_title_elem = root.find('.//property[@name="windowTitle"]/string')
        window_title = window_title_elem.text if window_title_elem is not None else 'Новая форма'

        width, height = 800, 600
        width_elem = root.find('.//property[@name="geometry"]/rect/width')
        height_elem = root.find('.//property[@name="geometry"]/rect/height')
        if width_elem is not None and width_elem.text:
            width = int(width_elem.text)
        if height_elem is not None and height_elem.text:
            height = int(height_elem.text)

        return {
            "class": "MozartForm",
            "objectName": form_name,
            "windowTitle": window_title,
            "geometry": {"x": 0, "y": 0, "width": width, "height": height},
            "widgets": [],
            "connections": [],
            "custom_properties": {}
        }

    def _cleanup(self):
        """Удаляет временный .ui файл"""
        if self.ui_file_path and os.path.exists(self.ui_file_path):
            try:
                os.unlink(self.ui_file_path)
            except:
                pass