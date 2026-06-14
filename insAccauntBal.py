#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import json
import sys
from datetime import datetime

# =====================================================
# НАСТРОЙКИ (меняй здесь пути к файлам)
# =====================================================
RAS_FILE = "/home/sergey/Documents/configurate/plan/ras_accounts.json"
IFRS_FILE = "/home/sergey/Documents/configurate/plan/ifrs_accounts.json"
LOG_FILE = "/home/sergey/Documents/configurate/plan/import_log.json"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mozart_erp",
    "user": "postgres",
    "password": "SQLSerIra"
}


# =====================================================
# ФУНКЦИИ
# =====================================================

def log_message(log_data, step, message, level="INFO"):
    """Добавляет сообщение в лог"""
    log_data["steps"].append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "step": step,
        "message": message
    })
    print(f"[{level}] {step}: {message}")


def get_chart_id(cur, calias):
    """Возвращает instance_id плана счетов по calias"""
    cur.execute("""
        SELECT v.instanceid
        FROM ext.ext_chart_of_accounts coa
        JOIN data.entity_versions v ON v.id = coa.versionid
        WHERE coa.calias = %s
    """, (calias,))
    row = cur.fetchone()
    if not row:
        raise Exception(f"План счетов {calias} не найден в БД")
    return row[0]


def account_exists(cur, chart_id, code):
    """Проверяет, существует ли счёт в указанном плане"""
    cur.execute("""
        SELECT ca.id FROM ext.ext_chart_account ca
        WHERE ca.chart_id = %s AND ca.code = %s
    """, (chart_id, code))
    return cur.fetchone() is not None


def get_parent_instance_id(cur, chart_id, parent_code, account_instances):
    """Возвращает instance_id родительского счёта"""
    if not parent_code:
        return None

    # Сначала ищем в кэше текущей сессии
    if parent_code in account_instances:
        return account_instances[parent_code]

    # Затем в БД
    cur.execute("""
        SELECT i.id 
        FROM data.entity_instances i
        JOIN data.entity_versions v ON v.instanceid = i.id
        JOIN ext.ext_chart_account ca ON ca.versionid = v.id
        WHERE ca.chart_id = %s AND ca.code = %s
    """, (chart_id, parent_code))
    row = cur.fetchone()
    if row:
        return row[0]
    return None


def import_accounts(cur, chart_id, accounts_data, entity_type_id, chart_name, log_data):
    """Импортирует счета из JSON-данных"""
    account_instances = {}
    stats = {"new": 0, "skipped": 0, "errors": 0}
    errors = []

    for idx, acc in enumerate(accounts_data):
        code = acc.get("code")
        name = acc.get("name")
        acc_type = acc.get("type", "A")
        parent_code = acc.get("parent")
        comment = acc.get("comment")

        if not code or not name:
            msg = f"Строка {idx}: пропущена (нет code или name)"
            log_message(log_data, chart_name, msg, "WARNING")
            stats["skipped"] += 1
            continue

        # Проверяем существование
        if account_exists(cur, chart_id, code):
            msg = f"Пропущен: {code} — {name} (уже существует)"
            log_message(log_data, chart_name, msg, "INFO")
            stats["skipped"] += 1
            # Всё равно запоминаем для иерархии
            cur.execute("""
                SELECT i.id FROM data.entity_instances i
                JOIN data.entity_versions v ON v.instanceid = i.id
                JOIN ext.ext_chart_account ca ON ca.versionid = v.id
                WHERE ca.chart_id = %s AND ca.code = %s
            """, (chart_id, code))
            row = cur.fetchone()
            if row:
                account_instances[code] = row[0]
            continue

        try:
            # Определяем родителя
            parent_instance_id = get_parent_instance_id(cur, chart_id, parent_code, account_instances)

            # Создаём экземпляр
            cur.execute("""
                INSERT INTO data.entity_instances (entitytypeid, tdt_birth)
                VALUES (%s, now()) RETURNING id
            """, (entity_type_id,))
            instance_id = cur.fetchone()[0]

            # Создаём версию
            cur.execute("""
                INSERT INTO data.entity_versions (instanceid, parentinstanceid, cname, cversionstatus, tdt_start)
                VALUES (%s, %s, %s, 'Active', now()) RETURNING id
            """, (instance_id, parent_instance_id, f"{code} — {name}"))
            version_id = cur.fetchone()[0]

            # Создаём запись в ext-таблице
            if comment:
                cur.execute("""
                    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment)
                    VALUES (%s, %s, %s, %s, %s, true, %s)
                """, (version_id, chart_id, code, name, acc_type, comment))
            else:
                cur.execute("""
                    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active)
                    VALUES (%s, %s, %s, %s, %s, true)
                """, (version_id, chart_id, code, name, acc_type))

            account_instances[code] = instance_id
            stats["new"] += 1
            log_message(log_data, chart_name, f"Добавлен: {code} — {name}", "INFO")

        except Exception as e:
            stats["errors"] += 1
            error_msg = f"Ошибка при добавлении {code} — {name}: {str(e)}"
            log_message(log_data, chart_name, error_msg, "ERROR")
            errors.append({"code": code, "name": name, "error": str(e)})

    return stats, errors


def load_json_file(file_path, log_data):
    """Загружает JSON-файл с обработкой ошибок"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log_message(log_data, "FILE", f"Файл загружен: {file_path}", "INFO")
        return data
    except FileNotFoundError:
        log_message(log_data, "FILE", f"Файл не найден: {file_path}", "ERROR")
        return None
    except json.JSONDecodeError as e:
        log_message(log_data, "FILE", f"Ошибка парсинга JSON: {e}", "ERROR")
        return None


def save_log(log_data, log_file):
    """Сохраняет лог в JSON-файл"""
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Лог сохранён: {log_file}")
    except Exception as e:
        print(f"\n❌ Ошибка сохранения лога: {e}")


def main():
    # Инициализация лога
    log_data = {
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "results": {}
    }

    print("=" * 60)
    print("ИМПОРТ ПЛАНОВ СЧЕТОВ")
    print("=" * 60)

    # Проверка файлов
    log_message(log_data, "CHECK", f"Файл РСБУ: {RAS_FILE}")
    log_message(log_data, "CHECK", f"Файл МСФО: {IFRS_FILE}")

    ras_data = load_json_file(RAS_FILE, log_data)
    ifrs_data = load_json_file(IFRS_FILE, log_data)

    if not ras_data and not ifrs_data:
        log_message(log_data, "ERROR", "Нет данных для импорта", "ERROR")
        save_log(log_data, LOG_FILE)
        return

    # Подключение к БД
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()
        log_message(log_data, "DB", "Подключение к БД успешно", "INFO")

        # Получаем ID типа сущности CHART_ACCOUNT
        cur.execute("SELECT id FROM meta.entitytypes WHERE calias = 'CHART_ACCOUNT'")
        row = cur.fetchone()
        if not row:
            raise Exception("Тип сущности CHART_ACCOUNT не найден")
        entity_type_id = row[0]
        log_message(log_data, "DB", f"entitytype_id CHART_ACCOUNT = {entity_type_id}", "INFO")

        # Импорт РСБУ
        if ras_data:
            print("\n" + "=" * 60)
            print("ИМПОРТ РСБУ")
            print("=" * 60)

            chart_id = get_chart_id(cur, "RAS")
            log_message(log_data, "RAS", f"chart_id = {chart_id}", "INFO")

            stats, errors = import_accounts(cur, chart_id, ras_data, entity_type_id, "РСБУ", log_data)
            conn.commit()

            log_data["results"]["RAS"] = {
                "new": stats["new"],
                "skipped": stats["skipped"],
                "errors": stats["errors"],
                "error_details": errors
            }

            print(f"\n📊 РСБУ: добавлено {stats['new']}, пропущено {stats['skipped']}, ошибок {stats['errors']}")

        # Импорт МСФО
        if ifrs_data:
            print("\n" + "=" * 60)
            print("ИМПОРТ МСФО")
            print("=" * 60)

            chart_id = get_chart_id(cur, "IFRS")
            log_message(log_data, "IFRS", f"chart_id = {chart_id}", "INFO")

            stats, errors = import_accounts(cur, chart_id, ifrs_data, entity_type_id, "МСФО", log_data)
            conn.commit()

            log_data["results"]["IFRS"] = {
                "new": stats["new"],
                "skipped": stats["skipped"],
                "errors": stats["errors"],
                "error_details": errors
            }

            print(f"\n📊 МСФО: добавлено {stats['new']}, пропущено {stats['skipped']}, ошибок {stats['errors']}")

        # Итоговая статистика по БД
        cur.execute("""
            SELECT COUNT(*) FROM ext.ext_chart_account ca
            WHERE ca.chart_id = (SELECT v.instanceid FROM ext.ext_chart_of_accounts coa JOIN data.entity_versions v ON v.id = coa.versionid WHERE coa.calias = 'RAS')
        """)
        ras_total = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM ext.ext_chart_account ca
            WHERE ca.chart_id = (SELECT v.instanceid FROM ext.ext_chart_of_accounts coa JOIN data.entity_versions v ON v.id = coa.versionid WHERE coa.calias = 'IFRS')
        """)
        ifrs_total = cur.fetchone()[0]

        log_data["final_stats"] = {
            "РСБУ_total": ras_total,
            "МСФО_total": ifrs_total
        }

        print("\n" + "=" * 60)
        print("ИТОГО")
        print("=" * 60)
        print(f"РСБУ: {ras_total} счетов")
        print(f"МСФО: {ifrs_total} счетов")

        conn.commit()

    except Exception as e:
        log_message(log_data, "FATAL", str(e), "ERROR")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    log_data["end_time"] = datetime.now().isoformat()
    save_log(log_data, LOG_FILE)
    print("\n✅ ГОТОВО!")


if __name__ == "__main__":
    main()