# create_import_structure.py
import os

ROOT = "/home/sergey/Documents/configurate"

STRUCTURE = {
    "mozart_import/graph": [
        "__init__.py",
        "graphics_items.py",
        "graphics_view.py",
        "relation_scene.py",
        "link_line.py",
    ],
    "mozart_import/wizards": [
        "__init__.py",
        "source_page.py",
        "schema_page.py",
        "relation_page.py",
        "mapping_detail_page.py",
        "execute_page.py",
    ],
    "mozart_import/core": [
        "__init__.py",
        "models.py",
        "source_analyzer.py",
        "mapping_manager.py",
    ],
    "mozart_import/utils": [
        "__init__.py",
        "field_creator.py",
    ],
    "mozart_import/connectors": [],  # уже есть, оставляем
}

def create_structure():
    for dirpath, files in STRUCTURE.items():
        full_path = os.path.join(ROOT, dirpath)
        os.makedirs(full_path, exist_ok=True)
        for filename in files:
            file_path = os.path.join(full_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# -*- coding: utf-8 -*-\n")
                print(f"Created: {file_path}")
            else:
                print(f"Exists: {file_path}")

if __name__ == "__main__":
    create_structure()
    print("Done.")