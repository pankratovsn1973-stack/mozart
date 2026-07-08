# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/utils/analitik_mozart/analitik_core/assembler.py
"""
Сборщик кода из частей для Аналитика Моцарт.
Версия: 1.0 — сборка файлов, классов, методов из атомарных частей
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from analitik_core.database import get_session
from analitik_core.models import Entity, EntityType


class CodeAssembler:
    """Сборщик кода из атомарных частей."""

    def __init__(self, db_session: Session = None):
        self.db_session = db_session or get_session()

    # ================================================================
    # СБОРКА ФАЙЛА
    # ================================================================

    def assemble_file(self, file_id: str) -> Optional[str]:
        """Собирает полный текст файла из всех его частей."""
        file_entity = self.db_session.query(Entity).filter(
            Entity.id == file_id,
            Entity.is_active == True
        ).first()

        if not file_entity:
            return None

        lines = []

        # 1. Shebang (если есть)
        if file_entity.t_blobskript and file_entity.t_blobskript.startswith('#!'):
            lines.append(file_entity.t_blobskript)
            lines.append('')

        # 2. Кодировка (если есть)
        if file_entity.t_blobskript and 'coding:' in file_entity.t_blobskript:
            if file_entity.t_blobskript not in lines:
                lines.append(file_entity.t_blobskript)
                lines.append('')

        # 3. Заголовок (docstring)
        headers = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.HEADER,
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for header in headers:
            if header.t_blobskript:
                lines.append(f'"""\n{header.t_blobskript}\n"""')
                lines.append('')

        # 4. Импорты
        imports = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.IMPORT,
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for imp in imports:
            if imp.t_blobskript:
                lines.append(imp.t_blobskript)

        if imports:
            lines.append('')

        # 5. Глобальные переменные
        globals_ = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.GLOBAL_VARIABLE,
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for var in globals_:
            if var.t_blobskript:
                lines.append(var.t_blobskript)

        if globals_:
            lines.append('')

        # 6. Процедуры
        procedures = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROCEDURE,
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for proc in procedures:
            if proc.t_blobskript:
                lines.append(proc.t_blobskript)
                lines.append('')

        # 7. Классы (собираем каждый класс)
        classes = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.CLASS,
            Entity.parent_id == file_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for cls in classes:
            class_text = self.assemble_class(str(cls.id))
            if class_text:
                lines.append(class_text)
                lines.append('')

        return '\n'.join(lines)

    # ================================================================
    # СБОРКА КЛАССА
    # ================================================================

    def assemble_class(self, class_id: str) -> Optional[str]:
        """Собирает полный текст класса из его частей."""
        cls_entity = self.db_session.query(Entity).filter(
            Entity.id == class_id,
            Entity.is_active == True
        ).first()

        if not cls_entity:
            return None

        lines = []

        # 1. Заголовок класса (class Xxx(...):)
        if cls_entity.t_blobskript:
            lines.append(cls_entity.t_blobskript)
        else:
            bases = cls_entity.j_data.get('bases', []) if cls_entity.j_data else []
            lines.append(f"class {cls_entity.c_name}({', '.join(bases)}):")

        # 2. Docstring класса
        if cls_entity.m_comment:
            lines.append(f'    """{cls_entity.m_comment}"""')

        # 3. Переменные класса
        class_vars = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.CLASS_VARIABLE,
            Entity.parent_id == class_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for var in class_vars:
            if var.t_blobskript:
                for line in var.t_blobskript.split('\n'):
                    lines.append(f"    {line}")

        if class_vars:
            lines.append('')

        # 4. Свойства (@property)
        props = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.PROPERTY,
            Entity.parent_id == class_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for prop in props:
            if prop.t_blobskript:
                for line in prop.t_blobskript.split('\n'):
                    lines.append(f"    {line}")
                lines.append('')

        # 5. Методы
        methods = self.db_session.query(Entity).filter(
            Entity.type_id == EntityType.METHOD,
            Entity.parent_id == class_id,
            Entity.is_active == True
        ).order_by(Entity.n_order).all()

        for method in methods:
            if method.t_blobskript:
                for line in method.t_blobskript.split('\n'):
                    lines.append(f"    {line}")
                lines.append('')

        return '\n'.join(lines)

    # ================================================================
    # СБОРКА МЕТОДА (для отдельного использования)
    # ================================================================

    def assemble_method(self, method_id: str) -> Optional[str]:
        """Возвращает полный текст метода."""
        method = self.db_session.query(Entity).filter(
            Entity.id == method_id,
            Entity.is_active == True
        ).first()

        if not method:
            return None

        return method.t_blobskript

    # ================================================================
    # СБОРКА ПРОЦЕДУРЫ
    # ================================================================

    def assemble_procedure(self, proc_id: str) -> Optional[str]:
        """Возвращает полный текст процедуры."""
        proc = self.db_session.query(Entity).filter(
            Entity.id == proc_id,
            Entity.is_active == True
        ).first()

        if not proc:
            return None

        return proc.t_blobskript

    # ================================================================
    # ПЕРЕСБОРКА ПОСЛЕ ИЗМЕНЕНИЯ
    # ================================================================

    def rebuild_after_change(self, entity_id: str) -> Dict[str, Any]:
        """
        Пересобирает все уровни после изменения сущности.
        Возвращает ID новых версий.
        """
        entity = self.db_session.query(Entity).filter(
            Entity.id == entity_id,
            Entity.is_active == True
        ).first()

        if not entity:
            return {'error': 'Сущность не найдена'}

        result = {'old_version': entity_id}

        # Определяем, что нужно пересобрать
        if entity.type_id == EntityType.METHOD:
            # Изменился метод → пересобираем класс
            class_id = entity.parent_id
            new_class = self._rebuild_class(class_id)
            result['new_class'] = str(new_class.id) if new_class else None

            # Пересобираем файл
            class_entity = self.db_session.query(Entity).filter(Entity.id == class_id).first()
            if class_entity:
                file_id = class_entity.parent_id
                new_file = self._rebuild_file(file_id)
                result['new_file'] = str(new_file.id) if new_file else None

        elif entity.type_id == EntityType.PROPERTY:
            # Изменилось свойство → пересобираем класс
            class_id = entity.parent_id
            new_class = self._rebuild_class(class_id)
            result['new_class'] = str(new_class.id) if new_class else None

            # Пересобираем файл
            class_entity = self.db_session.query(Entity).filter(Entity.id == class_id).first()
            if class_entity:
                file_id = class_entity.parent_id
                new_file = self._rebuild_file(file_id)
                result['new_file'] = str(new_file.id) if new_file else None

        elif entity.type_id == EntityType.CLASS_VARIABLE:
            # Изменилась переменная класса → пересобираем класс
            class_id = entity.parent_id
            new_class = self._rebuild_class(class_id)
            result['new_class'] = str(new_class.id) if new_class else None

            # Пересобираем файл
            class_entity = self.db_session.query(Entity).filter(Entity.id == class_id).first()
            if class_entity:
                file_id = class_entity.parent_id
                new_file = self._rebuild_file(file_id)
                result['new_file'] = str(new_file.id) if new_file else None

        elif entity.type_id == EntityType.CLASS:
            # Изменился класс → пересобираем файл
            file_id = entity.parent_id
            new_file = self._rebuild_file(file_id)
            result['new_file'] = str(new_file.id) if new_file else None

        elif entity.type_id in (EntityType.IMPORT, EntityType.GLOBAL_VARIABLE, EntityType.PROCEDURE):
            # Изменился импорт, переменная или процедура → пересобираем файл
            file_id = entity.parent_id
            new_file = self._rebuild_file(file_id)
            result['new_file'] = str(new_file.id) if new_file else None

        result['success'] = True
        return result

    def _rebuild_class(self, class_id: str) -> Optional[Entity]:
        """Пересобирает класс: закрывает старый, создаёт новый."""
        old_class = self.db_session.query(Entity).filter(
            Entity.id == class_id,
            Entity.is_active == True
        ).first()

        if not old_class:
            return None

        # Собираем новый текст класса
        new_text = self.assemble_class(class_id)
        if not new_text:
            return None

        # Закрываем старый класс
        old_class.is_active = False
        old_class.dt_end = datetime.now()

        # Создаём новый класс
        new_class = Entity(
            type_id=EntityType.CLASS,
            c_name=old_class.c_name,
            parent_id=old_class.parent_id,
            t_blobskript=new_text.split('\n')[0] if new_text else '',  # только заголовок
            t_full_text=new_text,
            j_data=old_class.j_data.copy() if old_class.j_data else {},
            m_comment=old_class.m_comment,
            n_order=old_class.n_order,
            n_old_version=old_class.id
        )
        self.db_session.add(new_class)
        self.db_session.flush()

        # Копируем методы, свойства, переменные класса в новую версию
        self._copy_class_parts(old_class.id, new_class.id)

        return new_class

    def _copy_class_parts(self, old_class_id: str, new_class_id: str):
        """Копирует части класса в новую версию."""
        parts = self.db_session.query(Entity).filter(
            Entity.parent_id == old_class_id,
            Entity.is_active == True
        ).all()

        for part in parts:
            new_part = Entity(
                type_id=part.type_id,
                c_name=part.c_name,
                parent_id=new_class_id,
                t_blobskript=part.t_blobskript,
                t_full_text=part.t_full_text,
                j_data=part.j_data.copy() if part.j_data else {},
                m_comment=part.m_comment,
                n_order=part.n_order,
                n_old_version=part.id
            )
            self.db_session.add(new_part)

        self.db_session.flush()

    def _rebuild_file(self, file_id: str) -> Optional[Entity]:
        """Пересобирает файл: закрывает старый, создаёт новый."""
        old_file = self.db_session.query(Entity).filter(
            Entity.id == file_id,
            Entity.is_active == True
        ).first()

        if not old_file:
            return None

        # Собираем новый текст файла
        new_text = self.assemble_file(file_id)
        if not new_text:
            return None

        # Закрываем старый файл
        old_file.is_active = False
        old_file.dt_end = datetime.now()

        # Создаём новый файл
        new_file = Entity(
            type_id=EntityType.FILE,
            c_name=old_file.c_name,
            parent_id=old_file.parent_id,
            t_full_text=new_text,
            j_data=old_file.j_data.copy() if old_file.j_data else {},
            m_comment=old_file.m_comment,
            n_order=old_file.n_order,
            n_old_version=old_file.id
        )
        self.db_session.add(new_file)
        self.db_session.flush()

        # Копируем все части файла в новую версию
        self._copy_file_parts(old_file.id, new_file.id)

        return new_file

    def _copy_file_parts(self, old_file_id: str, new_file_id: str):
        """Копирует все части файла в новую версию."""
        parts = self.db_session.query(Entity).filter(
            Entity.parent_id == old_file_id,
            Entity.is_active == True
        ).all()

        for part in parts:
            new_part = Entity(
                type_id=part.type_id,
                c_name=part.c_name,
                parent_id=new_file_id,
                t_blobskript=part.t_blobskript,
                t_full_text=part.t_full_text,
                j_data=part.j_data.copy() if part.j_data else {},
                m_comment=part.m_comment,
                n_order=part.n_order,
                n_old_version=part.id
            )
            self.db_session.add(new_part)

        self.db_session.flush()


# ================================================================
# УТИЛИТА
# ================================================================

def assemble_file(file_id: str) -> Optional[str]:
    """Быстрая сборка файла."""
    assembler = CodeAssembler()
    return assembler.assemble_file(file_id)


def assemble_class(class_id: str) -> Optional[str]:
    """Быстрая сборка класса."""
    assembler = CodeAssembler()
    return assembler.assemble_class(class_id)


def rebuild_after_change(entity_id: str) -> Dict[str, Any]:
    """Быстрая пересборка после изменения."""
    assembler = CodeAssembler()
    return assembler.rebuild_after_change(entity_id)