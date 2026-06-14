-- ============================================================================
-- ХРАНИМАЯ ПРОЦЕДУРА: загрузка плана счетов РСБУ
-- ============================================================================

CREATE OR REPLACE PROCEDURE meta.load_chart_ras()
LANGUAGE plpgsql
AS $$
DECLARE
    v_chart_instance_id INTEGER;
    v_inst_id INTEGER;
    v_ver_id INTEGER;
    v_entity_chart_id INTEGER;
    v_entity_account_id INTEGER;
BEGIN
    -- Получаем ID типов сущностей
    SELECT id INTO v_entity_chart_id FROM meta.entitytypes WHERE calias = 'CHART_OF_ACCOUNTS';
    SELECT id INTO v_entity_account_id FROM meta.entitytypes WHERE calias = 'CHART_ACCOUNT';

    -- Создаём план РСБУ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth)
    VALUES (v_entity_chart_id, now())
    RETURNING id INTO v_inst_id;
    
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start)
    VALUES (v_inst_id, 'Российский план счетов (РСБУ)', 'Active', now())
    RETURNING id INTO v_ver_id;
    
    INSERT INTO ext_chart_of_accounts (versionid, cname, calias, is_active, mcomment)
    VALUES (v_ver_id, 'РСБУ', 'RAS', true, 
            'План счетов бухучёта, утв. Приказом Минфина РФ от 31.10.2000 №94н');
    
    v_chart_instance_id := v_inst_id;

    -- Создаём счета через INSERT'ы напрямую, без вложенной функции
    -- Каждый счёт = entity_instances + entity_versions + ext_chart_account

    -- РАЗДЕЛ I. ВНЕОБОРОТНЫЕ АКТИВЫ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01 — Основные средства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '01', 'Основные средства', 'A', true, 'Раздел I. Учёт основных средств');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01.01 — Основные средства в организации', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '01.01', 'Основные средства в организации', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01.02 — Выбытие основных средств', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '01.02', 'Выбытие основных средств', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '02 — Амортизация основных средств', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '02', 'Амортизация основных средств', 'P', true, 'Раздел I. Накопленная амортизация');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '02.01 — Амортизация собственных ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '02.01', 'Амортизация собственных ОС', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '04 — Нематериальные активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '04', 'Нематериальные активы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '05 — Амортизация НМА', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '05', 'Амортизация нематериальных активов', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '08 — Вложения во внеоборотные активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '08', 'Вложения во внеоборотные активы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '08.04 — Приобретение ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '08.04', 'Приобретение объектов основных средств', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '09 — Отложенные налоговые активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '09', 'Отложенные налоговые активы', 'A', true);

    -- РАЗДЕЛ II. ПРОИЗВОДСТВЕННЫЕ ЗАПАСЫ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10 — Материалы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '10', 'Материалы', 'A', true, 'Раздел II. Производственные запасы');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.01 — Сырьё и материалы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '10.01', 'Сырьё и материалы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.03 — Топливо', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '10.03', 'Топливо', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.05 — Запасные части', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '10.05', 'Запасные части', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.09 — Инвентарь и хоз.принадлежности', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '10.09', 'Инвентарь и хозяйственные принадлежности', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '19 — НДС по приобретённым ценностям', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '19', 'НДС по приобретённым ценностям', 'A', true);

    -- РАЗДЕЛ III. ЗАТРАТЫ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '20 — Основное производство', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '20', 'Основное производство', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '26 — Общехозяйственные расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '26', 'Общехозяйственные расходы', 'A', true);

    -- РАЗДЕЛ IV. ГОТОВАЯ ПРОДУКЦИЯ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '41 — Товары', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '41', 'Товары', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '43 — Готовая продукция', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '43', 'Готовая продукция', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '44 — Расходы на продажу', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '44', 'Расходы на продажу', 'A', true);

    -- РАЗДЕЛ V. ДЕНЕЖНЫЕ СРЕДСТВА
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '50 — Касса', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '50', 'Касса', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '51 — Расчётные счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '51', 'Расчётные счета', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '52 — Валютные счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '52', 'Валютные счета', 'A', true);

    -- РАЗДЕЛ VI. РАСЧЁТЫ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60 — Расчёты с поставщиками', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '60', 'Расчёты с поставщиками и подрядчиками', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60.01 — Расчёты с поставщиками', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '60.01', 'Расчёты с поставщиками', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60.02 — Авансы выданные', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '60.02', 'Авансы выданные', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62 — Расчёты с покупателями', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '62', 'Расчёты с покупателями и заказчиками', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62.01 — Расчёты с покупателями', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '62.01', 'Расчёты с покупателями', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62.02 — Авансы полученные', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '62.02', 'Авансы полученные', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '66 — Краткосрочные кредиты', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '66', 'Расчёты по краткосрочным кредитам и займам', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '67 — Долгосрочные кредиты', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '67', 'Расчёты по долгосрочным кредитам и займам', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68 — Расчёты по налогам', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '68', 'Расчёты по налогам и сборам', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68.01 — НДФЛ', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '68.01', 'НДФЛ', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68.02 — НДС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '68.02', 'НДС', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '69 — Расчёты по соц.страхованию', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '69', 'Расчёты по социальному страхованию и обеспечению', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '70 — Расчёты по оплате труда', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '70', 'Расчёты с персоналом по оплате труда', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '71 — Расчёты с подотчётными лицами', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '71', 'Расчёты с подотчётными лицами', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '76 — Расчёты с разными дебиторами/кредиторами', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '76', 'Расчёты с разными дебиторами и кредиторами', 'AP', true);

    -- РАЗДЕЛ VII. КАПИТАЛ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '80 — Уставный капитал', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '80', 'Уставный капитал', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '84 — Нераспределённая прибыль', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '84', 'Нераспределённая прибыль (непокрытый убыток)', 'AP', true);

    -- РАЗДЕЛ VIII. ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90 — Продажи', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '90', 'Продажи', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90.01 — Выручка', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '90.01', 'Выручка', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90.02 — Себестоимость продаж', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '90.02', 'Себестоимость продаж', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '91 — Прочие доходы и расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '91', 'Прочие доходы и расходы', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '99 — Прибыли и убытки', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_instance_id, '99', 'Прибыли и убытки', 'AP', true);

    -- ЗАБАЛАНСОВЫЕ СЧЕТА
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '001 — Арендованные ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '001', 'Арендованные основные средства', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '002 — ТМЦ на хранении', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '002', 'ТМЦ, принятые на ответственное хранение', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '006 — Бланки строгой отчётности', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '006', 'Бланки строгой отчётности', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '010 — Износ ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) VALUES (v_ver_id, v_chart_instance_id, '010', 'Износ основных средств', 'A', true, 'Забалансовый');

    RAISE NOTICE 'План счетов РСБУ загружен. Создано 45 счетов.';
END;
$$;


