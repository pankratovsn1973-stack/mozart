# /home/sergey/Documents/configurate/tabs/forms/form_utils.py
# -*- coding: utf-8 -*-

import json
import tempfile
import os


def get_empty_form_json():
    """Возвращает JSON пустой формы"""
    return {
        "class": "MozartForm",
        "objectName": "Form",
        "windowTitle": "Новая форма",
        "geometry": {"x": 0, "y": 0, "width": 800, "height": 600},
        "widgets": [],
        "connections": [],
        "custom_properties": {}
    }


def form_data_to_json(cname, calias, ientitytypeid, mstate_json):
    """Преобразует данные формы в JSON для сохранения"""
    if isinstance(mstate_json, dict):
        mstate_json = json.dumps(mstate_json, ensure_ascii=False)
    return {
        "cname": cname,
        "calias": calias,
        "ientitytypeid": ientitytypeid,
        "mstate_json": mstate_json
    }


def parse_mstate(mstate_text):
    """Парсит mstate_json из строки"""
    if not mstate_text:
        return None
    try:
        return json.loads(mstate_text)
    except:
        return mstate_text


# /home/sergey/Documents/configurate/tabs/forms/form_utils.py

def create_temp_ui_file(form_json):
    """Создаёт временный .ui файл и возвращает путь к нему"""
    from utils.json_to_ui import json_to_ui

    # Убеждаемся, что form_json — это словарь
    if isinstance(form_json, str):
        try:
            import json
            form_json = json.loads(form_json)
        except:
            form_json = get_empty_form_json()

    if not form_json:
        form_json = get_empty_form_json()

    fd, temp_file = tempfile.mkstemp(suffix='.ui', prefix='mozart_form_')
    os.close(fd)
    json_to_ui(json_data=form_json, output_ui_path=temp_file)
    return temp_file


def load_from_ui_file(ui_file_path):
    """Загружает форму из .ui файла и возвращает JSON"""
    from utils.ui_to_json import convert_ui_to_json
    return convert_ui_to_json(ui_file_path=ui_file_path)