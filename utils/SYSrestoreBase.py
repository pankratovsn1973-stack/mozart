import subprocess
import os
import sys
# использование системного рестора из системного бакапа
# --- Настройки для ЦЕЛЕВОГО сервера ---
TARGET_HOST = "target-server-ip"
TARGET_PORT = "5432"
TARGET_USER = "postgres"
TARGET_PASSWORD = "password_on_target"
TARGET_DB = "mozart_erp"

# Путь к файлу дампа
DUMP_FILE = "/path/to/mozart_erp_20260504_120000.dump"


# --- Конец настроек ---

def check_prerequisites():
    """Проверка наличия pg_restore"""
    try:
        subprocess.run(["pg_restore", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ошибка: pg_restore не найден. Установите PostgreSQL client tools.")
        return False


def check_dump_file():
    """Проверка целостности дампа"""
    if not os.path.exists(DUMP_FILE):
        print(f"Ошибка: файл дампа не найден: {DUMP_FILE}")
        return False

    # Проверяем, что это валидный архив
    cmd = ["pg_restore", "--list", DUMP_FILE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Дамп валиден. Содержит {len(result.stdout.splitlines())} объектов")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка: невалидный дамп-файл: {e.stderr}")
        return False


def check_target_connection():
    """Проверка подключения к целевому серверу"""
    env = os.environ.copy()
    env["PGPASSWORD"] = TARGET_PASSWORD

    cmd = [
        "psql",
        "-U", TARGET_USER,
        "-h", TARGET_HOST,
        "-p", TARGET_PORT,
        "-d", "postgres",
        "-c", "SELECT 1"
    ]

    try:
        subprocess.run(cmd, env=env, capture_output=True, check=True)
        print(f"Подключение к {TARGET_HOST}:{TARGET_PORT} успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка подключения к целевому серверу: {e.stderr.decode()}")
        return False


def check_target_database():
    """Проверка существования базы на целевом сервере"""
    env = os.environ.copy()
    env["PGPASSWORD"] = TARGET_PASSWORD

    cmd = [
        "psql",
        "-U", TARGET_USER,
        "-h", TARGET_HOST,
        "-p", TARGET_PORT,
        "-d", "postgres",
        "-t", "-c",
        f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'"
    ]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        if "1" in result.stdout:
            print(f"База {TARGET_DB} существует на целевом сервере")
            return True
        else:
            print(f"База {TARGET_DB} НЕ существует на целевом сервере")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Ошибка проверки базы: {e.stderr}")
        return False


def restore_database():
    """Основная функция восстановления"""
    print("=" * 60)
    print("ПРОВЕРКА ПЕРЕД ВОССТАНОВЛЕНИЕМ")
    print("=" * 60)

    # Проверки
    if not check_prerequisites():
        return False

    if not check_dump_file():
        return False

    if not check_target_connection():
        return False

    print("\n" + "=" * 60)
    print("ВОССТАНОВЛЕНИЕ БАЗЫ")
    print("=" * 60)

    env = os.environ.copy()
    env["PGPASSWORD"] = TARGET_PASSWORD

    # Проверяем существование базы
    db_exists = check_target_database()

    if not db_exists:
        print(f"Создаем базу {TARGET_DB}...")
        create_cmd = [
            "psql",
            "-U", TARGET_USER,
            "-h", TARGET_HOST,
            "-p", TARGET_PORT,
            "-d", "postgres",
            "-c", f"CREATE DATABASE {TARGET_DB}"
        ]
        try:
            subprocess.run(create_cmd, env=env, capture_output=True, check=True)
            print(f"База {TARGET_DB} создана")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка создания базы: {e.stderr.decode()}")
            return False

    # Восстановление
    print(f"Восстанавливаем из {DUMP_FILE}...")
    restore_cmd = [
        "pg_restore",
        "-U", TARGET_USER,
        "-h", TARGET_HOST,
        "-p", TARGET_PORT,
        "-d", TARGET_DB,
        "-v",  # подробный вывод
        "--no-owner",  # игнорировать владельцев (полезно если роли отличаются)
        "--no-privileges",  # игнорировать привилегии
        DUMP_FILE
    ]

    try:
        result = subprocess.run(
            restore_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print("\n" + "=" * 60)
        print("ВОССТАНОВЛЕНИЕ УСПЕШНО ЗАВЕРШЕНО!")
        print("=" * 60)

        # Проверяем схемы после восстановления
        check_cmd = [
            "psql",
            "-U", TARGET_USER,
            "-h", TARGET_HOST,
            "-p", TARGET_PORT,
            "-d", TARGET_DB,
            "-c", "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
        ]
        try:
            schemas_result = subprocess.run(check_cmd, env=env, capture_output=True, text=True, check=True)
            print("\nВосстановленные схемы:")
            print(schemas_result.stdout)
        except:
            pass

        return True

    except subprocess.CalledProcessError as e:
        print(f"Ошибка восстановления: {e.stderr}")
        return False


if __name__ == "__main__":
    success = restore_database()
    sys.exit(0 if success else 1)