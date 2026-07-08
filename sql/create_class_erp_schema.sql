-- Полный путь: sql/create_class_erp_schema.sql
-- Описание: Скрипт создает схему class_erp и все необходимые таблицы
-- для хранения метаданных классов, их версий, методов и сигналов.
-- Реализует гибридное наследование (PYTHON/ERP) и поддержку составных объектов.
-- Используется в конфигураторе для управления абстрактными классами системы.

-- 1. Создание схемы
CREATE SCHEMA IF NOT EXISTS class_erp;

-- 2. Таблица абстрактных классов
CREATE TABLE class_erp.mozartclasses (
    id SERIAL PRIMARY KEY,
    c_name VARCHAR(255) NOT NULL UNIQUE,
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.mozartclasses IS 'Абстрактные классы системы (MozartTextBox, MozartButton и т.д.)';
COMMENT ON COLUMN class_erp.mozartclasses.c_name IS 'Имя класса (строго соответствует имени в controls/)';

-- 3. Таблица версий классов
CREATE TABLE class_erp.class_version (
    id SERIAL PRIMARY KEY,
    id_mozart_class INTEGER NOT NULL REFERENCES class_erp.mozartclasses(id) ON DELETE CASCADE,
    is_visible BOOLEAN DEFAULT TRUE,
    c_base_class VARCHAR(255),
    c_base_source VARCHAR(10) CHECK (c_base_source IN ('PYTHON', 'ERP')),
    i_base_class INTEGER REFERENCES class_erp.class_version(id),
    i_parent_id INTEGER REFERENCES class_erp.class_version(id),
    txt_properties TEXT DEFAULT '',
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.class_version IS 'Версии классов с реализацией и временем жизни';
COMMENT ON COLUMN class_erp.class_version.is_visible IS 'TRUE - визуальный класс, FALSE - невизуальный';
COMMENT ON COLUMN class_erp.class_version.c_base_source IS 'PYTHON - системный (Qt), ERP - пользовательский';
COMMENT ON COLUMN class_erp.class_version.i_base_class IS 'Приоритетная ссылка на родительскую версию';
COMMENT ON COLUMN class_erp.class_version.i_parent_id IS 'Для составных классов (часть целого)';

-- 4. Таблица свойств версии класса
CREATE TABLE class_erp.class_version_properties (
    id SERIAL PRIMARY KEY,
    id_class_version INTEGER NOT NULL REFERENCES class_erp.class_version(id) ON DELETE CASCADE,
    c_name VARCHAR(255) NOT NULL,
    type INTEGER DEFAULT 0,
    mask VARCHAR(255) DEFAULT '',
    source VARCHAR(255) DEFAULT '',
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.class_version_properties IS 'Детализированные свойства версий классов';
COMMENT ON COLUMN class_erp.class_version_properties.type IS '0 - текстовое, 1 - числовое, 2 - булево';
COMMENT ON COLUMN class_erp.class_version_properties.source IS 'Источник данных (entity.street, etc.)';

-- 5. Таблица методов (абстракция)
CREATE TABLE class_erp.method (
    id SERIAL PRIMARY KEY,
    c_name VARCHAR(255) NOT NULL UNIQUE,
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.method IS 'Абстрактные методы (doDefault, onLoad и т.д.)';

-- 6. Таблица версий методов (реализация)
CREATE TABLE class_erp.method_version (
    id SERIAL PRIMARY KEY,
    id_method INTEGER NOT NULL REFERENCES class_erp.method(id) ON DELETE CASCADE,
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL,
    c_komment TEXT DEFAULT '',
    txt_method TEXT DEFAULT ''
);

COMMENT ON TABLE class_erp.method_version IS 'Реализация методов с исходным кодом';

-- 7. Связь методов с версиями классов
CREATE TABLE class_erp.method_class_relation (
    id SERIAL PRIMARY KEY,
    id_method INTEGER NOT NULL REFERENCES class_erp.method(id) ON DELETE CASCADE,
    id_class_version INTEGER NOT NULL REFERENCES class_erp.class_version(id) ON DELETE CASCADE,
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.method_class_relation IS 'Один метод может быть в разных классах';

-- 8. Таблица сигналов
CREATE TABLE class_erp.signal (
    id SERIAL PRIMARY KEY,
    c_signal VARCHAR(255) NOT NULL,
    id_class_version INTEGER NOT NULL REFERENCES class_erp.class_version(id) ON DELETE CASCADE,
    id_method INTEGER REFERENCES class_erp.method(id) ON DELETE SET NULL,
    dt_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dt_end TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE class_erp.signal IS 'Сигналы классов с привязкой к методам';

-- 9. Индексы для производительности
CREATE INDEX idx_cv_mozart_id ON class_erp.class_version(id_mozart_class);
CREATE INDEX idx_cv_parent ON class_erp.class_version(i_parent_id);
CREATE INDEX idx_cv_base ON class_erp.class_version(i_base_class);
CREATE INDEX idx_mcr_class ON class_erp.method_class_relation(id_class_version);
CREATE INDEX idx_mcr_method ON class_erp.method_class_relation(id_method);
CREATE INDEX idx_signal_class ON class_erp.signal(id_class_version);
CREATE INDEX idx_signal_method ON class_erp.signal(id_method);

-- 10. Функция для мягкого удаления (установка dt_end = NOW())
CREATE OR REPLACE FUNCTION class_erp.f_set_dt_end()
RETURNS TRIGGER AS $$
BEGIN
    NEW.dt_end = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 11. Триггер для автоматического обновления dt_end при UPDATE
CREATE TRIGGER trg_soft_delete
BEFORE UPDATE OF dt_end ON class_erp.class_version
FOR EACH ROW
WHEN (OLD.dt_end IS NULL AND NEW.dt_end IS NOT NULL)
EXECUTE FUNCTION class_erp.f_set_dt_end();

-- 12. Проверка создания таблиц
DO $$
BEGIN
    RAISE NOTICE 'Схема class_erp создана успешно. Таблицы:';
    RAISE NOTICE '  - mozartclasses';
    RAISE NOTICE '  - class_version';
    RAISE NOTICE '  - class_version_properties';
    RAISE NOTICE '  - method';
    RAISE NOTICE '  - method_version';
    RAISE NOTICE '  - method_class_relation';
    RAISE NOTICE '  - signal';
END $$;