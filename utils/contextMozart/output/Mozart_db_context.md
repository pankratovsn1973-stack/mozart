# Карта БД Mozart ERP

- **Хост:** `localhost:5432`
- **БД:** `mozart_erp`
- **Сгенерирован:** 2026-10-25 21:29:32


## Сводная статистика

| Показатель | Значение |
|------------|----------|
| Классы сущностей | 12 |
| Типы сущностей | 34 |
| Поля | 224 |
| Роли вложений | 10 |
| Связи мастер-деталь | 18 |
| Low-code классы | 34 |
| Версии классов | 34 |
| Мосты свойств | 388 |
| Формы | 1 |
| Элементы форм | 3 |
| Ключей переводов | 553 |


## Классы сущностей (`meta.entity_classes`)

| ID | Alias | Название | Описание |
|----|-------|----------|----------|
| 1 | `DICT` | Справочник | Простые и иерархические справочники (опционально с версионностью) |
| 2 | `DOC` | Документ | Объекты, имеющие подчинённые таблицы, поддерживающие маршрутизацию и задания |
| 3 | `CALC` | Расчёт/алгоритм | Хранит ссылки на исполняемые процедуры или скрипты |
| 4 | `ACTION` | Действие/операция | Перечень активностей пользователей/процессов, может иметь проводки |
| 5 | `ACCOUNT` | Счёт | Объекты учёта (например, здание котельной, монитор) с признаком дебета/кредита |
| 6 | `CHART` | План счетов | Совокупность счетов бухгалтерского учёта |
| 7 | `ASPECT` | Ипостась | Качественная или количественная характеристика счёта |
| 8 | `ORG` | Оргструктура | Организационные единицы и структуры предприятий |
| 9 | `PERSON` | Персоны | Физические лица, используемые для связи с пользователями |
| 10 | `ADDRESS` | Адрес | Структурированный адрес с поддержкой ГАР и иерархического выбора |
| 11 | `REGISTER` | Регистр | Регистры накопления (остатки/обороты), сведений, бухгалтерские регистры |
| 17 | `STAFF_POSITION` | !tst! Штатная единица | Привязка должности к подразделению и человеку (тестовый) |

## Типы сущностей (`meta.entitytypes`)

| ID | Alias | Название | Базовый класс | Класс | Версионная | Системная |
|----|-------|----------|---------------|-------|------------|-----------|
| 10 | `БИК_банков` | BIK | — | Справочник | ✅ |  |
| 7 | `накладная` | Invoice | DOC | Документ | ✅ |  |
| 8 | `стр_накл` | Invoice_line | — | Справочник | ✅ |  |
| 82 | `ACCOUNT` | account | ACCOUNT | Счёт | ✅ |  |
| 87 | `ACCOUNT_TURNOVER` | account_turnover | DICT | Справочник |  |  |
| 84 | `ASPECT` | aspect | ASPECT | Ипостась | ✅ |  |
| 85 | `ASPECT_CHART_BINDING` | aspect_chart_binding | DICT | Справочник | ✅ |  |
| 86 | `ASPECT_DAILY` | aspect_daily | DICT | Справочник |  |  |
| 83 | `ASSET_MOVEMENT` | asset_movement | DICT | Справочник | ✅ |  |
| 70 | `ASSIGNMENT` | assignment | DOC | Документ | ✅ | ✅ |
| 71 | `ASSIGNMENT_REPORT` | assignment_report | DOC | Документ | ✅ | ✅ |
| 66 | `ASSIGNMENT_TEMPLATE` | assignment_template | DICT | Справочник | ✅ |  |
| 80 | `CHART_ACCOUNT` | chart_account | DICT | Справочник | ✅ |  |
| 81 | `CHART_ACCOUNT_COMMENT` | chart_account_comment | DICT | Справочник | ✅ |  |
| 79 | `CHART_OF_ACCOUNTS` | chart_of_accounts | CHART | План счетов | ✅ |  |
| 2 | `города` | city | Справочник | Справочник | ✅ |  |
| 48 | `!tst!DEPT` | dept | ORG | Оргструктура | ✅ |  |
| 76 | `DOC_FILE` | doc_file | DICT | Справочник | ✅ | ✅ |
| 47 | `!tst!EMPLOYEE` | employee | DICT | Справочник | ✅ |  |
| 65 | `EXTERNAL_CONTACT` | external_contact | DICT | Справочник | ✅ |  |
| 67 | `INCOMING_DOC` | incoming_doc | DOC | Документ | ✅ |  |
| 50 | `!tst!MEMO` | memo | DOC | Документ | ✅ |  |
| 68 | `OUTGOING_DOC` | outgoing_doc | DOC | Документ | ✅ |  |
| 1 | `person` | person | PERSON | Персоны | ✅ |  |
| 77 | `REPORT_FILE` | report_file | DICT | Справочник | ✅ | ✅ |
| 69 | `RESOLUTION` | resolution | DOC | Документ | ✅ | ✅ |
| 51 | `!tst!ROUTE` | route | DICT | Справочник | ✅ |  |
| 72 | `ROUTE_INSTANCE` | route_instance | DOC | Документ | ✅ | ✅ |
| 52 | `!tst!ROUTE_STEP` | route_step | DICT | Справочник | ✅ |  |
| 73 | `ROUTE_STEP_INSTANCE` | route_step_instance | DOC | Документ | ✅ | ✅ |
| 49 | `!tst!STAFF_POSITION` | staff_position | DICT | Справочник | ✅ |  |
| 5 | `ADDRESS` | Адрес | ADDRESS | Адрес | ✅ |  |
| 3 | `street` | Улицы | — | Справочник | ✅ |  |
| 4 | `sex` | пол | — | Справочник |  |  |

## Поля сущностей (`meta.fields`)


### person (id=1)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 1 | `cLastName` | LastName | C | 255 |  |  | ✅ |  |  |
| 2 | `cFirstName` | FirstName | C | 255 |  | ✅ | ✅ |  |  |
| 3 | `cSecondName` | SecondName | C | 255 |  |  |  |  |  |
| 4 | `dBirthDate` | BirthDate | D | 255 |  | ✅ | ✅ |  |  |
| 5 | `cInn` | INN | C | 255 |  | ✅ |  |  |  |
| 6 | `sex` | sex | R | 1 |  | ✅ |  |  |  |
| 99 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### city (id=2)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 7 | `citizent` | cityzrnt | I | 255 |  | ✅ |  |  |  |
| 98 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### Улицы (id=3)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 101 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### пол (id=4)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 24 | `sex` | Новое поле | C | 255 |  |  |  |  |  |
| 102 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### Адрес (id=5)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 12 | `full_address` | Полный адрес | C | 500 |  | ✅ |  |  |  |
| 13 | `aoguid` | Идентификатор ГАР | C | 36 |  | ✅ |  |  |  |
| 14 | `house` | Дом/строение | C | 50 |  |  |  |  |  |
| 15 | `building` | Корпус/литера | C | 50 |  |  |  |  |  |
| 16 | `flat` | Квартира/офис | C | 50 |  |  |  |  |  |
| 17 | `country` | Страна | C | 100 |  |  |  |  |  |
| 18 | `region` | Регион | C | 100 |  |  |  |  |  |
| 19 | `district` | Район | C | 100 |  |  |  |  |  |
| 20 | `city` | Город/населённый пункт | C | 150 |  |  |  |  |  |
| 21 | `locality` | Населённый пункт | C | 150 |  |  |  |  |  |
| 22 | `street` | Улица | C | 150 |  |  |  |  |  |
| 23 | `additional` | Дополнительно | C | 100 |  |  |  |  |  |
| 100 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### Invoice (id=7)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 96 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### Invoice_line (id=8)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 26 | `idInvoice` | FK: idInvoice | I | 255 |  | ✅ |  |  |  |
| 97 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |

### BIK (id=10)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 135 | `sourceid` | Source ID | C | 255 |  | ✅ |  |  | ✅ |
| 136 | `bic` | Bic | C | 255 |  | ✅ |  |  |  |
| 137 | `participantinfo_namep` | Participantinfo_namep | C | 255 |  | ✅ |  |  |  |
| 138 | `participantinfo_regn` | Participantinfo_regn | C | 255 |  | ✅ |  |  |  |
| 139 | `participantinfo_cntrcd` | Participantinfo_cntrcd | C | 255 |  | ✅ |  |  |  |
| 140 | `participantinfo_rgn` | Participantinfo_rgn | C | 255 |  | ✅ |  |  |  |
| 141 | `participantinfo_ind` | Participantinfo_ind | C | 255 |  | ✅ |  |  |  |
| 142 | `participantinfo_tnp` | Participantinfo_tnp | C | 255 |  | ✅ |  |  |  |
| 143 | `participantinfo_nnp` | Participantinfo_nnp | C | 255 |  | ✅ |  |  |  |
| 144 | `participantinfo_adr` | Participantinfo_adr | C | 255 |  | ✅ |  |  |  |
| 145 | `participantinfo_datein` | Participantinfo_datein | C | 255 |  | ✅ |  |  |  |
| 146 | `participantinfo_pttype` | Participantinfo_pttype | C | 255 |  | ✅ |  |  |  |
| 147 | `participantinfo_srvcs` | Participantinfo_srvcs | C | 255 |  | ✅ |  |  |  |
| 148 | `participantinfo_xchtype` | Participantinfo_xchtype | C | 255 |  | ✅ |  |  |  |
| 149 | `participantinfo_uid` | Participantinfo_uid | C | 255 |  | ✅ |  |  |  |
| 150 | `participantinfo_participantstatus` | Participantinfo_participantstatus | C | 255 |  | ✅ |  |  |  |
| 151 | `participantinfo_rstrlist_rstr` | Participantinfo_rstrlist_rstr | C | 255 |  | ✅ |  |  |  |
| 152 | `participantinfo_rstrlist_rstrdate` | Participantinfo_rstrlist_rstrdate | C | 255 |  | ✅ |  |  |  |
| 153 | `accounts_account` | Accounts_account | C | 255 |  | ✅ |  |  |  |
| 154 | `accounts_regulationaccounttype` | Accounts_regulationaccounttype | C | 255 |  | ✅ |  |  |  |
| 155 | `accounts_ck` | Accounts_ck | C | 255 |  | ✅ |  |  |  |
| 156 | `accounts_accountcbrbic` | Accounts_accountcbrbic | C | 255 |  | ✅ |  |  |  |
| 157 | `accounts_datein` | Accounts_datein | C | 255 |  | ✅ |  |  |  |
| 158 | `accounts_accountstatus` | Accounts_accountstatus | C | 255 |  | ✅ |  |  |  |

### employee (id=47)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 334 | `cname` | Наименование | C | 150 |  | ✅ |  |  |  |
| 335 | `code` | Код должности | C | 50 |  | ✅ |  |  |  |
| 336 | `salary_rate` | Тарифная ставка | N | 15 |  |  |  |  |  |
| 337 | `parentid` | Родительская должность | I |  |  |  |  |  |  |

### dept (id=48)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 338 | `cname` | Наименование | C | 150 |  | ✅ |  |  |  |
| 339 | `code` | Код подразделения | C | 50 |  | ✅ |  |  |  |
| 340 | `parentid` | Родительское подразделение | I |  |  | ✅ |  |  |  |
| 341 | `chief_staff_id` | Руководитель (штатная единица) | R |  |  |  |  |  |  |

### staff_position (id=49)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 342 | `dept_id` | Подразделение | R |  |  | ✅ |  |  |  |
| 343 | `employee_id` | Должность | R |  |  | ✅ |  |  |  |
| 344 | `person_id` | Сотрудник (персона) | R |  |  | ✅ |  |  |  |
| 345 | `rate` | Ставка | N | 15 |  |  |  |  |  |
| 346 | `is_chief` | Руководитель подразделения | L |  |  | ✅ |  |  |  |
| 347 | `date_from` | Дата назначения | D |  |  | ✅ |  |  |  |
| 348 | `date_to` | Дата увольнения | D |  |  | ✅ |  |  |  |
| 349 | `balanceunit_id` | Балансовая единица | R |  |  | ✅ |  |  |  |
| 505 | `dept_ID` | FK: dept_ID | I | 255 |  | ✅ |  |  |  |

### memo (id=50)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 350 | `doc_number` | Номер документа | C | 50 |  | ✅ |  |  |  |
| 351 | `doc_date` | Дата документа | D |  |  | ✅ |  |  |  |
| 352 | `subject` | Тема | C | 255 |  | ✅ |  |  |  |
| 353 | `content` | Содержание | M |  |  |  |  |  |  |
| 354 | `author_staff_id` | Автор (штатная единица) | R |  |  | ✅ |  |  |  |
| 355 | `status` | Статус документа | C | 50 |  | ✅ |  |  |  |

### route (id=51)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 356 | `cname` | Наименование | C | 150 |  | ✅ |  |  |  |
| 357 | `code` | Код маршрута | C | 50 |  | ✅ |  |  |  |
| 358 | `doc_type_id` | Тип документа | R |  |  | ✅ |  |  |  |
| 359 | `is_active` | Активен | L |  |  | ✅ |  |  |  |

### route_step (id=52)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 360 | `route_id` | Маршрут | R |  |  | ✅ |  |  |  |
| 361 | `step_order` | Порядок этапа | I |  |  | ✅ |  |  |  |
| 362 | `step_name` | Название этапа | C | 100 |  | ✅ |  |  |  |
| 363 | `assign_type` | Тип назначения | C | 50 |  | ✅ |  |  |  |
| 364 | `assign_target` | Цель назначения | C | 255 |  | ✅ |  |  |  |
| 365 | `scope` | Область поиска | C | 20 |  | ✅ |  |  |  |
| 366 | `scope_target` | Целевая БЕ | C | 255 |  |  |  |  |  |
| 367 | `time_limit_days` | Лимит дней | I |  |  |  |  |  |  |
| 368 | `next_step_on_reject` | Следующий этап при отказе | I |  |  |  |  |  |  |

### external_contact (id=65)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 415 | `cname` | Наименование | C | 500 |  | ✅ |  |  |  |
| 416 | `short_name` | Краткое наименование | C | 255 |  |  |  |  |  |
| 417 | `contact_type` | Тип | C | 1 |  |  |  |  |  |
| 418 | `inn` | ИНН | C | 20 |  | ✅ |  |  |  |
| 419 | `phone` | Телефон | C | 50 |  |  |  |  |  |
| 420 | `email` | Email | C | 255 |  |  |  |  |  |
| 421 | `address` | Адрес | M |  |  |  |  |  |  |

### assignment_template (id=66)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 422 | `cname` | Текст поручения | C | 500 |  | ✅ |  |  |  |
| 423 | `code` | Код | C | 100 |  | ✅ |  |  |  |
| 424 | `default_deadline_days` | Срок по умолчанию | I |  |  |  |  |  |  |
| 425 | `is_active` | Активно | L |  |  |  |  |  |  |
| 426 | `sort_order` | Порядок | I |  |  |  |  |  |  |
| 427 | `mcomment` | Комментарий | M |  |  |  |  |  |  |

### incoming_doc (id=67)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 428 | `balanceunit_id` | Балансовая единица | R |  |  | ✅ |  |  |  |
| 429 | `doc_number` | Входящий номер | C | 100 |  | ✅ |  |  |  |
| 430 | `doc_date` | Дата регистрации | D |  |  | ✅ |  |  |  |
| 431 | `external_number` | Номер отправителя | C | 100 |  |  |  |  |  |
| 432 | `external_date` | Дата отправителя | D |  |  |  |  |  |  |
| 433 | `sender_contact_id` | Отправитель | R |  |  | ✅ |  |  |  |
| 434 | `subject` | Тема | C | 500 |  | ✅ |  |  |  |
| 435 | `delivery_method` | Способ доставки | C | 20 |  |  |  |  |  |
| 436 | `is_urgent` | Срочно | L |  |  |  |  |  |  |

### outgoing_doc (id=68)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 437 | `balanceunit_id` | Балансовая единица | R |  |  | ✅ |  |  |  |
| 438 | `doc_number` | Исходящий номер | C | 100 |  | ✅ |  |  |  |
| 439 | `doc_date` | Дата | D |  |  | ✅ |  |  |  |
| 440 | `recipient_contact_id` | Получатель | R |  |  | ✅ |  |  |  |
| 441 | `subject` | Тема | C | 500 |  | ✅ |  |  |  |
| 442 | `response_to_doc_id` | Ответ на входящий | R |  |  |  |  |  |  |
| 443 | `signed_by_user_id` | Подписал | R |  |  |  |  |  |  |
| 444 | `sent_date` | Дата отправки | D |  |  |  |  |  |  |
| 445 | `delivery_method` | Способ отправки | C | 20 |  |  |  |  |  |

### resolution (id=69)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 446 | `doc_instance_id` | Документ | R |  |  | ✅ |  |  |  |
| 447 | `author_user_id` | Автор | I |  |  | ✅ |  |  |  |
| 448 | `on_behalf_user_id` | От имени | I |  |  |  |  |  |  |
| 449 | `resolution_text` | Текст резолюции | M |  |  |  |  |  |  |
| 450 | `deadline` | Срок | D |  |  |  |  |  |  |

### assignment (id=70)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 451 | `resolution_id` | Резолюция | R |  |  | ✅ |  |  |  |
| 452 | `assignee_user_id` | Исполнитель | I |  |  | ✅ |  |  |  |
| 453 | `role_type` | Роль | C | 20 |  |  |  |  |  |
| 454 | `description` | Текст поручения | M |  |  |  |  |  |  |
| 455 | `deadline` | Плановый срок | D |  |  |  |  |  |  |
| 456 | `finished_at` | Фактический срок | T |  |  |  |  |  |  |
| 457 | `status` | Статус | C | 20 |  | ✅ |  |  |  |
| 480 | `balanceunit_id` | Балансовая единица | R |  |  | ✅ |  |  |  |
| 481 | `step_instance_id` | Связанный этап | R |  |  |  |  |  |  |

### assignment_report (id=71)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 458 | `assignment_id` | Поручение | R |  |  | ✅ |  |  |  |
| 459 | `author_user_id` | Автор отчёта | I |  |  | ✅ |  |  |  |
| 460 | `report_text` | Текст отчёта | M |  |  |  |  |  |  |
| 482 | `status` | Статус отчёта | C | 20 |  |  |  |  |  |

### route_instance (id=72)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 461 | `template_id` | Шаблон | I |  |  | ✅ |  |  |  |
| 462 | `doc_instance_id` | Документ | R |  |  | ✅ |  |  |  |
| 463 | `balanceunit_id` | Балансовая единица | R |  |  | ✅ |  |  |  |
| 464 | `started_at` | Дата запуска | T |  |  |  |  |  |  |
| 465 | `finished_at` | Дата завершения | T |  |  |  |  |  |  |
| 466 | `status` | Статус | C | 20 |  | ✅ |  |  |  |

### route_step_instance (id=73)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 467 | `route_instance_id` | Маршрут | R |  |  | ✅ |  |  |  |
| 468 | `step_template_id` | Шаблон этапа | I |  |  |  |  |  |  |
| 469 | `parent_step_id` | Родительский этап | R |  |  |  |  |  |  |
| 470 | `assignee_user_id` | Исполнитель | I |  |  | ✅ |  |  |  |
| 471 | `delegate_to_user_id` | Делегат | I |  |  |  |  |  |  |
| 472 | `started_at` | Начало | T |  |  |  |  |  |  |
| 473 | `deadline` | Срок | T |  |  |  |  |  |  |
| 474 | `finished_at` | Завершение | T |  |  |  |  |  |  |
| 475 | `decision` | Решение | C | 20 |  |  |  |  |  |
| 476 | `comment` | Комментарий | M |  |  |  |  |  |  |
| 477 | `status` | Статус | C | 20 |  | ✅ |  |  |  |

### doc_file (id=76)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 503 | `doc_instance_id` | FK: INCOMING_DOC | I | 255 |  | ✅ |  |  |  |
| 493 | `file_data` | Файл | G |  |  |  |  |  |  |
| 494 | `file_size` | Размер (байт) | I |  |  |  |  |  |  |
| 495 | `mime_type` | MIME-тип | C | 100 |  |  |  |  |  |
| 496 | `description` | Описание | M |  |  |  |  |  |  |
| 497 | `uploaded_by_user_id` | Кто загрузил | I |  |  | ✅ |  |  |  |

### report_file (id=77)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 504 | `report_id` | FK: ASSIGNMENT_REPORT | I | 255 |  | ✅ |  |  |  |
| 498 | `file_data` | Файл | G |  |  |  |  |  |  |
| 499 | `file_size` | Размер (байт) | I |  |  |  |  |  |  |
| 500 | `mime_type` | MIME-тип | C | 100 |  |  |  |  |  |
| 501 | `description` | Описание | M |  |  |  |  |  |  |
| 502 | `uploaded_by_user_id` | Кто загрузил | I |  |  | ✅ |  |  |  |

### chart_of_accounts (id=79)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 508 | `cname` | Наименование | C | 500 |  | ✅ |  |  |  |
| 509 | `calias` | Код | C | 100 |  | ✅ |  |  |  |
| 510 | `balanceunit_id` | Балансовая единица | R |  |  |  |  |  |  |
| 511 | `is_active` | Активен | L |  |  |  |  |  |  |
| 512 | `mcomment` | Комментарий | M |  |  |  |  |  |  |

### chart_account (id=80)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 559 | `chart_id` | FK: CHART_OF_ACCOUNTS | I | 255 |  | ✅ |  |  |  |
| 513 | `code` | Код счёта | C | 20 |  | ✅ |  |  |  |
| 514 | `cname` | Наименование | C | 500 |  | ✅ |  |  |  |
| 515 | `account_type` | Тип (A/P/AP) | C | 2 |  |  |  |  |  |
| 516 | `parent_id` | Родительский счёт | R |  |  |  |  |  |  |
| 517 | `is_active` | Активен | L |  |  |  |  |  |  |
| 518 | `mcomment` | Комментарий | M |  |  |  |  |  |  |

### chart_account_comment (id=81)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 560 | `chart_account_id` | FK: CHART_ACCOUNT | I | 255 |  | ✅ |  |  |  |
| 519 | `source` | Источник | C | 255 |  |  |  |  |  |
| 520 | `section` | Раздел | C | 255 |  | ✅ |  |  |  |
| 521 | `comment_text` | Текст | M |  |  |  |  |  |  |
| 522 | `doc_url` | Ссылка | C | 500 |  |  |  |  |  |
| 523 | `file_data` | Файл | G |  |  |  |  |  |  |

### account (id=82)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 524 | `cname` | Наименование | C | 500 |  | ✅ |  |  |  |
| 525 | `calias` | Код | C | 100 |  |  |  |  |  |
| 526 | `description` | Описание | M |  |  |  |  |  |  |
| 527 | `parent_account_id` | Группирующий счёт | R |  |  |  |  |  |  |
| 528 | `is_group` | Это группа | L |  |  |  |  |  |  |

### asset_movement (id=83)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 561 | `account_id` | FK: ACCOUNT | I | 255 |  | ✅ |  |  |  |
| 529 | `to_employee_id` | Ответственный | R |  |  | ✅ |  |  |  |
| 530 | `to_location` | Местонахождение | C | 255 |  |  |  |  |  |
| 531 | `movement_date` | Дата перемещения | D |  |  | ✅ |  |  |  |
| 532 | `return_date` | Дата возврата | D |  |  |  |  |  |  |
| 533 | `comment` | Комментарий | M |  |  |  |  |  |  |

### aspect (id=84)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 562 | `account_id` | FK: ACCOUNT | I | 255 |  | ✅ |  |  |  |
| 534 | `calias` | Код ипостаси | C | 50 |  | ✅ |  |  |  |
| 535 | `cname` | Наименование | C | 500 |  | ✅ |  |  |  |
| 536 | `is_monetary` | Денежная | L |  |  |  |  |  |  |
| 537 | `description` | Описание | M |  |  |  |  |  |  |

### aspect_chart_binding (id=85)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 563 | `aspect_id` | FK: ASPECT | I | 255 |  | ✅ |  |  |  |
| 538 | `chart_id` | План счетов | R |  |  | ✅ |  |  |  |
| 539 | `chart_account_id` | Балансовый счёт | R |  |  | ✅ |  |  |  |
| 540 | `is_default` | По умолчанию | L |  |  |  |  |  |  |
| 541 | `mcomment` | Комментарий | M |  |  |  |  |  |  |

### aspect_daily (id=86)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 564 | `aspect_id` | FK: ASPECT | I | 255 |  | ✅ |  |  |  |
| 542 | `chart_binding_id` | Привязка к плану | R |  |  | ✅ |  |  |  |
| 543 | `date` | Дата | D |  |  | ✅ |  |  |  |
| 544 | `in_debet` | Вх. дебет | N | 15 |  |  |  |  |  |
| 545 | `in_kredit` | Вх. кредит | N | 15 |  |  |  |  |  |
| 546 | `turnover_debet` | Оборот дебет | N | 15 |  |  |  |  |  |
| 547 | `turnover_kredit` | Оборот кредит | N | 15 |  |  |  |  |  |
| 548 | `out_debet` | Исх. дебет | N | 15 |  |  |  |  |  |
| 549 | `out_kredit` | Исх. кредит | N | 15 |  |  |  |  |  |

### account_turnover (id=87)

| ID | Имя | Alias | Тип | Длина | Точн. | Индекс | Обязат. | Ссылка | Системное |
|----|-----|-------|-----|-------|-------|--------|---------|--------|-----------|
| 565 | `account_id` | FK: ACCOUNT | I | 255 |  | ✅ |  |  |  |
| 550 | `doc_instance_id` | Документ | R |  |  | ✅ |  |  |  |
| 551 | `doc_child_entitytype_id` | Тип строки | I |  |  |  |  |  |  |
| 552 | `doc_line_instance_id` | Строка документа | R |  |  |  |  |  |  |
| 553 | `debit_aspect_id` | Ипостась дебета | R |  |  | ✅ |  |  |  |
| 554 | `credit_aspect_id` | Ипостась кредита | R |  |  | ✅ |  |  |  |
| 555 | `amount` | Сумма | N | 15 |  | ✅ |  |  |  |
| 556 | `turnover_date` | Дата | D |  |  | ✅ |  |  |  |
| 557 | `period` | Период | C | 7 |  | ✅ |  |  |  |
| 558 | `comment` | Комментарий | M |  |  |  |  |  |  |

## Роли вложений (`meta.composition_roles`)

| ID | Alias | Название | Описание |
|----|-------|----------|----------|
| 1 | `строкиНакладных` | lineInv |  |
| 3 | `FILES` | Файлы | Прикреплённые файлы |
| 4 | `должности оргструктуры` | dlzSTR | должности подразделений |
| 5 | `ITEMS` | Элементы | Элементы справочника |
| 6 | `COMMENTS` | Комментарии | Комментарии и рекомендации |
| 7 | `MOVEMENTS` | Движения | Перемещения активов |
| 8 | `ASPECTS` | Ипостаси | Характеристики объекта учёта |
| 9 | `CHART_BINDINGS` | Привязки к планам | Связь ипостаси с балансовыми счетами |
| 10 | `DAILY_STATES` | Состояния по дням | Ежедневные срезы ипостаси |
| 11 | `TURNOVERS` | Проводки | Журнал хозяйственных операций |

## Связи мастер-деталь (`meta.entity_composition`)

| ID | Мастер | Деталь | Роль | Поле связи | Порядок |
|----|--------|--------|------|------------|---------|
| 1 | Invoice | Invoice_line | lineInv | `idInvoice` | 10 |
| 4 | incoming_doc | doc_file | Файлы | `doc_instance_id` | 10 |
| 13 | assignment_report | report_file | Файлы | `report_id` | 10 |
| 14 | Invoice | doc_file | Файлы | `doc_instance_id` | 10 |
| 15 | assignment | doc_file | Файлы | `doc_instance_id` | 10 |
| 16 | assignment_report | doc_file | Файлы | `doc_instance_id` | 10 |
| 17 | memo | doc_file | Файлы | `doc_instance_id` | 10 |
| 18 | outgoing_doc | doc_file | Файлы | `doc_instance_id` | 10 |
| 19 | route_instance | doc_file | Файлы | `doc_instance_id` | 10 |
| 20 | route_step_instance | doc_file | Файлы | `doc_instance_id` | 10 |
| 21 | dept | staff_position | dlzSTR | `dept_ID` | 10 |
| 22 | chart_of_accounts | chart_account | Элементы | `chart_id` | 10 |
| 23 | chart_account | chart_account_comment | Комментарии | `chart_account_id` | 10 |
| 24 | account | asset_movement | Движения | `account_id` | 10 |
| 25 | account | aspect | Ипостаси | `account_id` | 10 |
| 26 | aspect | aspect_chart_binding | Привязки к планам | `aspect_id` | 10 |
| 27 | aspect | aspect_daily | Состояния по дням | `aspect_id` | 10 |
| 28 | account | account_turnover | Проводки | `account_id` | 10 |

## Low-code классы (`class_erp.mozartclasses`)

| ID | Имя | Категория | Класс | Владелец |
|----|-----|-----------|-------|----------|
| 200 | `DemoProductsGrid` |  | ✅ | 200 |
| 16 | `MozartBaseInvisible` | 4 | ✅ |  |
| 9 | `MozartButton` | 2 | ✅ |  |
| 4 | `MozartCheckBox` | 1 | ✅ |  |
| 5 | `MozartComboBox` | 1 | ✅ |  |
| 12 | `MozartContainer` | 3 | ✅ |  |
| 3 | `MozartDateBox` | 1 | ✅ |  |
| 109 | `MozartDialogForm` | 3 | ✅ |  |
| 112 | `MozartGrid` | 3 | ✅ |  |
| 108 | `MozartGridColumn` | 3 | подобъект | 104 |
| 14 | `MozartImageView` | 2 | ✅ |  |
| 10 | `MozartLabel` | 2 | ✅ |  |
| 6 | `MozartListBox` | 1 | ✅ |  |
| 101 | `MozartMainForm` | 3 | ✅ |  |
| 8 | `MozartMemo` | 1 | ✅ |  |
| 2 | `MozartNumberBox` | 1 | ✅ |  |
| 7 | `MozartOptionGroup` |  | ✅ |  |
| 15 | `MozartRadioButton` | 2 | ✅ |  |
| 17 | `MozartReference` | 4 | ✅ | 17 |
| 13 | `MozartTabContainer` | 3 | ✅ |  |
| 113 | `MozartTable` | 3 | ✅ |  |
| 1 | `MozartTextBox` | 1 | ✅ |  |
| 106 | `MozartTreeColumn` | 4 | подобъект | 104 |
| 105 | `MozartTreeView` | 4 | ✅ |  |
| 102 | `MozartWorkForm` | 3 | ✅ |  |
| 110 | `MyDialogForm` | 3 | ✅ |  |
| 100 | `MyMainForm` | 3 | ✅ |  |
| 104 | `MyTreeView` | 4 | ✅ | 104 |
| 21 | `Ref_ClearBtn` | 2 | подобъект | 17 |
| 18 | `Ref_Label` | 2 | подобъект | 17 |
| 20 | `Ref_SelectBtn` | 2 | подобъект | 17 |
| 19 | `Ref_TextEdit` | 1 | подобъект | 17 |
| 210 | `demoColumn1` |  | подобъект | 200 |
| 220 | `domoColumn2` |  | подобъект | 200 |

## Версии low-code классов (`class_erp.class_version`)

| ID | Класс | Базовый Qt | Источник | Env | Preload | Статус | Видимый | Библиотека |
|----|-------|------------|----------|-----|---------|--------|---------|------------|
| 200 | `DemoProductsGrid` | `DemoProductsGrid` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 16 | `MozartBaseInvisible` | `QObject` | QT | HYBRID | ⚡ | 2 |  | PySide6.QtCore |
| 9 | `MozartButton` | `QPushButton` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 4 | `MozartCheckBox` | `QCheckBox` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 5 | `MozartComboBox` | `QComboBox` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 12 | `MozartContainer` | `QGroupBox` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 3 | `MozartDateBox` | `QDateEdit` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 109 | `MozartDialogForm` | `QDialog` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 112 | `MozartGrid` | `MozartGrid` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 108 | `MozartGridColumn` | `MozartGridColumn` | ERP | HYBRID |  | 1 |  | builtins |
| 14 | `MozartImageView` | `QWidget` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 10 | `MozartLabel` | `QLabel` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 6 | `MozartListBox` | `QListWidget` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 101 | `MozartMainForm` | `QMainWindow` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 8 | `MozartMemo` | `QPlainTextEdit` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 2 | `MozartNumberBox` | `QLineEdit` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 7 | `MozartOptionGroup` | `QWidget` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 15 | `MozartRadioButton` | `QRadioButton` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 17 | `MozartReference` | `MozartContainer` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 13 | `MozartTabContainer` | `QTabWidget` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 113 | `MozartTable` | `QTableWidget` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 1 | `MozartTextBox` | `QLineEdit` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 106 | `MozartTreeColumn` | `MozartTreeColumn` | ERP | HYBRID |  | 1 |  | builtins |
| 105 | `MozartTreeView` | `QTreeView` | QT | HYBRID | ⚡ | 2 | 👁️ | PySide6.QtWidgets |
| 102 | `MozartWorkForm` | `MozartWorkForm` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 110 | `MyDialogForm` | `MyDialogForm` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 100 | `MyMainForm` | `MyMainForm` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 104 | `MyTreeView` | `MyTreeView` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 21 | `Ref_ClearBtn` | `MozartButton` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 18 | `Ref_Label` | `MozartLabel` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 20 | `Ref_SelectBtn` | `MozartButton` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 19 | `Ref_TextEdit` | `MozartTextBox` | ERP | HYBRID |  | 1 | 👁️ | builtins |
| 210 | `demoColumn1` | `demoColumn1` | ERP | HYBRID |  | 1 |  | builtins |
| 220 | `domoColumn2` | `domoColumn2` | ERP | HYBRID |  | 1 |  | builtins |

## Мосты свойств (`class_erp.class_property_bridge`)


### `QCheckBox` (23 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 764 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 17 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 18 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 13 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 756 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 14 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 100 | `checked` | Выставлен | boolean | checked | DIRECT |  |
| 760 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 15 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 761 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 767 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 758 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 757 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 134 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 183 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 177 | `myx` | X | number | myx | CUSTOM |  |
| 153 | `myy` | Y | number | myy | CUSTOM |  |
| 766 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 759 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 99 | `text` | Текст подписи | text | text | DIRECT |  |
| 16 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 768 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 762 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QComboBox` (22 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 632 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 23 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 24 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 19 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 624 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 20 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 628 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 21 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 629 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 635 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 310 | `items_list` | Список вариантов | list_items | items_json | JSON_MAP |  |
| 626 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 625 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 165 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 126 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 122 | `myx` | X | number | myx | CUSTOM |  |
| 160 | `myy` | Y | number | myy | CUSTOM |  |
| 634 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 627 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 22 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 636 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 630 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QDateEdit` (21 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 751 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 11 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 12 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 7 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 743 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 8 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 747 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 9 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 748 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 754 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 745 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 744 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 151 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 168 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 173 | `myx` | X | number | myx | CUSTOM |  |
| 138 | `myy` | Y | number | myy | CUSTOM |  |
| 753 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 746 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 10 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 755 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 749 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QDialog` (23 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 645 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 77 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 78 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 73 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 637 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 74 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 641 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 75 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 642 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 648 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 639 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 638 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 108 | `modal` | Модальное окно | boolean | modal | DIRECT |  |
| 171 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 152 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 144 | `myx` | X | number | myx | CUSTOM |  |
| 189 | `myy` | Y | number | myy | CUSTOM |  |
| 647 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 640 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 76 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 649 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 643 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |
| 107 | `windowTitle` | Заголовок окна | text | windowTitle | DIRECT |  |

### `QGroupBox` (23 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 726 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 59 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 60 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 55 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 205 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 56 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 722 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 57 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 106 | `flat` | Без рамок | boolean | flat | DIRECT |  |
| 723 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 729 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 720 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 719 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 186 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 137 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 141 | `myx` | X | number | myx | CUSTOM |  |
| 169 | `myy` | Y | number | myy | CUSTOM |  |
| 728 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 721 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 105 | `title` | Наименование группы | text | title | DIRECT |  |
| 58 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 730 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 724 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QLabel` (24 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 657 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 53 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 54 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 49 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 202 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 50 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 653 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 51 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 654 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 660 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 651 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 650 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 131 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 158 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 156 | `myx` | X | number | myx | CUSTOM |  |
| 129 | `myy` | Y | number | myy | CUSTOM |  |
| 207 | `pixmap` | Картинка (pixmap) | image | pixmap | CUSTOM |  |
| 659 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 652 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 103 | `text` | Текст метки | text | text | DIRECT |  |
| 52 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 661 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 655 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |
| 104 | `wordWrap` | Перенос слов | boolean | wordWrap | DIRECT |  |

### `QLineEdit` (29 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 504 | `alignment` | Выравнивание текста | choice | alignment | DIRECT |  |
| 823 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 511 | `binding_field` | Поле привязки к БД | field_ref | binding_field | DIRECT |  |
| 5 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 6 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 1 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 203 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 2 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 819 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 3 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 820 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 501 | `input_mask` | Маска ввода | text | inputMask | DIRECT |  |
| 512 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 503 | `max_length` | Макс. длина | number | maxLength | DIRECT |  |
| 517 | `maximum_size` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 816 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 166 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 130 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 125 | `myx` | X | number | myx | CUSTOM |  |
| 159 | `myy` | Y | number | myy | CUSTOM |  |
| 502 | `placeholder_text` | Подсказка ввода | text | placeholderText | DIRECT |  |
| 93 | `readOnly` | Только чтение | boolean | readOnly | DIRECT |  |
| 825 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 818 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 518 | `style_sheet` | Доп. CSS стили | text | styleSheet | DIRECT |  |
| 91 | `text` | Значение текста | text | text | DIRECT |  |
| 4 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 513 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 821 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QListWidget` (22 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 701 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 29 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 30 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 25 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 693 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 26 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 697 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 27 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 698 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 704 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 311 | `items_list` | Список вариантов | list_items | items_json | JSON_MAP |  |
| 695 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 694 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 136 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 188 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 181 | `myx` | X | number | myx | CUSTOM |  |
| 150 | `myy` | Y | number | myy | CUSTOM |  |
| 703 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 696 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 28 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 705 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 699 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QMainWindow` (22 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 688 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 71 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 72 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 67 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 680 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 68 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 684 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 69 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 685 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 691 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 682 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 681 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 135 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 182 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 175 | `myx` | X | number | myx | CUSTOM |  |
| 155 | `myy` | Y | number | myy | CUSTOM |  |
| 690 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 683 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 70 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 692 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 686 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |
| 109 | `windowTitle` | Заголовок системы | text | windowTitle | DIRECT |  |

### `QObject` (23 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 117 | `alignment` | Выравнивание | choice | alignment | DIRECT |  |
| 115 | `allow_filter` | Включить фильтр | boolean | allow_filter | DIRECT |  |
| 619 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 111 | `binding_field` | Поле привязки к БД | text | binding_field | DIRECT |  |
| 769 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 773 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 112 | `data_type` | Тип данных | choice | data_type | DIRECT |  |
| 774 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 110 | `header_text` | Заголовок колонки | text | header_text | DIRECT |  |
| 622 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 771 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 770 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 163 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 127 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 123 | `myx` | X | number | myx | CUSTOM |  |
| 161 | `myy` | Y | number | myy | CUSTOM |  |
| 114 | `readonly` | Только чтение | boolean | readonly | DIRECT |  |
| 621 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 772 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 116 | `sortable` | Сортируемая | boolean | sortable | DIRECT |  |
| 623 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 113 | `width` | Ширина колонки | number | width | DIRECT |  |
| 775 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QPlainTextEdit` (23 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 670 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 41 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 42 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 37 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 662 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 38 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 666 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 39 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 667 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 673 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 664 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 663 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 170 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 149 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 145 | `myx` | X | number | myx | CUSTOM |  |
| 187 | `myy` | Y | number | myy | CUSTOM |  |
| 95 | `plainText` | Текст блока | text | plainText | DIRECT |  |
| 96 | `readOnly` | Только чтение | boolean | readOnly | DIRECT |  |
| 672 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 665 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 40 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 674 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 668 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QPushButton` (25 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 738 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 47 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 48 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 43 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 9001 | `c_border_color` | Цвет рамки | color | border-color | CSS |  |
| 204 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 44 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 734 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 45 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 98 | `flat` | Плоский стиль | boolean | flat | DIRECT |  |
| 735 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 208 | `icon` | Иконка кнопки | image | icon | CUSTOM |  |
| 741 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 732 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 731 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 178 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 140 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 139 | `myx` | X | number | myx | CUSTOM |  |
| 172 | `myy` | Y | number | myy | CUSTOM |  |
| 740 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 733 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 97 | `text` | Текст кнопки | text | text | DIRECT |  |
| 46 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 742 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 736 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QRadioButton` (17 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 785 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 777 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 102 | `checked` | Выбран | boolean | checked | DIRECT |  |
| 781 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 782 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 788 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 779 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 778 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 174 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 148 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 154 | `myx` | X | number | myx | CUSTOM |  |
| 176 | `myy` | Y | number | myy | CUSTOM |  |
| 787 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 780 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 101 | `text` | Текст опции | text | text | DIRECT |  |
| 789 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 783 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QTabWidget` (21 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 798 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 65 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 66 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 61 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 790 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 62 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 794 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 63 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 795 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 801 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 792 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 791 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 162 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 132 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 133 | `myx` | X | number | myx | CUSTOM |  |
| 164 | `myy` | Y | number | myy | CUSTOM |  |
| 800 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 793 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 64 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 802 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 796 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QTableWidget` (21 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 811 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 89 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 90 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 85 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 803 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 86 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 807 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 87 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 808 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 814 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 805 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 804 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 143 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 179 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 184 | `myx` | X | number | myx | CUSTOM |  |
| 146 | `myy` | Y | number | myy | CUSTOM |  |
| 813 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 806 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 88 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 815 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 809 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QTreeView` (21 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 714 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 83 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 84 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 79 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 706 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 80 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 710 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 81 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 711 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 717 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 708 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 707 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 167 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 124 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 128 | `myx` | X | number | myx | CUSTOM |  |
| 157 | `myy` | Y | number | myy | CUSTOM |  |
| 716 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 709 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 82 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 718 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 712 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

### `QWidget` (28 свойств)

| ID | Ключ | UI-метка | Редактор | Qt-target | Стратегия | DefaultERP |
|----|------|----------|----------|-----------|-----------|------------|
| 675 | `binding_entity` | Сущность-источник | entity_ref | binding_entity | DIRECT |  |
| 35 | `c_anchor_horiz` | Якорь по горизонтали | choice | horiz_anchor | GEOMETRY |  |
| 36 | `c_anchor_vert` | Якорь по вертикали | choice | vert_anchor | GEOMETRY |  |
| 31 | `c_back_color` | Цвет фона | color | background-color | CSS |  |
| 206 | `c_background_image` | Фоновое изображение | image | background-image | CSS |  |
| 9002 | `c_border_color` | Цвет рамки | color | border-color | CSS | ✅ |
| 118 | `c_data_source` | Источник данных | entity_ref | c_data_source | DIRECT | ✅ |
| 201 | `c_font` | Шрифт | font | font | CUSTOM |  |
| 32 | `c_text_color` | Цвет текста | color | color | CSS |  |
| 212 | `cursorShape` | Курсор мыши | choice | cursor | DIRECT |  |
| 676 | `display_field` | Поле отображения | field_ref | display_field | DIRECT | ✅ |
| 33 | `enabled` | Доступен | boolean | enabled | DIRECT |  |
| 213 | `focusPolicy` | Политика фокуса | choice | focusPolicy | DIRECT |  |
| 120 | `id_datasource` | ID экземпляра | text | id_datasource | DIRECT | ✅ |
| 678 | `is_required` | Обязательное поле | boolean | is_required | DIRECT |  |
| 210 | `maximumSize` | Макс. размер (W;H) | geometry | maximumSize | CUSTOM |  |
| 209 | `minimumSize` | Мин. размер (W;H) | geometry | minimumSize | CUSTOM |  |
| 142 | `myheight` | Высота | number | myheight | CUSTOM |  |
| 180 | `mywidth` | Ширина | number | mywidth | CUSTOM |  |
| 185 | `myx` | X | number | myx | CUSTOM |  |
| 147 | `myy` | Y | number | myy | CUSTOM |  |
| 312 | `orientation` | Ориентация списка | choice | orientation | DIRECT |  |
| 677 | `selector_form` | Форма выбора | form_ref | selector_form | DIRECT |  |
| 211 | `sizePolicy` | Политика размера | choice | sizePolicy | DIRECT |  |
| 34 | `toolTip` | Всплывающая подсказка | text | toolTip | DIRECT |  |
| 679 | `validation_rule` | Правило валидации (Regex) | text | validation_rule | DIRECT |  |
| 121 | `versionid_datasource` | ID версии | text | versionid_datasource | DIRECT | ✅ |
| 214 | `windowOpacity` | Прозрачность (0.0-1.0) | number | windowOpacity | DIRECT |  |

## Формы (`meta.forms`)

| ID | Alias | Название | Сущность |
|----|-------|----------|----------|
| 1 | `OrdinaryDictionary` | СтандСправочник |  |

## Элементы форм (`meta.form_elements`)


### СтандСправочник (id=1, 3 элементов)

| ID | Parent | Alias | Класс | Источник | Порядок | Активен |
|----|--------|-------|-------|----------|---------|---------|
| 841 |  | `OrdinaryDictionary` | form |  |  | ✅ |
| 823 | 841 | `control_823` | reference |  | 20 | ✅ |
| 828 | 841 | `control_828` | reference |  | 70 | ✅ |

## Переводы (`lang.translations`) — сводка по ключам

Всего ключей: **553**

| Ключ | Языков | Языки |
|------|--------|-------|
| `action_about` | 5 | de, en, ru, tt, zh |
| `action_exit` | 5 | de, en, ru, tt, zh |
| `action_new_project` | 5 | de, en, ru, tt, zh |
| `action_open_project` | 5 | de, en, ru, tt, zh |
| `action_refresh_lang` | 5 | de, en, ru, tt, zh |
| `action_save_project` | 5 | de, en, ru, tt, zh |
| `action_settings` | 5 | de, en, ru, tt, zh |
| `add_import_link` | 5 | de, en, ru, tt, zh |
| `add_import_link_title` | 2 | en, ru |
| `add_method_dialog` | 5 | de, en, ru, tt, zh |
| `add_new_field_button` | 2 | en, ru |
| `add_source_link_title` | 2 | en, ru |
| `apply_mapping_btn` | 2 | en, ru |
| `back_btn` | 2 | en, ru |
| `browse_button` | 5 | de, en, ru, tt, zh |
| `btn_add` | 5 | de, en, ru, tt, zh |
| `btn_add_method` | 5 | de, en, ru, tt, zh |
| `btn_cancel` | 5 | de, en, ru, tt, zh |
| `btn_clear` | 5 | de, en, ru, tt, zh |
| `btn_clear_parent` | 2 | en, ru |
| `btn_close` | 5 | de, en, ru, tt, zh |
| `btn_connect` | 5 | de, en, ru, tt, zh |
| `btn_db_work` | 5 | de, en, ru, tt, zh |
| `btn_delete` | 5 | de, en, ru, tt, zh |
| `btn_delete_method` | 5 | de, en, ru, tt, zh |
| `btn_down` | 5 | de, en, ru, tt, zh |
| `btn_duplicate` | 5 | de, en, ru, tt, zh |
| `btn_edit` | 5 | de, en, ru, tt, zh |
| `btn_edit_code` | 5 | de, en, ru, tt, zh |
| `btn_edit_group_class` | 2 | en, ru |
| `btn_grid_off` | 5 | de, en, ru, tt, zh |
| `btn_grid_on` | 5 | de, en, ru, tt, zh |
| `btn_load` | 5 | de, en, ru, tt, zh |
| `btn_manage_profiles` | 5 | de, en, ru, tt, zh |
| `btn_methods` | 5 | de, en, ru, tt, zh |
| `btn_new_project` | 5 | de, en, ru, tt, zh |
| `btn_new_version` | 5 | de, en, ru, tt, zh |
| `btn_ok` | 5 | de, en, ru, tt, zh |
| `btn_open_project` | 5 | de, en, ru, tt, zh |
| `btn_open_qt_designer` | 5 | de, en, ru, tt, zh |
| `btn_open_visual_designer` | 5 | de, en, ru, tt, zh |
| `btn_refresh` | 5 | de, en, ru, tt, zh |
| `btn_save` | 5 | de, en, ru, tt, zh |
| `btn_save_code` | 5 | de, en, ru, tt, zh |
| `btn_save_project` | 5 | de, en, ru, tt, zh |
| `btn_select` | 5 | de, en, ru, tt, zh |
| `btn_signals` | 5 | de, en, ru, tt, zh |
| `btn_start_client` | 5 | de, en, ru, tt, zh |
| `btn_start_import` | 5 | de, en, ru, tt, zh |
| `btn_start_import_designer` | 5 | de, en, ru, tt, zh |
| `btn_start_import_wizard` | 5 | de, en, ru, tt, zh |
| `btn_start_server` | 5 | de, en, ru, tt, zh |
| `btn_stop_server` | 5 | de, en, ru, tt, zh |
| `btn_up` | 5 | de, en, ru, tt, zh |
| `btn_update_current` | 5 | de, en, ru, tt, zh |
| `callback_not_assigned` | 2 | en, ru |
| `cancel` | 2 | en, ru |
| `class_label` | 5 | de, en, ru, tt, zh |
| `class_type_root` | 5 | de, en, ru, tt, zh |
| `composition_templates` | 5 | de, en, ru, tt, zh |
| `confirm_clear_form` | 5 | de, en, ru, tt, zh |
| `confirm_close` | 5 | de, en, ru, tt, zh |
| `confirm_close_unsaved` | 5 | de, en, ru, tt, zh |
| `confirm_delete` | 5 | de, en, ru, tt, zh |
| `confirm_delete_class` | 5 | de, en, ru, tt, zh |
| `confirm_delete_composition` | 5 | de, en, ru, tt, zh |
| `confirm_delete_context` | 5 | de, en, ru, tt, zh |
| `confirm_delete_document_type` | 5 | de, en, ru, tt, zh |
| `confirm_delete_element` | 5 | de, en, ru, tt, zh |
| `confirm_delete_entities` | 5 | de, en, ru, tt, zh |
| `confirm_delete_fields` | 5 | de, en, ru, tt, zh |
| `confirm_delete_form` | 5 | de, en, ru, tt, zh |
| `confirm_delete_menu_item` | 5 | de, en, ru, tt, zh |
| `confirm_delete_method` | 5 | de, en, ru, tt, zh |
| `confirm_delete_record` | 5 | de, en, ru, tt, zh |
| `confirm_delete_records` | 5 | de, en, ru, tt, zh |
| `confirm_delete_ref_type` | 5 | de, en, ru, tt, zh |
| `confirm_delete_role` | 5 | de, en, ru, tt, zh |
| `confirm_delete_rule` | 5 | de, en, ru, tt, zh |
| `confirm_delete_template` | 5 | de, en, ru, tt, zh |
| `confirm_rename_message` | 5 | de, en, ru, tt, zh |
| `confirm_rename_title` | 5 | de, en, ru, tt, zh |
| `confirm_title` | 5 | de, en, ru, tt, zh |
| `connector_not_ready` | 2 | en, ru |
| `context_configure_link` | 5 | de, en, ru, tt, zh |
| `context_create_entity` | 5 | de, en, ru, tt, zh |
| `context_create_fields_from_table` | 5 | de, en, ru, tt, zh |
| `context_delete_link` | 5 | de, en, ru, tt, zh |
| `context_deselect_all_fields` | 5 | de, en, ru, tt, zh |
| `context_hint_select_one` | 5 | de, en, ru, tt, zh |
| `context_link_selected` | 5 | de, en, ru, tt, zh |
| `context_preview_table` | 5 | de, en, ru, tt, zh |
| `context_ref_fields` | 5 | de, en, ru, tt, zh |
| `context_refresh_links` | 5 | de, en, ru, tt, zh |
| `context_select_all_fields` | 5 | de, en, ru, tt, zh |
| `context_show_import_links` | 5 | de, en, ru, tt, zh |
| `control_button` | 5 | de, en, ru, tt, zh |
| `control_checkbox` | 5 | de, en, ru, tt, zh |
| `control_datebox` | 5 | de, en, ru, tt, zh |
| `control_grid` | 5 | de, en, ru, tt, zh |
| `control_group` | 5 | de, en, ru, tt, zh |
| `control_label` | 5 | de, en, ru, tt, zh |
| `control_memo` | 5 | de, en, ru, tt, zh |
| `control_numberbox` | 5 | de, en, ru, tt, zh |
| `control_panel` | 5 | de, en, ru, tt, zh |
| `control_reference` | 5 | de, en, ru, tt, zh |
| `control_tab` | 5 | de, en, ru, tt, zh |
| `control_textbox` | 5 | de, en, ru, tt, zh |
| `create_entity` | 5 | de, en, ru, tt, zh |
| `create_entity_btn` | 2 | en, ru |
| `create_entity_button` | 2 | en, ru |
| `create_entity_dialog_title` | 2 | en, ru |
| `create_fields_from_checked` | 5 | de, en, ru, tt, zh |
| `create_new_entity` | 2 | en, ru |
| `created_at` | 2 | en, ru |
| `db_group` | 5 | de, en, ru, tt, zh |
| `db_host_label` | 5 | de, en, ru, tt, zh |
| `db_name_label` | 5 | de, en, ru, tt, zh |
| `db_not_ready` | 2 | en, ru |
| `db_pass_label` | 5 | de, en, ru, tt, zh |
| `db_port_label` | 5 | de, en, ru, tt, zh |
| `db_type_label` | 5 | de, en, ru, tt, zh |
| `db_user_label` | 5 | de, en, ru, tt, zh |
| `default_form_title` | 5 | de, en, ru, tt, zh |
| `delete_btn` | 2 | en, ru |
| `delete_profile_confirm` | 5 | de, en, ru, tt, zh |
| `deselect_all` | 5 | de, en, ru, tt, zh |
| `deselect_all_fields` | 5 | de, en, ru, tt, zh |
| `designer_instructions_detail` | 5 | de, en, ru, tt, zh |
| `designer_instructions_text` | 5 | de, en, ru, tt, zh |
| `designer_instructions_title` | 5 | de, en, ru, tt, zh |
| `designer_launch_error` | 5 | de, en, ru, tt, zh |
| `designer_not_found` | 5 | de, en, ru, tt, zh |
| `designer_reload_error` | 5 | de, en, ru, tt, zh |
| `detail_page_subtitle` | 2 | en, ru |
| `detail_page_title` | 2 | en, ru |
| `dialog_add_class` | 5 | de, en, ru, tt, zh |
| `dialog_edit_class` | 5 | de, en, ru, tt, zh |
| `edit_mapping` | 2 | en, ru |
| `entity_added_to_scene` | 2 | en, ru |
| `entity_alias_calias` | 2 | en, ru |
| `entity_class` | 5 | de, en, ru, tt, zh |
| `entity_created` | 5 | de, en, ru, tt, zh |
| `entity_info` | 5 | de, en, ru, tt, zh |
| `entity_name_cname` | 2 | en, ru |
| `entity_page_subtitle` | 5 | de, en, ru, tt, zh |
| `entity_page_title` | 5 | de, en, ru, tt, zh |
| `entity_types` | 5 | de, en, ru, tt, zh |
| `err_create_method` | 5 | de, en, ru, tt, zh |
| `err_no_db_connection` | 5 | de, en, ru, tt, zh |
| `err_save_method` | 5 | de, en, ru, tt, zh |
| `err_translations_refresh_failed` | 5 | de, en, ru, tt, zh |
| `error` | 5 | de, en, ru, tt, zh |
| `error_class_exists` | 5 | de, en, ru, tt, zh |
| `error_composition_exists` | 5 | de, en, ru, tt, zh |
| `error_connection` | 5 | de, en, ru, tt, zh |
| `error_copy_failed` | 5 | de, en, ru, tt, zh |
| `error_db_connection` | 5 | de, en, ru, tt, zh |
| `error_dual_interface_role` | 5 | de, en, ru, tt, zh |
| `error_ext_table_prepare` | 5 | de, en, ru, tt, zh |
| `error_fetch_data` | 2 | en, ru |
| `error_load_import_settings` | 5 | de, en, ru, tt, zh |
| `error_no_config_rights` | 5 | de, en, ru, tt, zh |
| `error_no_entity_alias` | 5 | de, en, ru, tt, zh |
| `error_no_source_fields` | 5 | de, en, ru, tt, zh |
| `error_no_tables_in_db` | 5 | de, en, ru, tt, zh |
| `error_prod_entity_delete` | 5 | de, en, ru, tt, zh |
| `error_prod_field_delete` | 5 | de, en, ru, tt, zh |
| `error_read_file` | 5 | de, en, ru, tt, zh |
| `error_rename_prod` | 5 | de, en, ru, tt, zh |
| `error_rename_table` | 5 | de, en, ru, tt, zh |
| `error_save_field` | 5 | de, en, ru, tt, zh |
| `error_save_import_settings` | 5 | de, en, ru, tt, zh |
| `error_unsupported_format` | 5 | de, en, ru, tt, zh |
| `error_user_not_found` | 5 | de, en, ru, tt, zh |
| `errors` | 2 | en, ru |
| `event_name` | 5 | de, en, ru, tt, zh |
| `execute_page_subtitle` | 2 | en, ru |
| `execute_page_title` | 2 | en, ru |
| `fast_table_preview` | 2 | en, ru |
| `field_active` | 5 | de, en, ru, tt, zh |
| `field_alias` | 5 | de, en, ru, tt, zh |
| `field_alis` | 5 | de, en, ru, tt, zh |
| `field_base_class` | 5 | de, en, ru, tt, zh |
| `field_baseclass_legacy` | 5 | de, en, ru, tt, zh |
| `field_binding` | 5 | de, en, ru, tt, zh |
| `field_child_entity` | 5 | de, en, ru, tt, zh |
| `field_class` | 5 | de, en, ru, tt, zh |
| `field_class_name` | 5 | de, en, ru, tt, zh |
| `field_code` | 5 | de, en, ru, tt, zh |
| `field_control_type` | 5 | de, en, ru, tt, zh |
| `field_created` | 2 | en, ru |
| `field_datasource` | 5 | de, en, ru, tt, zh |
| `field_decimals` | 5 | de, en, ru, tt, zh |
| `field_description` | 5 | de, en, ru, tt, zh |
| `field_detail` | 5 | de, en, ru, tt, zh |
| `field_end_date` | 5 | de, en, ru, tt, zh |
| `field_entity` | 5 | de, en, ru, tt, zh |
| `field_entity_class` | 5 | de, en, ru, tt, zh |
| `field_filter` | 5 | de, en, ru, tt, zh |

_… и ещё 353 ключей._

---

_Конец карты БД. Для получения деталей по конкретной таблице — запросите SQL-дамп или конкретные строки._
