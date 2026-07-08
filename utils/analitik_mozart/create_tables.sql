-- /home/sergey/Documents/configurate/utils/analitik_mozart/create_tables.sql
-- SQL скрипт для создания таблиц, индексов, функций и триггеров Аналитика Моцарт
-- Версия: 3.4 — исправлены проверки FOREIGN KEY

-- ============================================================
-- 1. СОЗДАНИЕ СХЕМЫ
-- ============================================================
CREATE SCHEMA IF NOT EXISTS mozart;

-- ============================================================
-- 2. СОЗДАНИЕ ТАБЛИЦ С ПРОВЕРКОЙ
-- ============================================================

-- 2.1. Единая таблица сущностей
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_entity') THEN
        CREATE TABLE mozart.tbl_entity (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type_id INTEGER NOT NULL,
            c_name VARCHAR(500) NOT NULL,
            parent_id UUID,
            dt_start TIMESTAMP NOT NULL DEFAULT NOW(),
            dt_end TIMESTAMP,
            n_old_version UUID,
            is_active BOOLEAN DEFAULT TRUE,
            m_comment TEXT,
            n_order INTEGER DEFAULT 0,
            n_relise VARCHAR(50),
            t_blobskript TEXT,
            j_data JSONB
        );
        RAISE NOTICE '✅ Таблица tbl_entity создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_entity уже существует';
    END IF;
END $$;

-- 2.2. Задачи
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_task') THEN
        CREATE TABLE mozart.tbl_task (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_number VARCHAR(50) NOT NULL UNIQUE,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'draft',
            parent_task_id UUID,
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            deadline TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            dt_start TIMESTAMP DEFAULT NOW(),
            dt_end TIMESTAMP
        );
        RAISE NOTICE '✅ Таблица tbl_task создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_task уже существует';
    END IF;
END $$;

-- 2.3. Кандидаты задач
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_task_candidate') THEN
        CREATE TABLE mozart.tbl_task_candidate (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL,
            target_id UUID NOT NULL,
            impact_type VARCHAR(20) NOT NULL,
            justification TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        RAISE NOTICE '✅ Таблица tbl_task_candidate создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_task_candidate уже существует';
    END IF;
END $$;

-- 2.4. Архитектурные решения
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_arch_solution') THEN
        CREATE TABLE mozart.tbl_arch_solution (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL,
            solution_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            approach VARCHAR(50) DEFAULT 'monolith',
            tech_stack JSONB,
            depends_on UUID,
            replaces UUID,
            status VARCHAR(20) DEFAULT 'proposed',
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            dt_start TIMESTAMP DEFAULT NOW(),
            dt_end TIMESTAMP
        );
        RAISE NOTICE '✅ Таблица tbl_arch_solution создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_arch_solution уже существует';
    END IF;
END $$;

-- 2.5. Кандидаты архитектуры
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_arch_candidate') THEN
        CREATE TABLE mozart.tbl_arch_candidate (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            arch_solution_id UUID NOT NULL,
            target_id UUID NOT NULL,
            impact_type VARCHAR(20) NOT NULL,
            justification TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        RAISE NOTICE '✅ Таблица tbl_arch_candidate создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_arch_candidate уже существует';
    END IF;
END $$;

-- 2.6. Планы
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_plan') THEN
        CREATE TABLE mozart.tbl_plan (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            arch_solution_id UUID NOT NULL,
            plan_name VARCHAR(255) NOT NULL,
            description TEXT,
            step_order INTEGER NOT NULL,
            depends_on UUID,
            assignee VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            dt_start TIMESTAMP DEFAULT NOW(),
            dt_end TIMESTAMP
        );
        RAISE NOTICE '✅ Таблица tbl_plan создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_plan уже существует';
    END IF;
END $$;

-- 2.7. Кандидаты планов
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_plan_candidate') THEN
        CREATE TABLE mozart.tbl_plan_candidate (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL,
            target_id UUID NOT NULL,
            impact_type VARCHAR(20) NOT NULL,
            justification TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        RAISE NOTICE '✅ Таблица tbl_plan_candidate создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_plan_candidate уже существует';
    END IF;
END $$;

-- 2.8. Действия
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_action') THEN
        CREATE TABLE mozart.tbl_action (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL,
            action_order INTEGER NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            change_description TEXT NOT NULL,
            new_value JSONB,
            precondition TEXT,
            postcondition TEXT,
            executed_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            dt_start TIMESTAMP DEFAULT NOW(),
            dt_end TIMESTAMP
        );
        RAISE NOTICE '✅ Таблица tbl_action создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_action уже существует';
    END IF;
END $$;

-- 2.9. Результаты действий
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_action_result') THEN
        CREATE TABLE mozart.tbl_action_result (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            action_id UUID NOT NULL,
            target_id UUID NOT NULL,
            change_type VARCHAR(20) NOT NULL,
            old_snapshot JSONB,
            new_snapshot JSONB,
            new_version_id UUID,
            executed_at TIMESTAMP DEFAULT NOW()
        );
        RAISE NOTICE '✅ Таблица tbl_action_result создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_action_result уже существует';
    END IF;
END $$;

-- 2.10. Граф вызовов
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = 'mozart' AND table_name = 'tbl_call') THEN
        CREATE TABLE mozart.tbl_call (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            caller_entity_id UUID NOT NULL,
            callee_name VARCHAR(255) NOT NULL,
            callee_type VARCHAR(20) DEFAULT 'unknown',
            line_number INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            dt_start TIMESTAMP DEFAULT NOW(),
            dt_end TIMESTAMP
        );
        RAISE NOTICE '✅ Таблица tbl_call создана';
    ELSE
        RAISE NOTICE '✅ Таблица tbl_call уже существует';
    END IF;
END $$;

-- ============================================================
-- 3. ДОБАВЛЕНИЕ ВНЕШНИХ КЛЮЧЕЙ (с проверкой на существование)
-- ============================================================

DO $$
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    -- Для tbl_entity
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_entity'
        AND constraint_name = 'fk_entity_parent'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_entity ADD CONSTRAINT fk_entity_parent FOREIGN KEY (parent_id) REFERENCES mozart.tbl_entity(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_entity_parent';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_entity'
        AND constraint_name = 'fk_entity_old_version'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_entity ADD CONSTRAINT fk_entity_old_version FOREIGN KEY (n_old_version) REFERENCES mozart.tbl_entity(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_entity_old_version';
    END IF;

    -- Для tbl_task
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_task'
        AND constraint_name = 'fk_task_parent'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_task ADD CONSTRAINT fk_task_parent FOREIGN KEY (parent_task_id) REFERENCES mozart.tbl_task(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_task_parent';
    END IF;

    -- Для tbl_task_candidate
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_task_candidate'
        AND constraint_name = 'fk_task_candidate_task'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_task_candidate ADD CONSTRAINT fk_task_candidate_task FOREIGN KEY (task_id) REFERENCES mozart.tbl_task(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_task_candidate_task';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_task_candidate'
        AND constraint_name = 'fk_task_candidate_target'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_task_candidate ADD CONSTRAINT fk_task_candidate_target FOREIGN KEY (target_id) REFERENCES mozart.tbl_entity(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_task_candidate_target';
    END IF;

    -- Для tbl_arch_solution
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_arch_solution'
        AND constraint_name = 'fk_arch_task'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_arch_solution ADD CONSTRAINT fk_arch_task FOREIGN KEY (task_id) REFERENCES mozart.tbl_task(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_arch_task';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_arch_solution'
        AND constraint_name = 'fk_arch_depends'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_arch_solution ADD CONSTRAINT fk_arch_depends FOREIGN KEY (depends_on) REFERENCES mozart.tbl_arch_solution(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_arch_depends';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_arch_solution'
        AND constraint_name = 'fk_arch_replaces'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_arch_solution ADD CONSTRAINT fk_arch_replaces FOREIGN KEY (replaces) REFERENCES mozart.tbl_arch_solution(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_arch_replaces';
    END IF;

    -- Для tbl_arch_candidate
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_arch_candidate'
        AND constraint_name = 'fk_arch_candidate_arch'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_arch_candidate ADD CONSTRAINT fk_arch_candidate_arch FOREIGN KEY (arch_solution_id) REFERENCES mozart.tbl_arch_solution(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_arch_candidate_arch';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_arch_candidate'
        AND constraint_name = 'fk_arch_candidate_target'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_arch_candidate ADD CONSTRAINT fk_arch_candidate_target FOREIGN KEY (target_id) REFERENCES mozart.tbl_entity(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_arch_candidate_target';
    END IF;

    -- Для tbl_plan
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_plan'
        AND constraint_name = 'fk_plan_arch'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_plan ADD CONSTRAINT fk_plan_arch FOREIGN KEY (arch_solution_id) REFERENCES mozart.tbl_arch_solution(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_plan_arch';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_plan'
        AND constraint_name = 'fk_plan_depends'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_plan ADD CONSTRAINT fk_plan_depends FOREIGN KEY (depends_on) REFERENCES mozart.tbl_plan(id) ON DELETE SET NULL';
        RAISE NOTICE '✅ Добавлен FK fk_plan_depends';
    END IF;

    -- Для tbl_plan_candidate
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_plan_candidate'
        AND constraint_name = 'fk_plan_candidate_plan'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_plan_candidate ADD CONSTRAINT fk_plan_candidate_plan FOREIGN KEY (plan_id) REFERENCES mozart.tbl_plan(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_plan_candidate_plan';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_plan_candidate'
        AND constraint_name = 'fk_plan_candidate_target'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_plan_candidate ADD CONSTRAINT fk_plan_candidate_target FOREIGN KEY (target_id) REFERENCES mozart.tbl_entity(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_plan_candidate_target';
    END IF;

    -- Для tbl_action
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_action'
        AND constraint_name = 'fk_action_plan'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_action ADD CONSTRAINT fk_action_plan FOREIGN KEY (plan_id) REFERENCES mozart.tbl_plan(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_action_plan';
    END IF;

    -- Для tbl_action_result
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_action_result'
        AND constraint_name = 'fk_result_action'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_action_result ADD CONSTRAINT fk_result_action FOREIGN KEY (action_id) REFERENCES mozart.tbl_action(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_result_action';
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_action_result'
        AND constraint_name = 'fk_result_target'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_action_result ADD CONSTRAINT fk_result_target FOREIGN KEY (target_id) REFERENCES mozart.tbl_entity(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_result_target';
    END IF;

    -- Для tbl_call
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = 'mozart'
        AND table_name = 'tbl_call'
        AND constraint_name = 'fk_call_caller'
    ) INTO constraint_exists;
    IF NOT constraint_exists THEN
        EXECUTE 'ALTER TABLE mozart.tbl_call ADD CONSTRAINT fk_call_caller FOREIGN KEY (caller_entity_id) REFERENCES mozart.tbl_entity(id) ON DELETE CASCADE';
        RAISE NOTICE '✅ Добавлен FK fk_call_caller';
    END IF;

END $$;



-- Добавляем поле, если его нет
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'mozart'
        AND table_name = 'tbl_entity'
        AND column_name = 't_full_text'
    ) THEN
        ALTER TABLE mozart.tbl_entity ADD COLUMN t_full_text TEXT;
        RAISE NOTICE '✅ Добавлено поле t_full_text в tbl_entity';
    END IF;
END $$;
-- ============================================================
-- 4. ИНДЕКСЫ
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_entity_type_id ON mozart.tbl_entity(type_id);
CREATE INDEX IF NOT EXISTS idx_entity_parent_id ON mozart.tbl_entity(parent_id);
CREATE INDEX IF NOT EXISTS idx_entity_dt_start ON mozart.tbl_entity(dt_start);
CREATE INDEX IF NOT EXISTS idx_entity_dt_end ON mozart.tbl_entity(dt_end);
CREATE INDEX IF NOT EXISTS idx_entity_name ON mozart.tbl_entity(c_name);
CREATE INDEX IF NOT EXISTS idx_entity_parent_type ON mozart.tbl_entity(parent_id, type_id);

CREATE INDEX IF NOT EXISTS idx_task_number ON mozart.tbl_task(task_number);
CREATE INDEX IF NOT EXISTS idx_task_status ON mozart.tbl_task(status);
CREATE INDEX IF NOT EXISTS idx_task_priority ON mozart.tbl_task(priority);

CREATE INDEX IF NOT EXISTS idx_task_candidate_task ON mozart.tbl_task_candidate(task_id);
CREATE INDEX IF NOT EXISTS idx_task_candidate_target ON mozart.tbl_task_candidate(target_id);

CREATE INDEX IF NOT EXISTS idx_arch_task ON mozart.tbl_arch_solution(task_id);
CREATE INDEX IF NOT EXISTS idx_arch_status ON mozart.tbl_arch_solution(status);

CREATE INDEX IF NOT EXISTS idx_arch_candidate_arch ON mozart.tbl_arch_candidate(arch_solution_id);
CREATE INDEX IF NOT EXISTS idx_arch_candidate_target ON mozart.tbl_arch_candidate(target_id);

CREATE INDEX IF NOT EXISTS idx_plan_arch ON mozart.tbl_plan(arch_solution_id);
CREATE INDEX IF NOT EXISTS idx_plan_status ON mozart.tbl_plan(status);
CREATE INDEX IF NOT EXISTS idx_plan_step ON mozart.tbl_plan(step_order);

CREATE INDEX IF NOT EXISTS idx_plan_candidate_plan ON mozart.tbl_plan_candidate(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_candidate_target ON mozart.tbl_plan_candidate(target_id);

CREATE INDEX IF NOT EXISTS idx_action_plan ON mozart.tbl_action(plan_id);
CREATE INDEX IF NOT EXISTS idx_action_type ON mozart.tbl_action(action_type);

CREATE INDEX IF NOT EXISTS idx_result_action ON mozart.tbl_action_result(action_id);
CREATE INDEX IF NOT EXISTS idx_result_target ON mozart.tbl_action_result(target_id);

CREATE INDEX IF NOT EXISTS idx_call_callee ON mozart.tbl_call(callee_name);
CREATE INDEX IF NOT EXISTS idx_call_caller ON mozart.tbl_call(caller_entity_id);

-- ============================================================
-- 5. ХРАНИМЫЕ ФУНКЦИИ
-- ============================================================

-- 5.1. Получить дерево сущностей
CREATE OR REPLACE FUNCTION mozart.get_entity_tree(
    p_root_id UUID,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    id UUID,
    type_id INTEGER,
    c_name VARCHAR,
    parent_id UUID,
    level INTEGER,
    path TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE tree AS (
        SELECT
            e.id, e.type_id, e.c_name, e.parent_id,
            0 as level,
            e.c_name::TEXT as path,
            e.n_order
        FROM mozart.tbl_entity e
        WHERE e.id = p_root_id
          AND e.dt_start <= p_dt
          AND (e.dt_end IS NULL OR e.dt_end > p_dt)

        UNION ALL

        SELECT
            e.id, e.type_id, e.c_name, e.parent_id,
            tree.level + 1,
            tree.path || ' → ' || e.c_name,
            e.n_order
        FROM mozart.tbl_entity e
        JOIN tree ON e.parent_id = tree.id
        WHERE e.dt_start <= p_dt
          AND (e.dt_end IS NULL OR e.dt_end > p_dt)
    )
    SELECT id, type_id, c_name, parent_id, level, path
    FROM tree
    ORDER BY path, n_order;
END;
$$;

-- 5.2. Получить сущность на момент времени
CREATE OR REPLACE FUNCTION mozart.get_entity_at_time(
    p_entity_id UUID,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    id UUID,
    type_id INTEGER,
    c_name VARCHAR,
    parent_id UUID,
    dt_start TIMESTAMP,
    dt_end TIMESTAMP,
    is_active BOOLEAN,
    m_comment TEXT,
    n_order INTEGER,
    n_relise VARCHAR,
    t_blobskript TEXT,
    j_data JSONB
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id, e.type_id, e.c_name, e.parent_id,
        e.dt_start, e.dt_end, e.is_active,
        e.m_comment, e.n_order, e.n_relise,
        e.t_blobskript, e.j_data
    FROM mozart.tbl_entity e
    WHERE e.id = p_entity_id
      AND e.dt_start <= p_dt
      AND (e.dt_end IS NULL OR e.dt_end > p_dt);
END;
$$;

-- 5.3. Получить все сущности по типу
CREATE OR REPLACE FUNCTION mozart.get_entities_by_type(
    p_type_id INTEGER,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    id UUID,
    c_name VARCHAR,
    parent_id UUID,
    m_comment TEXT,
    t_blobskript TEXT,
    j_data JSONB
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id, e.c_name, e.parent_id,
        e.m_comment, e.t_blobskript, e.j_data
    FROM mozart.tbl_entity e
    WHERE e.type_id = p_type_id
      AND e.dt_start <= p_dt
      AND (e.dt_end IS NULL OR e.dt_end > p_dt)
    ORDER BY e.c_name;
END;
$$;

-- 5.4. Поиск использований
CREATE OR REPLACE FUNCTION mozart.find_usages(
    p_entity_id UUID,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    caller_id UUID,
    caller_name VARCHAR,
    caller_type INTEGER,
    line_number INTEGER,
    dt_start TIMESTAMP
) LANGUAGE plpgsql AS $$
DECLARE
    v_entity_name TEXT;
BEGIN
    SELECT c_name INTO v_entity_name
    FROM mozart.tbl_entity
    WHERE id = p_entity_id
      AND dt_start <= p_dt
      AND (dt_end IS NULL OR dt_end > p_dt);

    IF v_entity_name IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        e.id as caller_id,
        e.c_name as caller_name,
        e.type_id as caller_type,
        c.line_number,
        c.dt_start
    FROM mozart.tbl_call c
    JOIN mozart.tbl_entity e ON c.caller_entity_id = e.id
    WHERE c.callee_name = v_entity_name
      AND c.dt_start <= p_dt
      AND (c.dt_end IS NULL OR c.dt_end > p_dt)
      AND e.dt_start <= p_dt
      AND (e.dt_end IS NULL OR e.dt_end > p_dt)
    ORDER BY c.dt_start DESC;
END;
$$;

-- 5.5. Рекурсивный поиск использований
CREATE OR REPLACE FUNCTION mozart.find_usage_chain(
    p_entity_id UUID,
    p_max_depth INTEGER DEFAULT 5,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    level INTEGER,
    caller_id UUID,
    caller_name VARCHAR,
    caller_type INTEGER,
    path TEXT
) LANGUAGE plpgsql AS $$
DECLARE
    v_entity_name TEXT;
BEGIN
    SELECT c_name INTO v_entity_name
    FROM mozart.tbl_entity
    WHERE id = p_entity_id
      AND dt_start <= p_dt
      AND (dt_end IS NULL OR dt_end > p_dt);

    IF v_entity_name IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    WITH RECURSIVE usage_tree AS (
        SELECT
            1 as level,
            e.id as caller_id,
            e.c_name as caller_name,
            e.type_id as caller_type,
            ARRAY[e.c_name]::TEXT[] as path
        FROM mozart.tbl_call c
        JOIN mozart.tbl_entity e ON c.caller_entity_id = e.id
        WHERE c.callee_name = v_entity_name
          AND c.dt_start <= p_dt
          AND (c.dt_end IS NULL OR c.dt_end > p_dt)
          AND e.dt_start <= p_dt
          AND (e.dt_end IS NULL OR e.dt_end > p_dt)

        UNION ALL

        SELECT
            ut.level + 1,
            e2.id,
            e2.c_name,
            e2.type_id,
            ut.path || ARRAY[e2.c_name]
        FROM usage_tree ut
        JOIN mozart.tbl_call c2 ON c2.callee_name = ut.caller_name
        JOIN mozart.tbl_entity e2 ON c2.caller_entity_id = e2.id
        WHERE ut.level < p_max_depth
          AND c2.dt_start <= p_dt
          AND (c2.dt_end IS NULL OR c2.dt_end > p_dt)
          AND e2.dt_start <= p_dt
          AND (e2.dt_end IS NULL OR e2.dt_end > p_dt)
          AND NOT (e2.c_name = ANY(ut.path))
    )
    SELECT * FROM usage_tree ORDER BY level, caller_name;
END;
$$;

-- 5.6. Получить все версии сущности
CREATE OR REPLACE FUNCTION mozart.get_entity_versions(
    p_entity_id UUID
)
RETURNS TABLE(
    id UUID,
    dt_start TIMESTAMP,
    dt_end TIMESTAMP,
    is_active BOOLEAN,
    c_name VARCHAR,
    type_id INTEGER,
    n_relise VARCHAR
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE versions AS (
        SELECT
            e.id, e.dt_start, e.dt_end, e.is_active,
            e.c_name, e.type_id, e.n_relise
        FROM mozart.tbl_entity e
        WHERE e.id = p_entity_id

        UNION ALL

        SELECT
            e.id, e.dt_start, e.dt_end, e.is_active,
            e.c_name, e.type_id, e.n_relise
        FROM mozart.tbl_entity e
        JOIN versions v ON e.n_old_version = v.id
    )
    SELECT * FROM versions ORDER BY dt_start DESC;
END;
$$;

-- 5.7. Получить сущности связанные с задачей
CREATE OR REPLACE FUNCTION mozart.get_task_entities(
    p_task_id UUID,
    p_dt TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    entity_id UUID,
    entity_name VARCHAR,
    entity_type INTEGER,
    impact_type VARCHAR,
    justification TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id as entity_id,
        e.c_name as entity_name,
        e.type_id as entity_type,
        tc.impact_type,
        tc.justification
    FROM mozart.tbl_task_candidate tc
    JOIN mozart.tbl_entity e ON tc.target_id = e.id
    WHERE tc.task_id = p_task_id
      AND e.dt_start <= p_dt
      AND (e.dt_end IS NULL OR e.dt_end > p_dt);
END;
$$;

-- ============================================================
-- 6. ТРИГГЕРЫ
-- ============================================================

-- 6.1. Триггер для is_active
CREATE OR REPLACE FUNCTION mozart.update_entity_is_active()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.dt_end IS NULL THEN
        NEW.is_active := TRUE;
    ELSE
        NEW.is_active := FALSE;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_entity_is_active ON mozart.tbl_entity;
CREATE TRIGGER trg_entity_is_active
    BEFORE INSERT OR UPDATE OF dt_end ON mozart.tbl_entity
    FOR EACH ROW
    EXECUTE FUNCTION mozart.update_entity_is_active();

-- 6.2. Триггер для dt_start
CREATE OR REPLACE FUNCTION mozart.set_entity_dt_start()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.dt_start IS NULL THEN
        NEW.dt_start := NOW();
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_entity_dt_start ON mozart.tbl_entity;
CREATE TRIGGER trg_entity_dt_start
    BEFORE INSERT ON mozart.tbl_entity
    FOR EACH ROW
    EXECUTE FUNCTION mozart.set_entity_dt_start();

-- ============================================================
-- 7. ИНИЦИАЛИЗАЦИЯ (корневой каталог)
-- ============================================================

INSERT INTO mozart.tbl_entity (id, type_id, c_name, j_data)
SELECT
    '00000000-0000-0000-0000-000000000001',
    1,
    'Корень проекта',
    '{"full_path": "/"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM mozart.tbl_entity
    WHERE type_id = 1 AND c_name = 'Корень проекта'
);

-- ============================================================
-- 8. ИНФОРМАЦИЯ О ВЫПОЛНЕНИИ
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ СХЕМА mozart ГОТОВА К РАБОТЕ!';
    RAISE NOTICE '============================================';
    RAISE NOTICE '📊 Таблицы:';
    RAISE NOTICE '   - tbl_entity (главная)';
    RAISE NOTICE '   - tbl_task (задачи)';
    RAISE NOTICE '   - tbl_task_candidate';
    RAISE NOTICE '   - tbl_arch_solution';
    RAISE NOTICE '   - tbl_arch_candidate';
    RAISE NOTICE '   - tbl_plan';
    RAISE NOTICE '   - tbl_plan_candidate';
    RAISE NOTICE '   - tbl_action';
    RAISE NOTICE '   - tbl_action_result';
    RAISE NOTICE '   - tbl_call';
    RAISE NOTICE '📦 Хранимые функции: 7 шт.';
    RAISE NOTICE '🔗 Индексы: созданы';
    RAISE NOTICE '⚡ Триггеры: созданы';
    RAISE NOTICE '============================================';
END $$;