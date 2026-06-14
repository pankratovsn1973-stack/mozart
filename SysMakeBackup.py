import subprocess
import os
from datetime import datetime
#использование системного бакапа постгри
# --- Настройки ---
DB_NAME = "mozart_erp"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
PGPASSWORD = "SQLSerIra!"

# Папка для бэкапов
BACKUP_DIR = "/home/sergey/Documents/dbBCK"


# --- Конец настроек ---

def create_backup():
    # Создаем папку, если её нет
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Формируем имя файла с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{DB_NAME}_{timestamp}.dump")
    log_file = os.path.join(BACKUP_DIR, "backup.log")

    # Настраиваем окружение для пароля
    env = os.environ.copy()
    env["PGPASSWORD"] = PGPASSWORD

    cmd = [
        "pg_dump",
        "-U", DB_USER,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-Fc",  # Сжатый формат
        "-f", backup_file,
        DB_NAME
    ]

    try:
        # Выполняем команду и пишем лог
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now()}] Starting backup to {backup_file}\n")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            log.write(f"[{datetime.now()}] Backup successful\n")
            if result.stderr:
                log.write(f"STDERR: {result.stderr}\n")
        print(f"Бэкап успешно создан: {backup_file}")

    except subprocess.CalledProcessError as e:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now()}] BACKUP FAILED\n")
            log.write(f"STDERR: {e.stderr}\n")
        print(f"Ошибка создания бэкапа! Детали в логе: {log_file}")


if __name__ == "__main__":
    create_backup()