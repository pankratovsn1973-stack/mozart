# Полный путь: utils/fullBackup/fullBackup.py
# -*- coding: utf-8 -*-
"""
Автоматизированная утилита полного резервного копирования для СУБД MOZART ERP.
Создает сжатый бинарный бэкап PostgreSQL строго по списку целевых схем проекта,
структурирует архив и готовит shell-скрипт для мгновенного развертывания СУБД.
"""
import os
import sys
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QFormLayout, QLineEdit, QPushButton,
                               QGridLayout, QCheckBox, QLabel, QTextEdit,
                               QFileDialog, QMessageBox)



class MozartBackupWindow(QDialog):
    def __init__(self, parent=None):
        """Инициализирует графическое окно управления резервным копированием СУБД MOZART."""
        super().__init__(parent)
        self.setWindowTitle("Резервное копирование СУБД MOZART ERP")
        self.resize(650, 500)

        # Конфигурация по умолчанию
        self.db_host = "localhost"
        self.db_port = "5432"
        self.db_name = "mozart_erp"
        self.db_user = "postgres"
        self.db_pass = "SQLSerIra!"
        self.default_backup_dir = "/home/sergey/Documents/configurate/backups"

        # Полный список доступных схем проекта
        self.all_schemas = [
            "auth", "autodoc", "class_erp", "data",
            "ext", "lang", "meta", "mozart", "public"
        ]
        self.schema_checkboxes = {}

        # Инициализируем интерфейс
        self.setup_ui()

    def setup_ui(self):
        """Строит визуальный интерфейс окна бэкапа (поля, чекбоксы схем, выбор папки и лог)."""
        main_layout = QVBoxLayout(self)

        # 1. Блок параметров подключения к PostgreSQL
        conn_group = QGroupBox("Параметры подключения к СУБД")
        conn_layout = QFormLayout(conn_group)

        self.host_edit = QLineEdit(self.db_host)
        self.port_edit = QLineEdit(self.db_port)
        self.name_edit = QLineEdit(self.db_name)
        self.user_edit = QLineEdit(self.db_user)
        self.pass_edit = QLineEdit(self.db_pass)
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

        conn_layout.addRow("Сервер (Host):", self.host_edit)
        conn_layout.addRow("Порт (Port):", self.port_edit)
        conn_layout.addRow("Имя базы данных:", self.name_edit)
        conn_layout.addRow("Пользователь (User):", self.user_edit)
        conn_layout.addRow("Пароль доступа:", self.pass_edit)
        main_layout.addWidget(conn_group)

        # 2. Блок выбора целевого каталога хранения
        dir_group = QGroupBox("Каталог назначения бэкапа")
        dir_layout = QHBoxLayout(dir_group)
        self.dir_edit = QLineEdit(self.default_backup_dir)
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(self.btn_browse)
        main_layout.addWidget(dir_group)

        # 3. Блок выбора схем (чекбоксы в сеточном расположении)
        schema_group = QGroupBox("Выбор целевых схем для выгрузки")
        schema_layout = QGridLayout(schema_group)

        for idx, schema in enumerate(self.all_schemas):
            cb = QCheckBox(schema)
            cb.setChecked(True)  # По умолчанию отмечаем все схемы
            self.schema_checkboxes[schema] = cb
            row = idx // 3
            col = idx % 3
            schema_layout.addWidget(cb, row, col)
        main_layout.addWidget(schema_group)

        # 4. Текстовое окно для вывода лога выполнения pg_dump в реальном времени
        main_layout.addWidget(QLabel("Лог выполнения операции:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(self._get_mono_font())
        main_layout.addWidget(self.log_output)

        # 5. Кнопки управления процессом
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Запустить бэкап")
        self.btn_start.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_start.clicked.connect(self.execute_backup)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)


    def browse_folder(self):
        """Вызывает стандартный системный диалог QFileDialog для интерактивного выбора директории бэкапа."""
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите каталог для сохранения резервных копий",
            self.dir_edit.text()
        )
        if selected_dir:
            self.dir_edit.setText(selected_dir)

    def execute_backup(self):
        """Собирает параметры из интерфейса и запускает pg_dump в изолированном фоновом потоке/процессе."""
        self.log_output.clear()
        target_dir = self.dir_edit.text().strip()

        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать каталог: {e}")
                return

        # Собираем отмеченные схемы из чекбоксов
        selected_schemas = [schema for schema, cb in self.schema_checkboxes.items() if cb.isChecked()]
        if not selected_schemas:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну схему для бэкапа!")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mozart_backup_{timestamp}.dump"
        backup_path = os.path.join(target_dir, backup_filename)
        restore_script_path = os.path.join(target_dir, f"restore_{timestamp}.sh")

        self.log_output.append(
            f"[{datetime.now().strftime('%H:%M:%S')}] Старт резервного копирования базы '{self.name_edit.text()}'...")
        QApplication.processEvents()

        # Настраиваем переменные окружения для передачи пароля утилите pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = self.pass_edit.text()

        # Формируем команду вызова pg_dump
        cmd = [
            "pg_dump",
            "-h", self.host_edit.text(),
            "-p", self.port_edit.text(),
            "-U", self.user_edit.text(),
            "-F", "c",  # Кастомный сжатый формат
            "-b",  # Включая большие объекты (скрипты)
            "-v",  # Детальный лог
            "-f", backup_path
        ]

        # Добавляем в параметры только выбранные пользователем схемы
        for schema in selected_schemas:
            cmd.extend(["--schema", schema])

        cmd.append(self.name_edit.text())

        try:
            # Запускаем системную утилиту pg_dump
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)

            # Выводим подробный системный отчет pg_dump в окно лога
            if result.stderr:
                self.log_output.append(result.stderr)

            self.log_output.append(f"\n[SUCCESS] Резервная копия успешно сформирована:\n{backup_path}")

            # Генерируем исполняемый bash-скрипт восстановления в ту же папку
            self._generate_restore_script(restore_script_path, backup_filename)
            QMessageBox.information(self, "Успех", f"Резервная копия успешно создана в каталоге:\n{target_dir}")

        except subprocess.CalledProcessError as e:
            self.log_output.append(f"\n[CRITICAL ERROR] Ошибка выполнения pg_dump:\n{e.stderr}")
            QMessageBox.critical(self, "Критическая ошибка", "Не удалось выполнить резервное копирование СУБД.")

    def _generate_restore_script(self, script_path: str, backup_filename: str):
        """Внутренний метод: генерирует shell-скрипт восстановления с подстановкой текущего пароля."""
        restore_cmd = (
            f"#!/bin/bash\n"
            f"# Скрипт автоматического развертывания бэкапа MOZART ERP\n"
            f"echo '=== Старт восстановления базы данных MOZART ==='\n"
            f"export PGPASSWORD=\"{self.pass_edit.text()}\"\n"
            f"pg_restore -h {self.host_edit.text()} -p {self.port_edit.text()} -U {self.user_edit.text()} "
            f"-d {self.name_edit.text()} -v -c --if-exists \"\\$(dirname \"\\$0\")/{backup_filename}\"\n"
            f"echo '=== Восстановление успешно завершено! ==='\n"
        )

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(restore_cmd)

        os.chmod(script_path, 0o755)
        self.log_output.append(
            f"[INFO] Подготовлен автоматический shell-скрипт восстановления: {os.path.basename(script_path)}")

    def _get_mono_font(self):
        """Внутренний вспомогательный метод: возвращает моноширинный шрифт для лога."""
        from PySide6.QtGui import QFont
        font = QFont("Courier New", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font



    def create_full_backup(self) -> str:
        """
        Выполняет полный бинарный бэкап базы данных со всеми схемами и триггерами.
        Генерирует сопутствующий скрипт для автоматического восстановления СУБД.
        """
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mozart_backup_{timestamp}.dump"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        restore_script_path = os.path.join(self.backup_dir, f"restore_{timestamp}.sh")

        print(f"[BACKUP] Старт резервного копирования базы '{self.db_name}'...")

        # Пробрасываем пароль через переменную окружения PostgreSQL,
        # чтобы утилита pg_dump выполнилась в автоматическом режиме без запроса в консоли
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_pass

        # Формируем базовую команду pg_dump в кастомном бинарном формате compressed (-F c)
        cmd = [
            "pg_dump",
            "-h", self.db_host,
            "-p", self.db_port,
            "-U", self.db_user,
            "-F", "c",  # Кастомный бинарный формат сжатия
            "-b",  # Включая большие объекты (blobs скриптов)
            "-v",  # Подробный вывод прогресса в консоль
            "-f", backup_path
        ]

        # Динамически добавляем флаг --schema для каждой схемы из нашего списка
        for schema in self.target_schemas:
            cmd.extend(["--schema", schema])

        # Последним аргументом передаем имя целевой базы данных
        cmd.append(self.db_name)

        try:
            # Запускаем системную утилиту PostgreSQL с пробросом пароля и фильтром схем
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            print(f"[SUCCESS] Бэкап успешно создан: {backup_path}")

            # Автоматически генерируем сопутствующий скрипт восстановления
            self._generate_restore_script(restore_script_path, backup_filename)
            return backup_path

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Ошибка выполнения pg_dump:\n{e.stderr}")
            raise e


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    app = QApplication(sys.argv)
    window = MozartBackupWindow()
    window.show()
    sys.exit(app.exec())
