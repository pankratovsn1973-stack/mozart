import json
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
import getpass

# --- Настройки по умолчанию (можно изменить) ---
# Если задать значения здесь, скрипт не будет запрашивать их при запуске
DEFAULT_TARGET_HOST = None  # Например: "192.168.1.100"
DEFAULT_TARGET_PORT = "5432"
DEFAULT_TARGET_DB = None  # Например: "mozart_erp"
DEFAULT_TARGET_USER = None  # Например: "postgres"
DEFAULT_TARGET_PASSWORD = None  # Например: "password"


# --- Конец настроек ---

def get_target_config():
    """Получение параметров подключения к целевому серверу"""

    print("=" * 60)
    print("НАСТРОЙКА ПОДКЛЮЧЕНИЯ К ЦЕЛЕВОМУ СЕРВЕРУ")
    print("=" * 60)
    print("Оставьте поле пустым для значения по умолчанию\n")

    config = {}

    # Хост
    if DEFAULT_TARGET_HOST:
        config["host"] = input(f"Хост PostgreSQL [{DEFAULT_TARGET_HOST}]: ").strip() or DEFAULT_TARGET_HOST
    else:
        config["host"] = input("Хост PostgreSQL [localhost]: ").strip() or "localhost"

    # Порт
    if DEFAULT_TARGET_PORT:
        config["port"] = input(f"Порт [{DEFAULT_TARGET_PORT}]: ").strip() or DEFAULT_TARGET_PORT
    else:
        config["port"] = input("Порт [5432]: ").strip() or "5432"

    # База данных
    if DEFAULT_TARGET_DB:
        config["database"] = input(f"Имя базы данных [{DEFAULT_TARGET_DB}]: ").strip() or DEFAULT_TARGET_DB
    else:
        config["database"] = input("Имя базы данных [mozart_erp]: ").strip() or "mozart_erp"

    # Пользователь
    if DEFAULT_TARGET_USER:
        config["user"] = input(f"Пользователь [{DEFAULT_TARGET_USER}]: ").strip() or DEFAULT_TARGET_USER
    else:
        config["user"] = input("Пользователь [postgres]: ").strip() or "postgres"

    # Пароль
    if DEFAULT_TARGET_PASSWORD:
        config["password"] = input(f"Пароль [{DEFAULT_TARGET_PASSWORD}]: ").strip() or DEFAULT_TARGET_PASSWORD
    else:
        config["password"] = getpass.getpass("Пароль: ").strip()
        if not config["password"]:
            config["password"] = input("Пароль не может быть пустым. Введите пароль: ").strip()

    return config


def test_connection(config):
    """Проверка подключения к целевому серверу"""
    print("\nПроверка подключения...")
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database="postgres",
            user=config["user"],
            password=config["password"]
        )
        conn.close()
        print("✅ Подключение успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


def create_database_if_not_exists(config):
    """Создание базы данных, если её нет"""
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="postgres",
        user=config["user"],
        password=config["password"]
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (config["database"],)
            )
            if cur.fetchone():
                print(f"\n⚠️  База данных '{config['database']}' уже существует!")
                action = input("Пересоздать базу? (DROP/CREATE) [y/N]: ").strip().lower()
                if action == 'y':
                    # Отключаем всех пользователей от базы
                    cur.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{config['database']}'
                        AND pid <> pg_backend_pid()
                    """)
                    cur.execute(f"DROP DATABASE {config['database']}")
                    cur.execute(f"CREATE DATABASE {config['database']} ENCODING 'UTF8'")
                    print(f"✅ База данных '{config['database']}' пересоздана")
                else:
                    print("Будет использована существующая база данных")
            else:
                cur.execute(f"CREATE DATABASE {config['database']} ENCODING 'UTF8'")
                print(f"✅ База данных '{config['database']}' создана")
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
        raise
    finally:
        conn.close()


def execute_sql_block(cur, sql_text, description):
    """Выполнение блока SQL с обработкой ошибок"""
    if not sql_text or not sql_text.strip():
        return True

    statements = [s.strip() for s in sql_text.split(';') if s.strip()]

    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt + ';')
        except Exception as e:
            print(f"  ⚠️  Ошибка в '{description}' (строка {i}): {str(e)[:100]}")
            # Продолжаем выполнение, так как объекты могут уже существовать
            conn = cur.connection
            conn.rollback()
    return True


def restore_from_json(json_file, config):
    """Восстановление базы из JSON файла"""

    # Проверка файла
    if not os.path.exists(json_file):
        print(f"❌ Файл {json_file} не найден!")
        return False

    # Загрузка данных
    print(f"\n📂 Загрузка данных из {json_file}...")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    export_info = data.get("export_info", {})
    schemas = data.get("schemas", [])

    print(f"📊 Схем для восстановления: {len(schemas)}")
    print(f"📋 Схемы: {', '.join([s['schema_name'] for s in schemas])}")

    if not schemas:
        print("❌ Нет данных для восстановления!")
        return False

    # Подключение к целевой базе
    print(f"\nПодключение к {config['host']}:{config['port']}/{config['database']}...")
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"]
    )

    try:
        with conn.cursor() as cur:
            for schema in schemas:
                schema_name = schema["schema_name"]
                print(f"\n{'=' * 60}")
                print(f"Обработка схемы: {schema_name}")
                print(f"{'=' * 60}")

                try:
                    # 1. Создаем схему
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                    print("  ✓ Схема создана")
                except Exception as e:
                    print(f"  ⚠️  Ошибка создания схемы: {e}")
                    conn.rollback()
                    continue

                # 2. Создаем таблицы (cleartable)
                print("  📋 Создание таблиц...")
                execute_sql_block(cur, schema.get("cleartable"), "таблицы")
                conn.commit()
                print("  ✓ Таблицы созданы")

                # 3. Восстанавливаем данные из JSON (если есть)
                if schema.get("jsondata") and schema["jsondata"] != "null":
                    print("  📊 Восстановление данных...")
                    tables_data = schema["jsondata"]
                    if isinstance(tables_data, str):
                        try:
                            tables_data = json.loads(tables_data)
                        except:
                            tables_data = {}

                    if isinstance(tables_data, dict):
                        for table_name, rows in tables_data.items():
                            if rows and isinstance(rows, list) and len(rows) > 0:
                                try:
                                    print(f"    - {table_name}: {len(rows)} записей")
                                    for row in rows:
                                        columns = []
                                        values = []
                                        for col, val in row.items():
                                            if val is not None:  # Только не NULL значения
                                                columns.append(f'"{col}"')
                                                values.append(val)

                                        if columns:
                                            placeholders = ', '.join(['%s'] * len(values))
                                            query = f'INSERT INTO {schema_name}."{table_name}" ({", ".join(columns)}) VALUES ({placeholders})'
                                            cur.execute(query, values)
                                except Exception as e:
                                    print(f"      ⚠️  Ошибка вставки в {table_name}: {str(e)[:100]}")
                                    conn.rollback()

                    conn.commit()
                    print("  ✓ Данные восстановлены")

                # 4. Первичные ключи (makeid)
                if schema.get("makeid"):
                    print("  🔑 Создание первичных ключей...")
                    execute_sql_block(cur, schema["makeid"], "первичные ключи")
                    conn.commit()
                    print("  ✓ Первичные ключи созданы")

                # 5. Автоинкремент (autoinc)
                if schema.get("autoinc"):
                    print("  🔢 Настройка автоинкремента...")
                    execute_sql_block(cur, schema["autoinc"], "автоинкремент")
                    conn.commit()
                    print("  ✓ Автоинкремент настроен")

                # 6. Индексы (index)
                if schema.get("index"):
                    print("  📑 Создание индексов...")
                    execute_sql_block(cur, schema["index"], "индексы")
                    conn.commit()
                    print("  ✓ Индексы созданы")

                # 7. Ограничения, NOT NULL, DEFAULT, внешние ключи (tablewithrule)
                if schema.get("tablewithrule"):
                    print("  🔗 Применение правил таблиц...")
                    execute_sql_block(cur, schema["tablewithrule"], "правила таблиц")
                    conn.commit()
                    print("  ✓ Правила применены")

                # 8. Представления (view)
                if schema.get("view"):
                    print("  👁️  Создание представлений...")
                    execute_sql_block(cur, schema["view"], "представления")
                    conn.commit()
                    print("  ✓ Представления созданы")

                # 9. Функции (func)
                if schema.get("func"):
                    print("  ⚡ Создание функций...")
                    execute_sql_block(cur, schema["func"], "функции")
                    conn.commit()
                    print("  ✓ Функции созданы")

                # 10. Процедуры (procedure)
                if schema.get("procedure"):
                    print("  🔧 Создание процедур...")
                    execute_sql_block(cur, schema["procedure"], "процедуры")
                    conn.commit()
                    print("  ✓ Процедуры созданы")

                # 11. Триггеры (triggers)
                if schema.get("triggers"):
                    print("  ⚙️  Создание триггеров...")
                    execute_sql_block(cur, schema["triggers"], "триггеры")
                    conn.commit()
                    print("  ✓ Триггеры созданы")

                print(f"  ✅ Схема {schema_name} обработана успешно")

        print(f"\n{'=' * 60}")
        print("✅ ВОССТАНОВЛЕНИЕ УСПЕШНО ЗАВЕРШЕНО!")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return False
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("ИМПОРТ БАЗЫ ДАННЫХ ИЗ JSON ЭКСПОРТА")
    print("=" * 60)

    # Выбор JSON файла
    json_file = input("\nПуть к JSON файлу экспорта: ").strip()
    if not json_file:
        json_file = "/home/sergey/Documents/dbBCK/mozart_full_export.json"
        print(f"Используется путь по умолчанию: {json_file}")

    # Настройка подключения
    config = get_target_config()

    # Проверка подключения
    if not test_connection(config):
        return

    # Создание базы данных
    try:
        create_database_if_not_exists(config)
    except Exception:
        return

    # Подтверждение
    print("\n" + "=" * 60)
    print("ВНИМАНИЕ! Будет выполнено восстановление базы данных.")
    print(f"Целевой сервер: {config['host']}:{config['port']}")
    print(f"База данных: {config['database']}")
    confirm = input("Продолжить? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Операция отменена")
        return

    # Восстановление
    restore_from_json(json_file, config)


if __name__ == "__main__":
    main()