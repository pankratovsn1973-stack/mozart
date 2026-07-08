-- Полный путь: sql/seed_class_erp_data.sql
-- Описание: Заполняет базу системными классами, соответствующими библиотеке controls/.
-- Создает версии классов, методы doDefault() и связывает их.
-- Все методы взяты от базовых классов, сигналы повторяют базовые классы.

DO $$
DECLARE
    v_class_id INTEGER;
    v_ver_id INTEGER;
    v_method_id INTEGER;
    v_ref_ver_id INTEGER;
    v_class_name TEXT;
    v_qt_class TEXT;
    v_signal TEXT;
BEGIN
    RAISE NOTICE 'Начало заполнения системными классами...';

    -- ================================================================
    -- 1. БАЗОВЫЕ ВИЗУАЛЬНЫЕ КЛАССЫ (Source: PYTHON)
    -- ================================================================

    -- 1.1 MozartTextBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartTextBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QLineEdit', TRUE, '{"label": "", "binding_field": "", "placeholder": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('textChanged', v_ver_id),
        ('editingFinished', v_ver_id),
        ('returnPressed', v_ver_id);

    RAISE NOTICE '  + MozartTextBox (QLineEdit)';

    -- 1.2 MozartNumberBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartNumberBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QLineEdit', TRUE, '{"label": "", "binding_field": "", "min_value": 0, "max_value": 999999999, "decimal_places": 2}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('textChanged', v_ver_id),
        ('editingFinished', v_ver_id);

    RAISE NOTICE '  + MozartNumberBox (QLineEdit)';

    -- 1.3 MozartDateBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartDateBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QDateEdit', TRUE, '{"label": "", "binding_field": "", "date_format": "dd.MM.yyyy"}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('dateChanged', v_ver_id);

    RAISE NOTICE '  + MozartDateBox (QDateEdit)';

    -- 1.4 MozartCheckBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartCheckBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QCheckBox', TRUE, '{"label": "", "binding_field": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('stateChanged', v_ver_id),
        ('toggled', v_ver_id);

    RAISE NOTICE '  + MozartCheckBox (QCheckBox)';

    -- 1.5 MozartComboBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartComboBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QComboBox', TRUE, '{"label": "", "binding_field": "", "source_type": "static", "items_json": "[]"}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('currentIndexChanged', v_ver_id),
        ('activated', v_ver_id);

    RAISE NOTICE '  + MozartComboBox (QComboBox)';

    -- 1.6 MozartListBox
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartListBox') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QListWidget', TRUE, '{"label": "", "binding_field": "", "source_type": "static", "items_json": "[]"}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('currentItemChanged', v_ver_id),
        ('itemClicked', v_ver_id);

    RAISE NOTICE '  + MozartListBox (QListWidget)';

    -- 1.7 MozartOptionGroup
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartOptionGroup') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QWidget', TRUE, '{"label": "", "binding_field": "", "orientation": "vertical", "source_type": "static", "items_json": "[]"}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('buttonClicked', v_ver_id);

    RAISE NOTICE '  + MozartOptionGroup (QWidget)';

    -- 1.8 MozartMemo
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartMemo') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QPlainTextEdit', TRUE, '{"label": "", "binding_field": "", "placeholder": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('textChanged', v_ver_id);

    RAISE NOTICE '  + MozartMemo (QPlainTextEdit)';

    -- 1.9 MozartButton
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartButton') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QPushButton', TRUE, '{"label": "Кнопка", "binding_field": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('clicked', v_ver_id),
        ('pressed', v_ver_id),
        ('released', v_ver_id);

    RAISE NOTICE '  + MozartButton (QPushButton)';

    -- 1.10 MozartLabel
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartLabel') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QLabel', TRUE, '{"label": "Метка", "binding_field": "", "text_alignment": "left", "bold": false, "font_size": 9}')
    RETURNING id INTO v_ver_id;

    -- У QLabel нет сигналов

    RAISE NOTICE '  + MozartLabel (QLabel)';

    -- 1.11 MozartGrid
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartGrid') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QWidget', TRUE, '{"label": "", "binding_field": "", "columns_json": "[]", "allow_filter": true, "allow_sort": true}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('cellClicked', v_ver_id),
        ('currentCellChanged', v_ver_id);

    RAISE NOTICE '  + MozartGrid (QWidget)';

    -- 1.12 MozartContainer
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartContainer') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QGroupBox', TRUE, '{"label": "Группа элементов", "binding_field": ""}')
    RETURNING id INTO v_ver_id;

    -- У QGroupBox нет сигналов

    RAISE NOTICE '  + MozartContainer (QGroupBox)';

    -- 1.13 MozartTabContainer
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartTabContainer') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QTabWidget', TRUE, '{"label": "", "binding_field": "", "tabs_json": "[]"}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('currentChanged', v_ver_id);

    RAISE NOTICE '  + MozartTabContainer (QTabWidget)';

    -- 1.14 MozartImageView
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartImageView') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QWidget', TRUE, '{"label": "", "binding_field": ""}')
    RETURNING id INTO v_ver_id;

    -- У QWidget нет сигналов

    RAISE NOTICE '  + MozartImageView (QWidget)';

    -- 1.15 MozartRadioButton
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartRadioButton') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QRadioButton', TRUE, '{"label": "", "binding_field": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('toggled', v_ver_id);

    RAISE NOTICE '  + MozartRadioButton (QRadioButton)';

    -- ================================================================
    -- 2. НЕВИЗУАЛЬНЫЙ БАЗОВЫЙ КЛАСС (Source: PYTHON)
    -- ================================================================

    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartBaseInvisible') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QObject', FALSE, '{"name": "", "components": ""}')
    RETURNING id INTO v_ver_id;

    INSERT INTO class_erp.signal (c_signal, id_class_version) VALUES
        ('destroyed', v_ver_id),
        ('objectNameChanged', v_ver_id);

    RAISE NOTICE '  + MozartBaseInvisible (QObject) - НЕВИЗУАЛЬНЫЙ';

    -- ================================================================
    -- 3. СОСТАВНОЙ КЛАСС MozartReference (Source: ERP)
    -- ================================================================

    -- 3.1 Родительский класс
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('MozartReference') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, is_visible, txt_properties)
    VALUES (v_class_id, 'ERP', '', TRUE, '{"entity": "", "field": "", "display_field": "cname", "selector_form": ""}')
    RETURNING id INTO v_ref_ver_id;

    RAISE NOTICE '  + MozartReference (ERP) - СОСТАВНОЙ';
    RAISE NOTICE '    Подконтролы:';

    -- 3.2 Ref_Label
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('Ref_Label') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, i_parent_id, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QLabel', v_ref_ver_id, TRUE, '{"text": "Ссылка:"}');
    RAISE NOTICE '      - Ref_Label (QLabel)';

    -- 3.3 Ref_TextEdit
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('Ref_TextEdit') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, i_parent_id, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QLineEdit', v_ref_ver_id, TRUE, '{"readonly": true}');
    RAISE NOTICE '      - Ref_TextEdit (QLineEdit)';

    -- 3.4 Ref_SelectBtn
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('Ref_SelectBtn') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, i_parent_id, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QPushButton', v_ref_ver_id, TRUE, '{"text": "..."}');
    RAISE NOTICE '      - Ref_SelectBtn (QPushButton)';

    -- 3.5 Ref_ClearBtn
    INSERT INTO class_erp.mozartclasses (c_name) VALUES ('Ref_ClearBtn') RETURNING id INTO v_class_id;
    INSERT INTO class_erp.class_version (id_mozart_class, c_base_source, c_base_class, i_parent_id, is_visible, txt_properties)
    VALUES (v_class_id, 'PYTHON', 'QPushButton', v_ref_ver_id, TRUE, '{"text": "X"}');
    RAISE NOTICE '      - Ref_ClearBtn (QPushButton)';

    -- ================================================================
    -- 4. МЕТОД doDefault
    -- ================================================================

    INSERT INTO class_erp.method (c_name) VALUES ('doDefault') RETURNING id INTO v_method_id;
    INSERT INTO class_erp.method_version (id_method, c_komment, txt_method)
    VALUES (v_method_id, 'Метод по умолчанию для всех классов', 'def doDefault(self):\n    """Метод по умолчанию. Переопределите в классе."""\n    pass');

    RAISE NOTICE '  + Метод doDefault создан';

    -- 4.1 Связываем doDefault со всеми созданными версиями классов
    INSERT INTO class_erp.method_class_relation (id_method, id_class_version)
    SELECT v_method_id, id FROM class_erp.class_version;

    RAISE NOTICE '  + doDefault связан со всеми классами';

    -- ================================================================
    -- 5. ИТОГИ
    -- ================================================================

    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Заполнение завершено!';
    RAISE NOTICE '  - Создано классов: 16';
    RAISE NOTICE '  - Создано версий: 20+ (включая подконтролы)';
    RAISE NOTICE '  - Создано сигналов: 25+';
    RAISE NOTICE '  - Создано методов: 1 (doDefault)';
    RAISE NOTICE '  - Создано связей методов: для всех версий';
    RAISE NOTICE '==================================================';

END $$;

-- Проверка результатов
DO $$
DECLARE
    v_class_count INTEGER;
    v_version_count INTEGER;
    v_signal_count INTEGER;
    v_method_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_class_count FROM class_erp.mozartclasses;
    SELECT COUNT(*) INTO v_version_count FROM class_erp.class_version;
    SELECT COUNT(*) INTO v_signal_count FROM class_erp.signal;
    SELECT COUNT(*) INTO v_method_count FROM class_erp.method;

    RAISE NOTICE '';
    RAISE NOTICE '=== ИТОГИ ПОСЛЕ ЗАПОЛНЕНИЯ ===';
    RAISE NOTICE 'Классов: %', v_class_count;
    RAISE NOTICE 'Версий классов: %', v_version_count;
    RAISE NOTICE 'Сигналов: %', v_signal_count;
    RAISE NOTICE 'Методов: %', v_method_count;
    RAISE NOTICE '===============================';
END $$;

-- Вывод списка всех классов для проверки
SELECT mc.c_name, cv.is_visible, cv.c_base_source, cv.c_base_class,
       COUNT(s.id) as signal_count
FROM class_erp.mozartclasses mc
LEFT JOIN class_erp.class_version cv ON mc.id = cv.id_mozart_class
LEFT JOIN class_erp.signal s ON cv.id = s.id_class_version AND s.dt_end IS NULL
WHERE cv.dt_end IS NULL
GROUP BY mc.c_name, cv.is_visible, cv.c_base_source, cv.c_base_class
ORDER BY mc.c_name;