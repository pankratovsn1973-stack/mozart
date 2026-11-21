# /home/sergey/Documents/configurate/core/extend_bridges.py
"""
Автономный скрипт расширения таблицы class_property_bridge.
Реализует принцип ПЛОСКОЙ ИЗБЫТОЧНОСТИ: каждое свойство прописывается явно
для КАЖДОГО из 17 базовых Qt-классов.
Гарантирует отсутствие дубликатов по бизнес-ключу (c_base_class, property_key).
"""
import psycopg2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "mozart_erp",
    "user": "postgres",
    "password": "SQLSerIra"
}

# Полный список всех базовых Qt-классов, которые должны иметь свои мосты
ALL_QT_CLASSES = [
    "QComboBox", "QDialog", "QLabel", "QPlainTextEdit", "QWidget",
    "QMainWindow", "QListWidget", "QTreeView", "QGroupBox", "QPushButton",
    "QDateEdit", "QCheckBox", "QObject", "QRadioButton", "QTabWidget",
    "QTableWidget", "QLineEdit"
]


def extend_property_bridges():
    print("🚀 [BRIDGE EXTENDER] Старт полного расширения мостов свойств...")
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        print("✅ Подключение к базе данных установлено.")

        # ========================================================================
        # ШАГ 1: ОБНОВЛЕНИЕ CHECK-ОГРАНИЧЕНИЙ
        # ========================================================================
        print("🔧 Обновление ограничений editor_type и translation_strategy...")

        new_editor_types = "'text', 'number', 'boolean', 'color', 'choice', 'json', " \
                           "'font', 'image', 'list_items', 'entity_ref', 'field_ref', " \
                           "'form_ref', 'geometry'"
        new_strategies = "'DIRECT', 'CSS', 'GEOMETRY', 'CUSTOM', 'JSON_MAP'"

        cur.execute(f"""
            ALTER TABLE class_erp.class_property_bridge DROP CONSTRAINT IF EXISTS chk_property_editor_type;
            ALTER TABLE class_erp.class_property_bridge ADD CONSTRAINT chk_property_editor_type 
                CHECK (editor_type IN ({new_editor_types}));

            ALTER TABLE class_erp.class_property_bridge DROP CONSTRAINT IF EXISTS chk_property_strategy;
            ALTER TABLE class_erp.class_property_bridge ADD CONSTRAINT chk_property_strategy 
                CHECK (translation_strategy IN ({new_strategies}));
        """)
        print("✅ Ограничения успешно обновлены.")

        # ========================================================================
        # ШАГ 2: ДОБАВЛЕНИЕ НОВЫХ ПРАВИЛ МОСТОВ ДЛЯ ВСЕХ 17 КЛАССОВ
        # ========================================================================
        print("📥 Проверка и добавление правил мостов для всех базовых классов...")

        # Определяем универсальные свойства, которые должны быть у ВСЕХ визуальных контролов
        universal_props = [
            ('c_font', 'Шрифт', 'font', 'font', 'CUSTOM'),
            ('minimumSize', 'Мин. размер (W;H)', 'geometry', 'minimumSize', 'CUSTOM'),
            ('maximumSize', 'Макс. размер (W;H)', 'geometry', 'maximumSize', 'CUSTOM'),
            ('sizePolicy', 'Политика размера', 'choice', 'sizePolicy', 'DIRECT'),
            ('cursorShape', 'Курсор мыши', 'choice', 'cursor', 'DIRECT'),
            ('focusPolicy', 'Политика фокуса', 'choice', 'focusPolicy', 'DIRECT'),
            ('windowOpacity', 'Прозрачность (0.0-1.0)', 'number', 'windowOpacity', 'DIRECT'),
            ('styleSheet', 'Доп. CSS стили', 'text', 'styleSheet', 'DIRECT'),
        ]

        # Специфичные свойства для определенных типов
        specific_props_map = {
            'QWidget': [('c_background_image', 'Фоновое изображение', 'image', 'background-image', 'CSS')],
            'QLabel': [('pixmap', 'Картинка (pixmap)', 'image', 'pixmap', 'CUSTOM')],
            'QPushButton': [('icon', 'Иконка кнопки', 'image', 'icon', 'CUSTOM')],
            'QComboBox': [('items_list', 'Список вариантов', 'list_items', 'items_json', 'JSON_MAP')],
            'QListWidget': [('items_list', 'Список вариантов', 'list_items', 'items_json', 'JSON_MAP')],
            'QWidget': [],  # Будет объединено с универсальными
        }

        # ERP-специфика для QObject (наследуется всеми, но пишем явно в плоскую таблицу)
        erp_props = [
            ('binding_entity', 'Сущность-источник', 'entity_ref', 'binding_entity', 'DIRECT'),
            ('display_field', 'Поле отображения', 'field_ref', 'display_field', 'DIRECT'),
            ('selector_form', 'Форма выбора', 'form_ref', 'selector_form', 'DIRECT'),
            ('is_required', 'Обязательное поле', 'boolean', 'is_required', 'DIRECT'),
            ('validation_rule', 'Правило валидации (Regex)', 'text', 'validation_rule', 'DIRECT'),
        ]

        added_count = 0
        skipped_count = 0

        for qt_class in ALL_QT_CLASSES:
            props_to_add = list(universal_props)

            # Добавляем специфичные свойства
            if qt_class in specific_props_map:
                props_to_add.extend(specific_props_map[qt_class])

            # Добавляем ERP-свойства для всех классов (так как они наследуют QObject)
            props_to_add.extend(erp_props)

            for prop_key, label, editor, qt_target, strategy in props_to_add:
                # 🔍 ЖЕСТКАЯ ПРОВЕРКА НА ДУБЛИКАТЫ ПО БИЗНЕС-КЛЮЧУ
                cur.execute("""
                    SELECT id FROM class_erp.class_property_bridge 
                    WHERE c_base_class = %s AND property_key = %s
                """, (qt_class, prop_key))

                existing = cur.fetchone()
                if not existing:
                    # Генерируем новый ID динамически
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM class_erp.class_property_bridge")
                    new_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO class_erp.class_property_bridge 
                        (id, c_base_class, property_key, ui_label_ru, editor_type, qt_target, translation_strategy, dt_start)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (new_id, qt_class, prop_key, label, editor, qt_target, strategy))
                    added_count += 1
                else:
                    skipped_count += 1

        print(f"✅ Добавлено {added_count} новых правил. Пропущено {skipped_count} существующих.")

        # ========================================================================
        # ШАГ 3: ЗАПОЛНЕНИЕ СПРАВОЧНИКА allowed_values
        # Привязываем значения к РЕАЛЬНЫМ ID, найденным в БД
        # ========================================================================
        print(" Заполнение справочника допустимых значений...")

        allowed_values_map = {
            ('QWidget', 'sizePolicy'): [
                ('Fixed', 'Фиксированный', 1), ('Minimum', 'Минимальный', 2),
                ('Maximum', 'Максимальный', 3), ('Preferred', 'Предпочтительный', 4),
                ('Expanding', 'Расширяющийся', 5),
            ],
            ('QWidget', 'cursorShape'): [
                ('ArrowCursor', 'Стрелка', 1), ('IBeamCursor', 'Текстовый курсор', 2),
                ('WaitCursor', 'Ожидание', 3), ('CrossCursor', 'Перекрестие', 4),
                ('PointingHandCursor', 'Рука (ссылка)', 5),
            ],
            ('QWidget', 'focusPolicy'): [
                ('NoFocus', 'Нет фокуса', 1), ('TabFocus', 'Только Tab', 2),
                ('ClickFocus', 'Только клик', 3), ('StrongFocus', 'Tab + Клик', 4),
            ],
        }

        val_added = 0
        for (base_class, prop_key), values in allowed_values_map.items():
            # Находим реальный ID правила моста для этого конкретного класса
            cur.execute("""
                SELECT id FROM class_erp.class_property_bridge 
                WHERE c_base_class = %s AND property_key = %s
            """, (base_class, prop_key))

            bridge_row = cur.fetchone()
            if not bridge_row:
                continue

            real_bridge_id = bridge_row[0]
            for c_value, display_ru, sort_order in values:
                cur.execute("""
                    SELECT id FROM class_erp.class_property_allowed_values 
                    WHERE bridge_id = %s AND c_value = %s
                """, (real_bridge_id, c_value))

                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO class_erp.class_property_allowed_values 
                        (bridge_id, c_value, display_ru, i_sortorder)
                        VALUES (%s, %s, %s, %s)
                    """, (real_bridge_id, c_value, display_ru, sort_order))
                    val_added += 1

        print(f"✅ Добавлено {val_added} значений в справочник allowed_values.")
        print("\n🎉 [BRIDGE EXTENDER] Расширение мостов завершено успешно!")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("🔒 Соединение с БД закрыто.")


if __name__ == "__main__":
    extend_property_bridges()