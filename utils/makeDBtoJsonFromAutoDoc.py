import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
# сначала получаем джейсон из таблицы дампов на сервере
# --- Настройки ---
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "mozart_erp"
DB_USER = "postgres"
DB_PASSWORD = "SQLSerIra!"

OUTPUT_DIR = "/home/sergey/Documents/dbBCK"


# --- Конец настроек ---

def export_schema_dumps():
    """Экспорт всех дампов схем из autodoc.schema_dumps в JSON"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем все записи из таблицы дампов
            cur.execute("SELECT * FROM autodoc.schema_dumps ORDER BY id")
            dumps = cur.fetchall()

            if not dumps:
                print("Ошибка: таблица autodoc.schema_dumps пуста!")
                print("Сначала запустите процедуру autodoc.dump_schema_to_table для нужных схем")
                return

            # Формируем выходную структуру
            export_data = {
                "export_info": {
                    "source_database": DB_NAME,
                    "source_host": DB_HOST,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_schemas": len(dumps),
                    "schemas": [d["schema_name"] for d in dumps]
                },
                "schemas": []
            }

            for dump in dumps:
                schema_data = {
                    "schema_name": dump["schema_name"],
                    "cleartable": dump["cleartable"],
                    "makeid": dump["makeid"],
                    "autoinc": dump["autoinc"],
                    "index": dump["index"],
                    "tablewithrule": dump["tablewithrule"],
                    "view": dump["view"],
                    "procedure": dump["procedure"],
                    "func": dump["func"],
                    "triggers": dump["triggers"],
                    "jsondata": dump["jsondata"]  # Данные таблиц в JSON
                }
                export_data["schemas"].append(schema_data)

            # Сохраняем в JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(OUTPUT_DIR, f"mozart_full_export_{timestamp}.json")

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"✅ Экспорт успешно завершен!")
            print(f"📁 Файл: {output_file}")
            print(f"📊 Экспортировано схем: {len(dumps)}")
            print(f"📋 Схемы: {', '.join([d['schema_name'] for d in dumps])}")

            # Показываем размер файла
            file_size = os.path.getsize(output_file)
            if file_size > 1024 * 1024:
                print(f"📦 Размер: {file_size / (1024 * 1024):.2f} MB")
            else:
                print(f"📦 Размер: {file_size / 1024:.2f} KB")

    finally:
        conn.close()


if __name__ == "__main__":
    export_schema_dumps()