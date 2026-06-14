# Дамп структуры базы данных

- **База данных:** mozart_erp
- **Хост:** localhost
- **Дата экспорта:** 2026-06-09T20:59:53.275628
- **Схемы:** ext, meta, data, auth, autodoc, lang, public

## Схема `ext`

### Таблицы

#### `ext_account`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_account_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| calias | character varying(100) | ✅ |  |  | None |
| description | text | ✅ |  |  | None |
| parent_account_id | integer | ✅ |  |  | None |
| is_group | boolean | ✅ | false |  | None |

**Первичный ключ:** `id`

---

#### `ext_account_turnover`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_account_turnover_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| account_id | integer | ✅ |  |  | None |
| doc_instance_id | integer | ✅ |  |  | None |
| doc_child_entitytype_id | integer | ✅ |  |  | None |
| doc_line_instance_id | integer | ✅ |  |  | None |
| debit_aspect_id | integer | ✅ |  |  | None |
| credit_aspect_id | integer | ✅ |  |  | None |
| amount | numeric(15,0) | ✅ |  |  | None |
| turnover_date | date | ✅ |  |  | None |
| period | character varying(7) | ✅ |  |  | None |
| comment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_aspect`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_aspect_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| account_id | integer | ✅ |  |  | None |
| calias | character varying(50) | ✅ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| is_monetary | boolean | ✅ | false |  | None |
| description | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_aspect_chart_binding`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_aspect_chart_binding_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| aspect_id | integer | ✅ |  |  | None |
| chart_id | integer | ✅ |  |  | None |
| chart_account_id | integer | ✅ |  |  | None |
| is_default | boolean | ✅ | false |  | None |
| mcomment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_aspect_daily`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_aspect_daily_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| aspect_id | integer | ✅ |  |  | None |
| chart_binding_id | integer | ✅ |  |  | None |
| date | date | ✅ |  |  | None |
| in_debet | numeric(15,0) | ✅ |  |  | None |
| in_kredit | numeric(15,0) | ✅ |  |  | None |
| turnover_debet | numeric(15,0) | ✅ |  |  | None |
| turnover_kredit | numeric(15,0) | ✅ |  |  | None |
| out_debet | numeric(15,0) | ✅ |  |  | None |
| out_kredit | numeric(15,0) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_asset_movement`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_asset_movement_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| account_id | integer | ✅ |  |  | None |
| to_employee_id | integer | ✅ |  |  | None |
| to_location | character varying(255) | ✅ |  |  | None |
| movement_date | date | ✅ |  |  | None |
| return_date | date | ✅ |  |  | None |
| comment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_assignment`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_assignment_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| resolution_id | integer | ✅ |  |  | None |
| assignee_user_id | integer | ✅ |  |  | None |
| role_type | character varying(20) | ✅ |  |  | None |
| description | text | ✅ |  |  | None |
| deadline | date | ✅ |  |  | None |
| finished_at | timestamp without time zone | ✅ |  |  | None |
| status | character varying(20) | ✅ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |
| step_instance_id | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_assignment_report`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_assignment_report_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| assignment_id | integer | ✅ |  |  | None |
| author_user_id | integer | ✅ |  |  | None |
| report_text | text | ✅ |  |  | None |
| status | character varying(20) | ✅ | 'SUBMITTED'::character varying |  | None |

**Первичный ключ:** `id`

---

#### `ext_assignment_template`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_assignment_template_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| code | character varying(100) | ✅ |  |  | None |
| default_deadline_days | integer | ✅ |  |  | None |
| is_active | boolean | ✅ | false |  | None |
| sort_order | integer | ✅ |  |  | None |
| mcomment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_bik`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_bik_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |
| bic | character varying(255) | ✅ |  |  | None |
| participantinfo_namep | character varying(255) | ✅ |  |  | None |
| participantinfo_regn | character varying(255) | ✅ |  |  | None |
| participantinfo_cntrcd | character varying(255) | ✅ |  |  | None |
| participantinfo_rgn | character varying(255) | ✅ |  |  | None |
| participantinfo_ind | character varying(255) | ✅ |  |  | None |
| participantinfo_tnp | character varying(255) | ✅ |  |  | None |
| participantinfo_nnp | character varying(255) | ✅ |  |  | None |
| participantinfo_adr | character varying(255) | ✅ |  |  | None |
| participantinfo_datein | character varying(255) | ✅ |  |  | None |
| participantinfo_pttype | character varying(255) | ✅ |  |  | None |
| participantinfo_srvcs | character varying(255) | ✅ |  |  | None |
| participantinfo_xchtype | character varying(255) | ✅ |  |  | None |
| participantinfo_uid | character varying(255) | ✅ |  |  | None |
| participantinfo_participantstatus | character varying(255) | ✅ |  |  | None |
| participantinfo_rstrlist_rstr | character varying(255) | ✅ |  |  | None |
| participantinfo_rstrlist_rstrdate | character varying(255) | ✅ |  |  | None |
| accounts_account | character varying(255) | ✅ |  |  | None |
| accounts_regulationaccounttype | character varying(255) | ✅ |  |  | None |
| accounts_ck | character varying(255) | ✅ |  |  | None |
| accounts_accountcbrbic | character varying(255) | ✅ |  |  | None |
| accounts_datein | character varying(255) | ✅ |  |  | None |
| accounts_accountstatus | character varying(255) | ✅ |  |  | None |
| data_hash | character varying(32) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_chart_account`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_chart_account_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| chart_id | integer | ✅ |  |  | None |
| code | character varying(20) | ✅ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| account_type | character varying(2) | ✅ |  |  | None |
| parent_id | integer | ✅ |  |  | None |
| is_active | boolean | ✅ | false |  | None |
| mcomment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_chart_account_comment`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_chart_account_comment_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| chart_account_id | integer | ✅ |  |  | None |
| source | character varying(255) | ✅ |  |  | None |
| section | character varying(255) | ✅ |  |  | None |
| comment_text | text | ✅ |  |  | None |
| doc_url | character varying(500) | ✅ |  |  | None |
| file_data | bytea | ✅ |  |  | None |
| file_data_name | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_chart_of_accounts`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_chart_of_accounts_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| calias | character varying(100) | ✅ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |
| is_active | boolean | ✅ | false |  | None |
| mcomment | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_city`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_cityes_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| citizent | integer | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_city_copy`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_city_copy_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| citizent | integer | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_dept`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_dept_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(150) | ✅ |  |  | None |
| code | character varying(50) | ✅ |  |  | None |
| parentid | integer | ✅ |  |  | None |
| chief_staff_id | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_doc_file`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_doc_file_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| doc_instance_id | integer | ✅ |  |  | None |
| file_data | bytea | ✅ |  |  | None |
| file_data_name | character varying(255) | ✅ |  |  | None |
| file_size | integer | ✅ |  |  | None |
| mime_type | character varying(100) | ✅ |  |  | None |
| description | text | ✅ |  |  | None |
| uploaded_by_user_id | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_employee`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_employee_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(150) | ✅ |  |  | None |
| code | character varying(50) | ✅ |  |  | None |
| salary_rate | numeric(15,0) | ✅ |  |  | None |
| parentid | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_external_contact`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_external_contact_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(500) | ✅ |  |  | None |
| short_name | character varying(255) | ✅ |  |  | None |
| contact_type | character varying(1) | ✅ |  |  | None |
| inn | character varying(20) | ✅ |  |  | None |
| phone | character varying(50) | ✅ |  |  | None |
| email | character varying(255) | ✅ |  |  | None |
| address | text | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_incoming_doc`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_incoming_doc_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |
| doc_number | character varying(100) | ✅ |  |  | None |
| doc_date | date | ✅ |  |  | None |
| external_number | character varying(100) | ✅ |  |  | None |
| external_date | date | ✅ |  |  | None |
| sender_contact_id | integer | ✅ |  |  | None |
| subject | character varying(500) | ✅ |  |  | None |
| delivery_method | character varying(20) | ✅ |  |  | None |
| is_urgent | boolean | ✅ | false |  | None |

**Первичный ключ:** `id`

---

#### `ext_invoice`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_invoice_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_invoice_line`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_invoice_line_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| idinvoice | integer | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_memo`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_memo_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| doc_number | character varying(50) | ✅ |  |  | None |
| doc_date | date | ✅ |  |  | None |
| subject | character varying(255) | ✅ |  |  | None |
| content | text | ✅ |  |  | None |
| author_staff_id | integer | ✅ |  |  | None |
| status | character varying(50) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_outgoing_doc`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_outgoing_doc_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |
| doc_number | character varying(100) | ✅ |  |  | None |
| doc_date | date | ✅ |  |  | None |
| recipient_contact_id | integer | ✅ |  |  | None |
| subject | character varying(500) | ✅ |  |  | None |
| response_to_doc_id | integer | ✅ |  |  | None |
| signed_by_user_id | integer | ✅ |  |  | None |
| sent_date | date | ✅ |  |  | None |
| delivery_method | character varying(20) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_person`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_person_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| clastname | character varying(255) | ❌ |  |  | None |
| cfirstname | character varying(255) | ❌ |  |  | None |
| csecondname | character varying(255) | ✅ |  |  | None |
| dbirthdate | date | ❌ |  |  | None |
| cinn | character varying(20) | ✅ |  |  | None |
| mcomment | text | ✅ |  |  | None |
| sex | integer | ✅ |  |  | None |
| sex1 | integer | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_report_file`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_report_file_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| report_id | integer | ✅ |  |  | None |
| file_data | bytea | ✅ |  |  | None |
| file_data_name | character varying(255) | ✅ |  |  | None |
| file_size | integer | ✅ |  |  | None |
| mime_type | character varying(100) | ✅ |  |  | None |
| description | text | ✅ |  |  | None |
| uploaded_by_user_id | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_resolution`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_resolution_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| doc_instance_id | integer | ✅ |  |  | None |
| author_user_id | integer | ✅ |  |  | None |
| on_behalf_user_id | integer | ✅ |  |  | None |
| resolution_text | text | ✅ |  |  | None |
| deadline | date | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_route`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_route_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| cname | character varying(150) | ✅ |  |  | None |
| code | character varying(50) | ✅ |  |  | None |
| doc_type_id | integer | ✅ |  |  | None |
| is_active | boolean | ✅ | false |  | None |

**Первичный ключ:** `id`

---

#### `ext_route_instance`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_route_instance_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| template_id | integer | ✅ |  |  | None |
| doc_instance_id | integer | ✅ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |
| started_at | timestamp without time zone | ✅ |  |  | None |
| finished_at | timestamp without time zone | ✅ |  |  | None |
| status | character varying(20) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_route_step`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_route_step_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| route_id | integer | ✅ |  |  | None |
| step_order | integer | ✅ |  |  | None |
| step_name | character varying(100) | ✅ |  |  | None |
| assign_type | character varying(50) | ✅ |  |  | None |
| assign_target | character varying(255) | ✅ |  |  | None |
| scope | character varying(20) | ✅ |  |  | None |
| scope_target | character varying(255) | ✅ |  |  | None |
| time_limit_days | integer | ✅ |  |  | None |
| next_step_on_reject | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_route_step_instance`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_route_step_instance_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| route_instance_id | integer | ✅ |  |  | None |
| step_template_id | integer | ✅ |  |  | None |
| parent_step_id | integer | ✅ |  |  | None |
| assignee_user_id | integer | ✅ |  |  | None |
| delegate_to_user_id | integer | ✅ |  |  | None |
| started_at | timestamp without time zone | ✅ |  |  | None |
| deadline | timestamp without time zone | ✅ |  |  | None |
| finished_at | timestamp without time zone | ✅ |  |  | None |
| decision | character varying(20) | ✅ |  |  | None |
| comment | text | ✅ |  |  | None |
| status | character varying(20) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_staff_position`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext.ext_staff_position_id_seq'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| dept_id | integer | ✅ |  |  | None |
| employee_id | integer | ✅ |  |  | None |
| person_id | integer | ✅ |  |  | None |
| rate | numeric(15,0) | ✅ |  |  | None |
| is_chief | boolean | ✅ | false |  | None |
| date_from | date | ✅ |  |  | None |
| date_to | date | ✅ |  |  | None |
| balanceunit_id | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_адрес`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext."ext_адрес_id_seq"'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| full_address | character varying(500) | ✅ |  |  | None |
| aoguid | character varying(36) | ✅ |  |  | None |
| house | character varying(50) | ✅ |  |  | None |
| building | character varying(50) | ✅ |  |  | None |
| flat | character varying(50) | ✅ |  |  | None |
| country | character varying(100) | ✅ |  |  | None |
| region | character varying(100) | ✅ |  |  | None |
| district | character varying(100) | ✅ |  |  | None |
| city | character varying(150) | ✅ |  |  | None |
| locality | character varying(150) | ✅ |  |  | None |
| street | character varying(150) | ✅ |  |  | None |
| additional | character varying(100) | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_города`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext."ext_города_id_seq"'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| жителей | integer | ✅ |  |  | None |
| square | integer | ✅ |  |  | None |
| citizent | integer | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_пол`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext."ext_пол_id_seq"'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| sex | character varying(255) | ✅ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_стр_накл`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext."ext_стр_накл_id_seq"'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |

**Первичный ключ:** `id`

---

#### `ext_улицы`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('ext."ext_улицы_id_seq"'::regclass) | ✅ | None |
| versionid | integer | ❌ |  |  | None |
| sourceid | character varying(255) | ✅ |  |  | None |

**Первичный ключ:** `id`

---
## Схема `meta`

### Таблицы

#### `account_aspects`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.account_aspects_id_seq'::regclass) | ✅ |  |
| account_entitytype_id | integer | ❌ |  |  |  |
| aspect_entitytype_id | integer | ❌ |  |  |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| is_monetary | boolean | ✅ | false |  |  |
| ref_chart_entitytype_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `account_aspects_account_entitytype_id_calias_key`: (`account_entitytype_id, calias`)

---

#### `calculations`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.calculations_id_seq'::regclass) | ✅ |  |
| calias | character varying(100) | ❌ |  |  |  |
| cfilepath | text | ❌ |  |  |  |
| chash | character(64) | ✅ |  |  |  |
| tlastupdate | timestamp without time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `calculations_calias_key`: (`calias`)

---

#### `class_composition_templates`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.class_composition_templates_id_seq'::regclass) | ✅ |  |
| class_id | integer | ❌ |  |  |  |
| child_entitytype_id | integer | ❌ |  |  |  |
| role_id | integer | ❌ |  |  |  |
| c_link_fieldname | character varying(63) | ❌ |  |  |  |
| isortorder | integer | ❌ | 10 |  |  |
| is_required | boolean | ❌ | true |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `class_composition_templates_class_id_child_entitytype_id_ro_key`: (`class_id, child_entitytype_id, role_id`)

---

#### `class_field_templates`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.class_field_templates_id_seq'::regclass) | ✅ |  |
| class_id | integer | ❌ |  |  |  |
| field_name | character varying(63) | ❌ |  |  |  |
| field_type | character(1) | ❌ |  |  |  |
| calias | character varying(255) | ❌ |  |  |  |
| nlength | integer | ✅ | 255 |  |  |
| is_indexed | boolean | ✅ | true |  |  |
| is_required | boolean | ✅ | false |  |  |
| ref_entitytype_id | integer | ✅ |  |  |  |
| sort_order | integer | ✅ | 10 |  |  |
| is_system | boolean | ✅ | false |  |  |
| ref_class_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `class_field_templates_class_id_field_name_key`: (`class_id, field_name`)

**Check-ограничения:**
- `chk_ref_single`: CHECK ((((ref_entitytype_id IS NOT NULL) AND (ref_class_id IS NULL)) OR ((ref_entitytype_id IS NULL) AND (ref_class_id IS NOT NULL)) OR ((ref_entitytype_id IS NULL) AND (ref_class_id IS NULL))))

---

#### `composition_roles`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.composition_roles_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `composition_roles_calias_key`: (`calias`)

---

#### `delegate_rules`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.delegate_rules_id_seq'::regclass) | ✅ |  |
| principal_user_id | integer | ❌ |  |  |  |
| allowed_delegate_id | integer | ❌ |  |  |  |
| scope | character varying(20) | ❌ | 'ALL'::character varying |  |  |
| scope_entitytype_id | integer | ✅ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| mcomment | text | ✅ |  |  |  |
| created_by_user_id | integer | ✅ |  |  |  |
| created_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `delegate_rules_principal_user_id_allowed_delegate_id_scope__key`: (`principal_user_id, allowed_delegate_id, scope, scope_entitytype_id`)

**Check-ограничения:**
- `delegate_rules_scope_check`: CHECK (((scope)::text = ANY ((ARRAY['ALL'::character varying, 'DOC_CLASS'::character varying, 'ENTITY_TYPE'::character varying])::text[])))

---

#### `doc_numberers`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.doc_numberers_id_seq'::regclass) | ✅ |  |
| entitytype_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ❌ |  |  |  |
| prefix | character varying(20) | ✅ |  |  |  |
| next_number | bigint | ❌ | 1 |  |  |
| pattern | character varying(100) | ✅ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| current_year | integer | ✅ | EXTRACT(year FROM now()) |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `doc_numberers_entitytype_id_balanceunit_id_key`: (`entitytype_id, balanceunit_id`)

---

#### `doc_route_bindings`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.doc_route_bindings_id_seq'::regclass) | ✅ |  |
| entitytype_id | integer | ❌ |  |  |  |
| route_template_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ❌ |  |  |  |
| is_default | boolean | ❌ | false |  |  |
| is_active | boolean | ❌ | true |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `doc_route_bindings_entitytype_id_route_template_id_balanceu_key`: (`entitytype_id, route_template_id, balanceunit_id`)

---

#### `doc_settings`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.doc_settings_id_seq'::regclass) | ✅ |  |
| balanceunit_id | integer | ✅ |  |  |  |
| setting_key | character varying(100) | ❌ |  |  |  |
| setting_value | text | ✅ |  |  |  |
| description | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `doc_settings_balanceunit_id_setting_key_key`: (`balanceunit_id, setting_key`)

---

#### `entity_classes`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entity_classes_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `entity_classes_calias_key`: (`calias`)

---

#### `entity_composition`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entity_composition_id_seq'::regclass) | ✅ |  |
| parent_entityid | integer | ❌ |  |  |  |
| child_entityid | integer | ❌ |  |  |  |
| role_id | integer | ❌ |  |  |  |
| c_link_fieldname | character varying(63) | ❌ |  |  |  |
| isortorder | integer | ✅ | 10 |  |  |
| from_template_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `uk_entity_comp_parent_child_field`: (`parent_entityid, child_entityid, c_link_fieldname`)
- `uk_entity_comp_role`: (`parent_entityid, child_entityid, role_id`)

---

#### `entity_ref_rules`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entity_ref_rules_id_seq'::regclass) | ✅ |  |
| reftypeid | integer | ❌ |  |  |  |
| entitytypeid | integer | ❌ |  |  |  |
| role_source_entityid | integer | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `uk_ref_rules`: (`reftypeid, entitytypeid`)

---

#### `entity_ref_types`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entity_ref_types_id_seq'::regclass) | ✅ |  |
| cname | character varying(255) | ❌ |  |  |  |
| calias | character varying(50) | ❌ |  |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `entity_ref_types_calias_key`: (`calias`)

---

#### `entitytype_bu_access`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| entitytype_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ❌ |  |  |  |
| is_active | boolean | ❌ | true |  |  |

**Первичный ключ:** `entitytype_id, balanceunit_id`

---

#### `entitytype_visibility`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entitytype_visibility_id_seq'::regclass) | ✅ |  |
| entitytype_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ❌ |  |  |  |
| visibility_policy | character(1) | ❌ | 'I'::bpchar |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `entitytype_visibility_entitytype_id_balanceunit_id_key`: (`entitytype_id, balanceunit_id`)

---

#### `entitytypes`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.entitytypes_id_seq'::regclass) | ✅ |  |
| cname | character varying(255) | ❌ |  |  |  |
| calias | character varying(50) | ❌ |  |  |  |
| cbaseclass | character varying(20) | ❌ |  |  |  |
| lisdependent | boolean | ✅ | false |  |  |
| lishierarchy | boolean | ✅ | false |  |  |
| lisversioned | boolean | ✅ | true |  |  |
| isecuritystrategy | integer | ✅ | 1 |  |  |
| class_id | integer | ✅ |  |  |  |
| mcomment | text | ✅ |  |  |  |
| status_id | integer | ✅ | 1 |  |  |
| is_system | boolean | ❌ | false |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `entitytypes_calias_key`: (`calias`)

---

#### `field_types`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| ccode | character(1) | ❌ |  |  |  |
| cname | character varying(50) | ❌ |  |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `ccode`

---

#### `fields`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.fields_id_seq'::regclass) | ✅ |  |
| entitytypeid | integer | ✅ |  |  |  |
| cfieldname | character varying(63) | ❌ |  |  |  |
| calias | character varying(100) | ❌ |  |  |  |
| cfieldtype | character(1) | ❌ |  |  |  |
| lisrequired | boolean | ✅ | false |  |  |
| lisindexed | boolean | ✅ | false |  |  |
| nlength | integer | ✅ | 255 |  |  |
| ndecimals | integer | ✅ | 0 |  |  |
| isortorder | integer | ✅ | 10 |  |  |
| ref_entitytypeid | integer | ✅ |  |  |  |
| mcomment | text | ✅ |  |  |  |
| status_id | integer | ✅ | 1 |  |  |
| is_system | boolean | ✅ | false |  |  |

**Первичный ключ:** `id`

---

#### `form_elements`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.form_elements_id_seq'::regclass) | ✅ |  |
| formid | integer | ✅ |  |  |  |
| parentid | integer | ✅ |  |  |  |
| calias | character varying(50) | ✅ |  |  |  |
| cclass | character varying(20) | ✅ |  |  |  |
| itaborder | integer | ✅ |  |  |  |
| cdatasource | character varying(100) | ✅ |  |  |  |
| mproperties_json | text | ✅ |  |  |  |
| isortorder | integer | ✅ | 10 |  |  |
| lisactive | boolean | ✅ | true |  |  |

**Первичный ключ:** `id`

---

#### `forms`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.forms_id_seq'::regclass) | ✅ |  |
| ientitytypeid | integer | ✅ |  |  |  |
| calias | character varying(50) | ✅ |  |  |  |
| cname | character varying(255) | ✅ |  |  |  |
| mstate_json | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `forms_calias_key`: (`calias`)

---

#### `import_links`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_links_id_seq'::regclass) | ✅ |  |
| profile_id | integer | ❌ |  |  |  |
| source_table_id | integer | ❌ |  |  |  |
| target_entity_id | integer | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_links_profile_id_source_table_id_target_entity_id_key`: (`profile_id, source_table_id, target_entity_id`)

---

#### `import_mappings`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_mappings_id_seq'::regclass) | ✅ |  |
| link_id | integer | ❌ |  |  |  |
| source_field | character varying(255) | ❌ |  |  |  |
| target_field | character varying(255) | ❌ |  |  |  |
| field_type | character varying(1) | ✅ | 'C'::character varying |  |  |
| field_length | integer | ✅ | 255 |  |  |
| is_source_id | boolean | ✅ | false |  |  |
| is_reference | boolean | ✅ | false |  |  |
| ref_src_table | character varying(255) | ✅ |  |  |  |
| ref_src_key_field | character varying(255) | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_mappings_link_id_source_field_key`: (`link_id, source_field`)

---

#### `import_profiles`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_profiles_id_seq'::regclass) | ✅ |  |
| profile_name | character varying(255) | ❌ |  |  |  |
| source_type | character varying(20) | ❌ |  |  |  |
| source_path | text | ❌ |  |  |  |
| created_at | timestamp with time zone | ✅ | now() |  |  |
| updated_at | timestamp with time zone | ✅ | now() |  |  |
| file_format | character varying(10) | ✅ |  |  |  |
| db_type | character varying(20) | ✅ |  |  |  |
| db_host | character varying(255) | ✅ |  |  |  |
| db_port | integer | ✅ |  |  |  |
| db_name | character varying(255) | ✅ |  |  |  |
| db_user | character varying(255) | ✅ |  |  |  |
| db_pass | character varying(255) | ✅ |  |  |  |
| import_mode | character varying(20) | ✅ | 'append'::character varying |  |  |

**Первичный ключ:** `id`

---

#### `import_source_links`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_source_links_id_seq'::regclass) | ✅ |  |
| profile_id | integer | ❌ |  |  |  |
| source_table_id | integer | ❌ |  |  |  |
| source_field | character varying(255) | ❌ |  |  |  |
| ref_table_id | integer | ❌ |  |  |  |
| ref_field | character varying(255) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_source_links_profile_id_source_table_id_source_field_key`: (`profile_id, source_table_id, source_field`)

---

#### `import_source_references`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_source_references_id_seq'::regclass) | ✅ |  |
| source_table_id | integer | ❌ |  |  |  |
| source_field | character varying(255) | ❌ |  |  |  |
| ref_table_id | integer | ❌ |  |  |  |
| ref_key_field | character varying(255) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_source_references_source_table_id_source_field_key`: (`source_table_id, source_field`)

---

#### `import_source_tables`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_source_tables_id_seq'::regclass) | ✅ |  |
| profile_id | integer | ❌ |  |  |  |
| table_name | character varying(255) | ❌ |  |  |  |
| row_count | integer | ✅ |  |  |  |
| sample_data | jsonb | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_source_tables_profile_id_table_name_key`: (`profile_id, table_name`)

---

#### `import_sources`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_sources_id_seq'::regclass) | ✅ |  |
| entitytypeid | integer | ❌ |  |  |  |
| source_name | character varying(255) | ✅ |  |  |  |
| source_type | character varying(20) | ❌ |  |  |  |
| source_path | text | ❌ |  |  |  |
| format | character varying(50) | ✅ |  |  |  |
| id_field | character varying(63) | ❌ |  |  |  |
| last_import | timestamp without time zone | ✅ |  |  |  |
| created_at | timestamp without time zone | ✅ | now() |  |  |
| updated_at | timestamp without time zone | ✅ | now() |  |  |
| scene_json | jsonb | ✅ |  |  |  |
| config_json | jsonb | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_sources_entitytypeid_key`: (`entitytypeid`)

---

#### `import_target_entities`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.import_target_entities_id_seq'::regclass) | ✅ |  |
| profile_id | integer | ❌ |  |  |  |
| entity_id | integer | ❌ |  |  |  |
| entity_name | character varying(255) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `import_target_entities_profile_id_entity_id_key`: (`profile_id, entity_id`)

---

#### `menu`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.menu_id_seq'::regclass) | ✅ |  |
| roleid | integer | ✅ |  |  |  |
| parentid | integer | ✅ |  |  |  |
| cname | character varying(100) | ❌ |  |  |  |
| calias | character varying(50) | ✅ |  |  |  |
| ientitytypeid | integer | ✅ |  |  |  |
| isortorder | integer | ✅ | 10 |  |  |
| iformid | integer | ✅ |  |  |  |
| lisactive | boolean | ✅ | true |  |  |
| oicon | bytea | ✅ |  |  |  |
| cicon_type | character varying(10) | ✅ | 'png'::character varying |  |  |
| copentype | character varying(20) | ✅ | 'main'::character varying |  |  |
| openparams_json | jsonb | ✅ |  |  |  |

**Первичный ключ:** `id`

---

#### `object_statuses`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.object_statuses_id_seq'::regclass) | ✅ |  |
| code | character varying(20) | ❌ |  |  |  |
| name | character varying(50) | ❌ |  |  |  |
| description | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `object_statuses_code_key`: (`code`)

---

#### `register_dimensions`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.register_dimensions_id_seq'::regclass) | ✅ |  |
| register_id | integer | ❌ |  |  |  |
| dimension_order | integer | ❌ |  |  |  |
| entitytype_id | integer | ❌ |  |  |  |
| is_required | boolean | ✅ | true |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `register_dimensions_register_id_dimension_order_key`: (`register_id, dimension_order`)

---

#### `register_resources`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.register_resources_id_seq'::regclass) | ✅ |  |
| register_id | integer | ❌ |  |  |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| resource_type | character(1) | ❌ |  |  |  |
| aspect_entitytype_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `register_resources_register_id_calias_key`: (`register_id, calias`)

---

#### `registers`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.registers_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| ctype | character(1) | ❌ | 'B'::bpchar |  |  |
| periodicity | character(1) | ❌ | 'D'::bpchar |  |  |
| is_active | boolean | ✅ | true |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `registers_calias_key`: (`calias`)

---

#### `route_step_templates`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.route_step_templates_id_seq'::regclass) | ✅ |  |
| route_template_id | integer | ❌ |  |  |  |
| parent_step_id | integer | ✅ |  |  |  |
| step_order | integer | ❌ |  |  |  |
| step_name | character varying(255) | ❌ |  |  |  |
| assign_type | character varying(20) | ❌ |  |  |  |
| assign_target | character varying(255) | ✅ |  |  |  |
| is_optional | boolean | ❌ | false |  |  |
| time_limit_days | integer | ✅ |  |  |  |
| scope | character varying(20) | ✅ | 'ALL'::character varying |  |  |
| scope_target | character varying(255) | ✅ |  |  |  |
| next_step_on_reject | integer | ✅ |  |  |  |
| notify_on_assign | boolean | ❌ | true |  |  |
| sort_order | integer | ❌ | 10 |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Check-ограничения:**
- `route_step_templates_assign_type_check`: CHECK (((assign_type)::text = ANY ((ARRAY['STAFF'::character varying, 'RULE'::character varying, 'ROLE'::character varying])::text[])))
- `route_step_templates_scope_check`: CHECK (((scope)::text = ANY ((ARRAY['ALL'::character varying, 'BU'::character varying, 'DEPT'::character varying])::text[])))

---

#### `route_template_bu_access`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| route_template_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ❌ |  |  |  |
| is_active | boolean | ❌ | true |  |  |

**Первичный ключ:** `route_template_id, balanceunit_id`

---

#### `route_templates`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.route_templates_id_seq'::regclass) | ✅ |  |
| calias | character varying(100) | ❌ |  |  |  |
| cname | character varying(500) | ❌ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| mcomment | text | ✅ |  |  |  |
| created_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `route_templates_calias_key`: (`calias`)

---

#### `sys_params`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.sys_params_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ✅ |  |  |  |
| ctype | character(1) | ❌ |  |  |  |
| isystem | boolean | ✅ | true |  |  |
| mdefault_value | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `sys_params_calias_key`: (`calias`)

---

#### `system_entity_roles`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('meta.system_entity_roles_id_seq'::regclass) | ✅ |  |
| entitytype_id | integer | ❌ |  |  |  |
| balanceunit_id | integer | ✅ |  |  |  |
| role_code | character varying(50) | ❌ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `system_entity_roles_entitytype_id_balanceunit_id_role_code_key`: (`entitytype_id, balanceunit_id, role_code`)

---

### Хранимые процедуры, функции и триггеры

#### Procedure `load_chart_ifrs`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.load_chart_ifrs()
 LANGUAGE plpgsql
AS $procedure$
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
    
    -- 1. СОЗДАЁМ ПЛАН СЧЕТОВ МСФО
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth)
    VALUES (v_entity_chart_id, now())
    RETURNING id INTO v_inst_id;
    
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start)
    VALUES (v_inst_id, 'Международный план счетов (МСФО)', 'Active', now())
    RETURNING id INTO v_ver_id;
    
    INSERT INTO ext.ext_chart_of_accounts (versionid, cname, calias, is_active, mcomment)
    VALUES (v_ver_id, 'МСФО', 'IFRS', true, 
            'План счетов по международным стандартам финансовой отчётности (IFRS)');
    
    v_chart_instance_id := v_inst_id;
    
    -- ========================================================================
    -- АКТИВЫ (ASSETS)
    -- ========================================================================
    
    -- Внеоборотные активы (Non-current assets)
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'PPE — Основные средства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'PPE', 'Property, Plant and Equipment', 'A', true, 'Внеоборотные активы');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'PPE.Cost — Первоначальная стоимость', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'PPE.Cost', 'Первоначальная стоимость ОС', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'PPE.Depr — Накопленная амортизация', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'PPE.Depr', 'Накопленная амортизация', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Intangibles — Нематериальные активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Intangibles', 'Нематериальные активы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Goodwill — Гудвилл', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Goodwill', 'Деловая репутация', 'A', true);

    -- Оборотные активы (Current assets)
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Inventory — Запасы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'INV', 'Товарно-материальные запасы', 'A', true, 'Оборотные активы');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Inventory.Raw — Сырьё и материалы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'INV.Raw', 'Сырьё и материалы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Inventory.WIP — Незавершённое производство', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'INV.WIP', 'Незавершённое производство', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Inventory.FG — Готовая продукция', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'INV.FG', 'Готовая продукция', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'TradeReceivables — Дебиторская задолженность', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'AR', 'Расчёты с покупателями', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'OtherReceivables — Прочая дебиторка', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'AR.Other', 'Прочая дебиторская задолженность', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Prepayments — Авансы выданные', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Prepayments', 'Авансы выданные поставщикам', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Cash — Денежные средства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'CASH', 'Денежные средства', 'A', true, 'Касса, расчётные счета');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Cash.Bank — Банковские счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'CASH.Bank', 'Расчётные счета', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Cash.Petty — Касса', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'CASH.Petty', 'Касса организации', 'A', true);

    -- ========================================================================
    -- ОБЯЗАТЕЛЬСТВА (LIABILITIES)
    -- ========================================================================
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'TradePayables — Кредиторская задолженность', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'AP', 'Расчёты с поставщиками', 'P', true, 'Обязательства');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'OtherPayables — Прочая кредиторка', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'AP.Other', 'Прочая кредиторская задолженность', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'AccruedExpenses — Начисленные обязательства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'AccruedExp', 'Начисленные расходы', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'TaxLiabilities — Налоговые обязательства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'TaxLiability', 'Задолженность по налогам', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'VATPayable — НДС к уплате', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'VAT.Payable', 'НДС подлежащий уплате', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Loans — Займы и кредиты', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Loans', 'Кредиты и займы', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Loans.ShortTerm — Краткосрочные', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Loans.Short', 'Краткосрочные кредиты', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Loans.LongTerm — Долгосрочные', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Loans.Long', 'Долгосрочные кредиты', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'DeferredRevenue — Доходы будущих периодов', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'DeferredRev', 'Доходы будущих периодов', 'P', true);

    -- ========================================================================
    -- КАПИТАЛ (EQUITY)
    -- ========================================================================
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'ShareCapital — Уставный капитал', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'Equity.Capital', 'Уставный капитал', 'P', true, 'Собственный капитал');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'RetainedEarnings — Нераспределённая прибыль', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Equity.Retained', 'Нераспределённая прибыль', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'RevaluationReserve — Резерв переоценки', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Equity.Reval', 'Резерв переоценки ОС', 'P', true);

    -- ========================================================================
    -- ДОХОДЫ (REVENUE)
    -- ========================================================================
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Revenue — Выручка', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'Revenue', 'Доходы от основной деятельности', 'P', true, 'Доходы');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Revenue.Sales — Продажи товаров', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Revenue.Sales', 'Продажи товаров', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'Revenue.Services — Услуги', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Revenue.Services', 'Доходы от услуг', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'OtherIncome — Прочие доходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Revenue.Other', 'Прочие доходы', 'P', true);

    -- ========================================================================
    -- РАСХОДЫ (EXPENSES)
    -- ========================================================================
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'CostOfSales — Себестоимость продаж', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.COGS', 'Себестоимость продаж', 'A', true, 'Расходы');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'SalariesExpense — Расходы на оплату труда', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Salaries', 'Заработная плата', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'DepreciationExpense — Амортизация', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Depr', 'Амортизация ОС', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'RentExpense — Аренда', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Rent', 'Арендная плата', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'UtilitiesExpense — Коммунальные услуги', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Utilities', 'Коммунальные услуги', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'TaxExpense — Налоговые расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Tax', 'Налог на прибыль', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'OtherExpenses — Прочие расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, 'Expense.Other', 'Прочие расходы', 'A', true);

    -- ========================================================================
    -- ЗАБАЛАНСОВЫЕ СЧЕТА (OFF-BALANCE)
    -- ========================================================================
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, 'OffBalance — Забалансовые счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, 'OFF', 'Забалансовые счета', 'A', true, 'Забалансовый учёт');

    RAISE NOTICE 'План счетов МСФО загружен. Создано 32 счета.';
END;
$procedure$

```
---

#### Procedure `load_chart_ras`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.load_chart_ras()
 LANGUAGE plpgsql
AS $procedure$
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
    
    -- 1. СОЗДАЁМ ПЛАН СЧЕТОВ (CHART_OF_ACCOUNTS)
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth)
    VALUES (v_entity_chart_id, now())
    RETURNING id INTO v_inst_id;
    
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start)
    VALUES (v_inst_id, 'Российский план счетов (РСБУ)', 'Active', now())
    RETURNING id INTO v_ver_id;
    
    INSERT INTO ext.ext_chart_of_accounts (versionid, cname, calias, is_active, mcomment)
    VALUES (v_ver_id, 'РСБУ', 'RAS', true, 
            'План счетов бухучёта, утв. Приказом Минфина РФ от 31.10.2000 №94н');
    
    v_chart_instance_id := v_inst_id;
    
    -- 2. СОЗДАЁМ БАЛАНСОВЫЕ СЧЕТА
    -- Раздел I. Внеоборотные активы
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01 — Основные средства', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '01', 'Основные средства', 'A', true, 'Раздел I');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '02 — Амортизация ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '02', 'Амортизация основных средств', 'P', true, 'Раздел I');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '04 — Нематериальные активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '04', 'Нематериальные активы', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '08 — Вложения во внеоборотные активы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '08', 'Вложения во внеоборотные активы', 'A', true);

    -- Раздел II. Производственные запасы
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10 — Материалы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '10', 'Материалы', 'A', true, 'Раздел II');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '19 — НДС по приобретённым ценностям', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '19', 'НДС по приобретённым ценностям', 'A', true);

    -- Раздел III. Затраты
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '20 — Основное производство', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '20', 'Основное производство', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '26 — Общехозяйственные расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '26', 'Общехозяйственные расходы', 'A', true);

    -- Раздел IV. Готовая продукция
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '41 — Товары', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '41', 'Товары', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '43 — Готовая продукция', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '43', 'Готовая продукция', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '44 — Расходы на продажу', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '44', 'Расходы на продажу', 'A', true);

    -- Раздел V. Денежные средства
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '50 — Касса', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '50', 'Касса', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '51 — Расчётные счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '51', 'Расчётные счета', 'A', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '52 — Валютные счета', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '52', 'Валютные счета', 'A', true);

    -- Раздел VI. Расчёты
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60 — Расчёты с поставщиками', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '60', 'Расчёты с поставщиками', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62 — Расчёты с покупателями', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '62', 'Расчёты с покупателями', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68 — Расчёты по налогам', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '68', 'Расчёты по налогам', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '69 — Расчёты по соц.страхованию', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '69', 'Расчёты по соц.страхованию', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '70 — Расчёты по оплате труда', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '70', 'Расчёты по оплате труда', 'P', true);

    -- Раздел VII. Капитал
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '80 — Уставный капитал', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '80', 'Уставный капитал', 'P', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '84 — Нераспределённая прибыль', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '84', 'Нераспределённая прибыль', 'AP', true);

    -- Раздел VIII. Финансовые результаты
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90 — Продажи', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '90', 'Продажи', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '91 — Прочие доходы и расходы', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '91', 'Прочие доходы и расходы', 'AP', true);

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '99 — Прибыли и убытки', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) 
    VALUES (v_ver_id, v_chart_instance_id, '99', 'Прибыли и убытки', 'AP', true);

    -- Забалансовые счета
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '001 — Арендованные ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '001', 'Арендованные ОС', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '002 — ТМЦ на хранении', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '002', 'ТМЦ на хранении', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '006 — Бланки строгой отчётности', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '006', 'Бланки строгой отчётности', 'A', true, 'Забалансовый');

    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '010 — Износ ОС', 'Active', now()) RETURNING id INTO v_ver_id;
    INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active, mcomment) 
    VALUES (v_ver_id, v_chart_instance_id, '010', 'Износ ОС', 'A', true, 'Забалансовый');

    RAISE NOTICE 'План счетов РСБУ загружен.';
END;
$procedure$

```
---

#### Procedure `load_chart_ras_accounts_only`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.load_chart_ras_accounts_only()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_chart_id INTEGER;
    v_inst_id INTEGER;
    v_ver_id INTEGER;
    v_entity_account_id INTEGER;
    v_parent_id INTEGER;
    v_code TEXT;
    v_cname TEXT;
    v_type CHAR(1);
    v_parent_code TEXT;
    v_comment TEXT;
    v_cursor CURSOR FOR
        SELECT * FROM (VALUES
            ('01', 'Основные средства', 'A', NULL, 'Раздел I'),
            ('01.01', 'Основные средства в организации', 'A', '01', NULL),
            ('01.02', 'Выбытие основных средств', 'A', '01', NULL),
            ('02', 'Амортизация основных средств', 'P', NULL, 'Раздел I'),
            ('02.01', 'Амортизация собственных основных средств', 'P', '02', NULL),
            ('04', 'Нематериальные активы', 'A', NULL, NULL),
            ('05', 'Амортизация нематериальных активов', 'P', NULL, NULL),
            ('08', 'Вложения во внеоборотные активы', 'A', NULL, NULL),
            ('08.04', 'Приобретение объектов основных средств', 'A', '08', NULL),
            ('09', 'Отложенные налоговые активы', 'A', NULL, NULL),
            ('10', 'Материалы', 'A', NULL, 'Раздел II'),
            ('10.01', 'Сырьё и материалы', 'A', '10', NULL),
            ('10.03', 'Топливо', 'A', '10', NULL),
            ('10.05', 'Запасные части', 'A', '10', NULL),
            ('10.09', 'Инвентарь и хозяйственные принадлежности', 'A', '10', NULL),
            ('19', 'НДС по приобретённым ценностям', 'A', NULL, NULL),
            ('20', 'Основное производство', 'A', NULL, 'Раздел III'),
            ('26', 'Общехозяйственные расходы', 'A', NULL, NULL),
            ('41', 'Товары', 'A', NULL, 'Раздел IV'),
            ('43', 'Готовая продукция', 'A', NULL, NULL),
            ('44', 'Расходы на продажу', 'A', NULL, NULL),
            ('50', 'Касса', 'A', NULL, 'Раздел V'),
            ('51', 'Расчётные счета', 'A', NULL, NULL),
            ('52', 'Валютные счета', 'A', NULL, NULL),
            ('60', 'Расчёты с поставщиками и подрядчиками', 'A', NULL, 'Раздел VI'),  -- AP -> A
            ('60.01', 'Расчёты с поставщиками', 'P', '60', NULL),
            ('60.02', 'Авансы выданные', 'A', '60', NULL),
            ('62', 'Расчёты с покупателями и заказчиками', 'A', NULL, NULL),  -- AP -> A
            ('62.01', 'Расчёты с покупателями', 'A', '62', NULL),
            ('62.02', 'Авансы полученные', 'P', '62', NULL),
            ('66', 'Расчёты по краткосрочным кредитам и займам', 'P', NULL, NULL),
            ('67', 'Расчёты по долгосрочным кредитам и займам', 'P', NULL, NULL),
            ('68', 'Расчёты по налогам и сборам', 'A', NULL, NULL),  -- AP -> A
            ('68.01', 'НДФЛ', 'P', '68', NULL),
            ('68.02', 'НДС', 'A', '68', NULL),  -- AP -> A
            ('69', 'Расчёты по социальному страхованию и обеспечению', 'A', NULL, NULL),  -- AP -> A
            ('70', 'Расчёты с персоналом по оплате труда', 'P', NULL, NULL),
            ('71', 'Расчёты с подотчётными лицами', 'A', NULL, NULL),  -- AP -> A
            ('76', 'Расчёты с разными дебиторами и кредиторами', 'A', NULL, NULL),  -- AP -> A
            ('80', 'Уставный капитал', 'P', NULL, 'Раздел VII'),
            ('84', 'Нераспределённая прибыль (непокрытый убыток)', 'A', NULL, NULL),  -- AP -> A
            ('90', 'Продажи', 'A', NULL, 'Раздел VIII'),  -- AP -> A
            ('90.01', 'Выручка', 'P', '90', NULL),
            ('90.02', 'Себестоимость продаж', 'A', '90', NULL),
            ('91', 'Прочие доходы и расходы', 'A', NULL, NULL),  -- AP -> A
            ('99', 'Прибыли и убытки', 'A', NULL, NULL),  -- AP -> A
            ('001', 'Арендованные основные средства', 'A', NULL, 'Забалансовый'),
            ('002', 'ТМЦ, принятые на ответственное хранение', 'A', NULL, 'Забалансовый'),
            ('006', 'Бланки строгой отчётности', 'A', NULL, 'Забалансовый'),
            ('010', 'Износ основных средств', 'A', NULL, 'Забалансовый')
        ) AS t(code, cname, account_type, parent_code, comment);
BEGIN
    -- Получаем versionid из ext.ext_chart_of_accounts для РСБУ
    SELECT versionid INTO v_chart_id FROM ext.ext_chart_of_accounts WHERE calias = 'RAS';
    
    IF v_chart_id IS NULL THEN
        RAISE EXCEPTION 'План счетов РСБУ не найден';
    END IF;
    
    -- Получаем ID типа сущности CHART_ACCOUNT
    SELECT id INTO v_entity_account_id FROM meta.entitytypes WHERE calias = 'CHART_ACCOUNT';
    
    IF v_entity_account_id IS NULL THEN
        RAISE EXCEPTION 'Тип сущности CHART_ACCOUNT не найден';
    END IF;
    
    RAISE NOTICE 'Загружаем счета для плана с chart_id = %', v_chart_id;
    
    -- Открываем курсор и загружаем счета
    OPEN v_cursor;
    LOOP
        FETCH v_cursor INTO v_code, v_cname, v_type, v_parent_code, v_comment;
        EXIT WHEN NOT FOUND;
        
        -- Находим ID родительского счета в entity_instances
        v_parent_id := NULL;
        IF v_parent_code IS NOT NULL THEN
            SELECT ca.id INTO v_parent_id
            FROM ext.ext_chart_account ca
            WHERE ca.chart_id = v_chart_id AND ca.code = v_parent_code;
        END IF;
        
        -- Создаем экземпляр и версию счета
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) 
        VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) 
        VALUES (v_inst_id, v_code || ' — ' || v_cname, 'Active', now()) RETURNING id INTO v_ver_id;
        
        -- Вставляем в ext-таблицу
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active, mcomment)
        VALUES (v_ver_id, v_chart_id, v_code, v_cname, v_type, v_parent_id, true, v_comment);
        
    END LOOP;
    CLOSE v_cursor;
    
    RAISE NOTICE 'Счета РСБУ загружены. Загружено % счетов.', (SELECT COUNT(*) FROM ext.ext_chart_account WHERE chart_id = v_chart_id);
END;
$procedure$

```
---

#### Procedure `load_chart_ras_missing_accounts`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.load_chart_ras_missing_accounts()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_chart_id CONSTANT INTEGER := 14320;
    v_entity_account_id INTEGER;
    v_parent_id INTEGER;
    v_inst_id INTEGER;
    v_ver_id INTEGER;
BEGIN
    -- Получаем ID типа сущности CHART_ACCOUNT
    SELECT id INTO v_entity_account_id FROM meta.entitytypes WHERE calias = 'CHART_ACCOUNT';
    
    -- ================================================================
    -- 01.01 и 01.02
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '01';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '01.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01.01 — Основные средства в организации', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '01.01', 'Основные средства в организации', 'A', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '01.02') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '01.02 — Выбытие основных средств', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '01.02', 'Выбытие основных средств', 'A', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- 02.01
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '02';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '02.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '02.01 — Амортизация собственных ОС', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '02.01', 'Амортизация собственных ОС', 'P', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- 05 (нет в списке)
    -- ================================================================
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '05') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '05 — Амортизация НМА', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '05', 'Амортизация нематериальных активов', 'P', true);
    END IF;
    
    -- ================================================================
    -- 08.04
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '08';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '08.04') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '08.04 — Приобретение ОС', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '08.04', 'Приобретение ОС', 'A', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- 09 (нет в списке)
    -- ================================================================
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '09') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '09 — Отложенные налоговые активы', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '09', 'Отложенные налоговые активы', 'A', true);
    END IF;
    
    -- ================================================================
    -- Дочерние счета 10
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '10';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '10.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.01 — Сырьё и материалы', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '10.01', 'Сырьё и материалы', 'A', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '10.03') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.03 — Топливо', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '10.03', 'Топливо', 'A', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '10.05') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.05 — Запасные части', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '10.05', 'Запасные части', 'A', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '10.09') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '10.09 — Инвентарь и хоз.принадлежности', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '10.09', 'Инвентарь и хоз.принадлежности', 'A', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- Дочерние счета 60
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '60';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '60.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60.01 — Расчёты с поставщиками', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '60.01', 'Расчёты с поставщиками', 'P', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '60.02') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '60.02 — Авансы выданные', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '60.02', 'Авансы выданные', 'A', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- Дочерние счета 62
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '62';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '62.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62.01 — Расчёты с покупателями', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '62.01', 'Расчёты с покупателями', 'A', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '62.02') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '62.02 — Авансы полученные', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '62.02', 'Авансы полученные', 'P', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- 66, 67 (нет в списке)
    -- ================================================================
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '66') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '66 — Краткосрочные кредиты', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '66', 'Расчёты по краткосрочным кредитам', 'P', true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '67') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '67 — Долгосрочные кредиты', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '67', 'Расчёты по долгосрочным кредитам', 'P', true);
    END IF;
    
    -- ================================================================
    -- 68.01, 68.02
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '68';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '68.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68.01 — НДФЛ', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '68.01', 'НДФЛ', 'P', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '68.02') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '68.02 — НДС', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '68.02', 'НДС', 'AP', v_parent_id, true);
    END IF;
    
    -- ================================================================
    -- 71 (нет в списке)
    -- ================================================================
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '71') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '71 — Расчёты с подотчётными лицами', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '71', 'Расчёты с подотчётными лицами', 'AP', true);
    END IF;
    
    -- ================================================================
    -- 76 (нет в списке)
    -- ================================================================
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '76') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '76 — Расчёты с разными дебиторами', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, is_active) VALUES (v_ver_id, v_chart_id, '76', 'Расчёты с разными дебиторами и кредиторами', 'AP', true);
    END IF;
    
    -- ================================================================
    -- Дочерние счета 90
    -- ================================================================
    SELECT id INTO v_parent_id FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '90';
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '90.01') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90.01 — Выручка', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '90.01', 'Выручка', 'P', v_parent_id, true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ext.ext_chart_account WHERE chart_id = v_chart_id AND code = '90.02') THEN
        INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_account_id, now()) RETURNING id INTO v_inst_id;
        INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (v_inst_id, '90.02 — Себестоимость продаж', 'Active', now()) RETURNING id INTO v_ver_id;
        INSERT INTO ext.ext_chart_account (versionid, chart_id, code, cname, account_type, parent_id, is_active) VALUES (v_ver_id, v_chart_id, '90.02', 'Себестоимость продаж', 'A', v_parent_id, true);
    END IF;
    
    RAISE NOTICE 'Недостающие счета РСБУ добавлены. Всего счетов: %', (SELECT COUNT(*) FROM ext.ext_chart_account WHERE chart_id = v_chart_id);
END;
$procedure$

```
---

#### Procedure `p_create_test_structure`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.p_create_test_structure()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_class_dict_id INTEGER;
    v_class_org_id INTEGER;
    v_class_doc_id INTEGER;
    v_class_person_id INTEGER;
    v_class_staff_id INTEGER;
    v_entity_person_id INTEGER;
    v_entity_dept_id INTEGER;
    v_entity_employee_id INTEGER;
    v_entity_staff_id INTEGER;
    v_entity_document_id INTEGER;
    v_entity_route_id INTEGER;
    v_entity_step_id INTEGER;
    v_field_id INTEGER;
    v_user_id INTEGER;
    v_role_user_id INTEGER;
    v_bu_head_id INTEGER;
    v_bu_corp_id INTEGER;
    v_bu_giraffe_id INTEGER;
    v_route_instance_id INTEGER;
    v_step1_id INTEGER;
    v_step2_id INTEGER;
    v_doc_instance_id INTEGER;
    v_permission_action_create INTEGER;
    v_permission_action_read INTEGER;
    v_permission_action_update INTEGER;
    v_permission_value_allow INTEGER;
    v_person_instance_id INTEGER;
BEGIN
    -- =====================================================
    -- 1. Получение ID служебных классов
    -- =====================================================
    SELECT id INTO v_class_dict_id FROM meta.entity_classes WHERE calias = 'DICT';
    SELECT id INTO v_class_org_id FROM meta.entity_classes WHERE calias = 'ORG';
    SELECT id INTO v_class_doc_id FROM meta.entity_classes WHERE calias = 'DOC';
    SELECT id INTO v_class_person_id FROM meta.entity_classes WHERE calias = 'PERSON';
    
    SELECT id INTO v_class_staff_id FROM meta.entity_classes WHERE calias = 'STAFF_POSITION';
    IF v_class_staff_id IS NULL THEN
        INSERT INTO meta.entity_classes (calias, cname, mcomment) 
        VALUES ('STAFF_POSITION', '!tst! Штатная единица', 'Привязка должности к подразделению и человеку (тестовый)')
        RETURNING id INTO v_class_staff_id;
    END IF;

    -- =====================================================
    -- 2. Получение ID балансовых единиц
    -- =====================================================
    SELECT id INTO v_bu_head_id FROM auth.balanceunits WHERE calias = 'HEAD_ORG';
    SELECT id INTO v_bu_corp_id FROM auth.balanceunits WHERE calias = 'BE001';
    SELECT id INTO v_bu_giraffe_id FROM auth.balanceunits WHERE calias = 'BE002';

    -- =====================================================
    -- 3. Создание сущностей
    -- =====================================================
    
    -- 3.1. Персоны
    SELECT id INTO v_entity_person_id FROM meta.entitytypes WHERE calias = 'PERSON';
    IF v_entity_person_id IS NULL THEN
        INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
        VALUES ('person', 'PERSON', v_class_person_id, 'PERSON', false, false, true, 1, 1)
        RETURNING id INTO v_entity_person_id;
    ELSE
        UPDATE meta.entitytypes SET cname = 'person' WHERE id = v_entity_person_id;
    END IF;
    
    -- 3.2. Должности
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('employee', '!tst!EMPLOYEE', v_class_dict_id, 'DICT', false, false, true, 1, 1)
    RETURNING id INTO v_entity_employee_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_employee_id, 'cname', 'C', 'Наименование', 150, true, 1),
    (v_entity_employee_id, 'code', 'C', 'Код должности', 50, true, 1),
    (v_entity_employee_id, 'salary_rate', 'N', 'Тарифная ставка', 15, false, 1),
    (v_entity_employee_id, 'parentid', 'I', 'Родительская должность', 0, false, 1);
    
    -- 3.3. Подразделения
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('dept', '!tst!DEPT', v_class_org_id, 'ORG', false, true, true, 1, 1)
    RETURNING id INTO v_entity_dept_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_dept_id, 'cname', 'C', 'Наименование', 150, true, 1),
    (v_entity_dept_id, 'code', 'C', 'Код подразделения', 50, true, 1),
    (v_entity_dept_id, 'parentid', 'I', 'Родительское подразделение', 0, true, 1),
    (v_entity_dept_id, 'chief_staff_id', 'R', 'Руководитель (штатная единица)', 0, false, 1);
    
    -- 3.4. Штатная единица
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('staff_position', '!tst!STAFF_POSITION', v_class_staff_id, 'STAFF_POSITION', false, false, true, 1, 1)
    RETURNING id INTO v_entity_staff_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_staff_id, 'dept_id', 'R', 'Подразделение', 0, true, 1),
    (v_entity_staff_id, 'employee_id', 'R', 'Должность', 0, true, 1),
    (v_entity_staff_id, 'person_id', 'R', 'Сотрудник (персона)', 0, true, 1),
    (v_entity_staff_id, 'rate', 'N', 'Ставка', 15, false, 1),
    (v_entity_staff_id, 'is_chief', 'L', 'Руководитель подразделения', 0, true, 1),
    (v_entity_staff_id, 'date_from', 'D', 'Дата назначения', 0, true, 1),
    (v_entity_staff_id, 'date_to', 'D', 'Дата увольнения', 0, true, 1),
    (v_entity_staff_id, 'balanceunit_id', 'R', 'Балансовая единица', 0, true, 1);
    
    -- 3.5. Документ
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('memo', '!tst!MEMO', v_class_doc_id, 'DOC', false, false, true, 1, 1)
    RETURNING id INTO v_entity_document_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_document_id, 'doc_number', 'C', 'Номер документа', 50, true, 1),
    (v_entity_document_id, 'doc_date', 'D', 'Дата документа', 0, true, 1),
    (v_entity_document_id, 'subject', 'C', 'Тема', 255, true, 1),
    (v_entity_document_id, 'content', 'M', 'Содержание', 0, false, 1),
    (v_entity_document_id, 'author_staff_id', 'R', 'Автор (штатная единица)', 0, true, 1),
    (v_entity_document_id, 'status', 'C', 'Статус документа', 50, true, 1);
    
    -- 3.6. Маршрут
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('route', '!tst!ROUTE', v_class_dict_id, 'DICT', false, false, true, 1, 1)
    RETURNING id INTO v_entity_route_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_route_id, 'cname', 'C', 'Наименование', 150, true, 1),
    (v_entity_route_id, 'code', 'C', 'Код маршрута', 50, true, 1),
    (v_entity_route_id, 'doc_type_id', 'R', 'Тип документа', 0, true, 1),
    (v_entity_route_id, 'is_active', 'L', 'Активен', 0, true, 1);
    
    -- 3.7. Этап маршрута
    INSERT INTO meta.entitytypes (cname, calias, class_id, cbaseclass, lisdependent, lishierarchy, lisversioned, isecuritystrategy, status_id)
    VALUES ('route_step', '!tst!ROUTE_STEP', v_class_dict_id, 'DICT', false, false, true, 1, 1)
    RETURNING id INTO v_entity_step_id;
    
    INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, nlength, lisindexed, status_id) VALUES
    (v_entity_step_id, 'route_id', 'R', 'Маршрут', 0, true, 1),
    (v_entity_step_id, 'step_order', 'I', 'Порядок этапа', 0, true, 1),
    (v_entity_step_id, 'step_name', 'C', 'Название этапа', 100, true, 1),
    (v_entity_step_id, 'assign_type', 'C', 'Тип назначения', 50, true, 1),
    (v_entity_step_id, 'assign_target', 'C', 'Цель назначения', 255, true, 1),
    (v_entity_step_id, 'scope', 'C', 'Область поиска', 20, true, 1),
    (v_entity_step_id, 'scope_target', 'C', 'Целевая БЕ', 255, false, 1),
    (v_entity_step_id, 'time_limit_days', 'I', 'Лимит дней', 0, false, 1),
    (v_entity_step_id, 'next_step_on_reject', 'I', 'Следующий этап при отказе', 0, false, 1);
    
    -- =====================================================
    -- 4. Синхронизация структур (p_field_sync)
    -- =====================================================
    FOR v_field_id IN SELECT id FROM meta.fields WHERE entitytypeid IN (
        v_entity_employee_id, v_entity_dept_id, v_entity_staff_id, 
        v_entity_document_id, v_entity_route_id, v_entity_step_id
    ) LOOP
        CALL meta.p_field_sync(v_field_id);
    END LOOP;
    
    -- =====================================================
    -- 5. Создание справочных данных
    -- =====================================================
    
    -- Должности
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_employee_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Директор', 'Active', now());
    INSERT INTO ext.ext_employee (versionid, cname, code, salary_rate) VALUES (currval('data.entity_versions_id_seq'), '!tst! Директор', '!tst!DIR', 100000);
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_employee_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Бухгалтер', 'Active', now());
    INSERT INTO ext.ext_employee (versionid, cname, code, salary_rate) VALUES (currval('data.entity_versions_id_seq'), '!tst! Бухгалтер', '!tst!BUH', 70000);
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_employee_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Менеджер', 'Active', now());
    INSERT INTO ext.ext_employee (versionid, cname, code, salary_rate) VALUES (currval('data.entity_versions_id_seq'), '!tst! Менеджер', '!tst!MGR', 50000);
    
    -- Персоны
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_person_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Иванов Иван Иванович', 'Active', now());
    INSERT INTO ext.ext_person (versionid, clastname, cfirstname, csecondname, dbirthdate, cinn) 
    VALUES (currval('data.entity_versions_id_seq'), 'Иванов', 'Иван', 'Иванович', '1980-01-15', '1234567890');
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_person_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Петров Петр Петрович', 'Active', now());
    INSERT INTO ext.ext_person (versionid, clastname, cfirstname, csecondname, dbirthdate, cinn) 
    VALUES (currval('data.entity_versions_id_seq'), 'Петров', 'Петр', 'Петрович', '1985-05-20', '0987654321');
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_person_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Сидоров Сидор Сидорович', 'Active', now());
    INSERT INTO ext.ext_person (versionid, clastname, cfirstname, csecondname, dbirthdate, cinn) 
    VALUES (currval('data.entity_versions_id_seq'), 'Сидоров', 'Сидор', 'Сидорович', '1990-10-30', '5555555555');
    
    -- Подразделения
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_dept_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Администрация', 'Active', now());
    INSERT INTO ext.ext_dept (versionid, cname, code) VALUES (currval('data.entity_versions_id_seq'), '!tst! Администрация', '!tst!ADM');
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_dept_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Бухгалтерия', 'Active', now());
    INSERT INTO ext.ext_dept (versionid, cname, code) VALUES (currval('data.entity_versions_id_seq'), '!tst! Бухгалтерия', '!tst!BUA');
    
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_dept_id, now());
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) VALUES (currval('data.entity_instances_id_seq'), '!tst! Отдел продаж', 'Active', now());
    INSERT INTO ext.ext_dept (versionid, cname, code) VALUES (currval('data.entity_versions_id_seq'), '!tst! Отдел продаж', '!tst!SAL');
    
    -- =====================================================
    -- 6. Создание тестового пользователя и роли
    -- =====================================================
    
    -- Роль
    IF NOT EXISTS (SELECT 1 FROM auth.roles WHERE calias = '!tst!USER_ROLE') THEN
        INSERT INTO auth.roles (cname, calias, role_type_id) 
        SELECT '!tst! Пользователь системы', '!tst!USER_ROLE', id FROM auth.role_types WHERE calias = 'USER';
    END IF;
    SELECT id INTO v_role_user_id FROM auth.roles WHERE calias = '!tst!USER_ROLE';
    
    -- ID первой персоны для привязки пользователя
    SELECT i.id INTO v_person_instance_id 
    FROM data.entity_instances i 
    WHERE i.entitytypeid = v_entity_person_id 
    ORDER BY i.id 
    LIMIT 1;
    
    -- Пользователь
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE clogin = '!tst!mister_bin') THEN
        INSERT INTO auth.users (clogin, cpassword_hash, lactive, is_system, person_instanceid) 
        VALUES ('!tst!mister_bin', crypt('mister_bin', gen_salt('bf')), true, false, v_person_instance_id);
    END IF;
    SELECT id INTO v_user_id FROM auth.users WHERE clogin = '!tst!mister_bin';
    
    -- Контекст (пользователь-роль-БЕ)
    IF v_user_id IS NOT NULL AND v_role_user_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM auth.userrolecontext WHERE userid = v_user_id AND roleid = v_role_user_id AND balanceunitid = v_bu_corp_id) THEN
            INSERT INTO auth.userrolecontext (userid, roleid, balanceunitid) 
            VALUES (v_user_id, v_role_user_id, v_bu_corp_id);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM auth.userrolecontext WHERE userid = v_user_id AND roleid = v_role_user_id AND balanceunitid = v_bu_giraffe_id) THEN
            INSERT INTO auth.userrolecontext (userid, roleid, balanceunitid) 
            VALUES (v_user_id, v_role_user_id, v_bu_giraffe_id);
        END IF;
    END IF;
    
    -- =====================================================
    -- 7. Настройка разрешений
    -- =====================================================
    SELECT id INTO v_permission_action_create FROM auth.permission_actions WHERE calias = 'CREATE';
    SELECT id INTO v_permission_action_read FROM auth.permission_actions WHERE calias = 'READ';
    SELECT id INTO v_permission_action_update FROM auth.permission_actions WHERE calias = 'UPDATE';
    SELECT id INTO v_permission_value_allow FROM auth.permission_values WHERE calias = 'ALLOW';
    
    IF v_role_user_id IS NOT NULL THEN
        INSERT INTO auth.permissions (role_id, entity_type_id, action_id, value_id, grantor_id)
        VALUES 
        (v_role_user_id, v_entity_document_id, v_permission_action_create, v_permission_value_allow, v_user_id),
        (v_role_user_id, v_entity_document_id, v_permission_action_read, v_permission_value_allow, v_user_id),
        (v_role_user_id, v_entity_document_id, v_permission_action_update, v_permission_value_allow, v_user_id)
        ON CONFLICT (role_id, entity_type_id, instance_id, action_id) DO NOTHING;
        
        INSERT INTO auth.permissions (role_id, entity_type_id, action_id, value_id, grantor_id)
        VALUES 
        (v_role_user_id, v_entity_person_id, v_permission_action_read, v_permission_value_allow, v_user_id),
        (v_role_user_id, v_entity_employee_id, v_permission_action_read, v_permission_value_allow, v_user_id),
        (v_role_user_id, v_entity_dept_id, v_permission_action_read, v_permission_value_allow, v_user_id),
        (v_role_user_id, v_entity_staff_id, v_permission_action_read, v_permission_value_allow, v_user_id)
        ON CONFLICT (role_id, entity_type_id, instance_id, action_id) DO NOTHING;
    END IF;
    
    -- =====================================================
    -- 8. Создание примера маршрута
    -- =====================================================
    
    -- Инстанс документа для ссылки doc_type_id
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) 
    VALUES (v_entity_document_id, now())
    RETURNING id INTO v_doc_instance_id;
    
    -- Маршрут
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_route_id, now()) RETURNING id INTO v_route_instance_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) 
    VALUES (v_route_instance_id, '!tst! Согласование служебной записки', 'Active', now());
    INSERT INTO ext.ext_route (versionid, cname, code, doc_type_id, is_active)
    VALUES (currval('data.entity_versions_id_seq'), '!tst! Согласование служебной записки', '!tst!MEMO_APPROVE', v_doc_instance_id, true);
    
    -- Этап 1
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_step_id, now()) RETURNING id INTO v_step1_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) 
    VALUES (v_step1_id, '!tst! Согласование', 'Active', now());
    INSERT INTO ext.ext_route_step (versionid, route_id, step_order, step_name, assign_type, assign_target, scope)
    VALUES (currval('data.entity_versions_id_seq'), v_route_instance_id, 10, '!tst! Согласование', 'RULE', 'HEAD', 'BU');
    
    -- Этап 2
    INSERT INTO data.entity_instances (entitytypeid, tdt_birth) VALUES (v_entity_step_id, now()) RETURNING id INTO v_step2_id;
    INSERT INTO data.entity_versions (instanceid, cname, cversionstatus, tdt_start) 
    VALUES (v_step2_id, '!tst! Утверждение', 'Active', now());
    INSERT INTO ext.ext_route_step (versionid, route_id, step_order, step_name, assign_type, assign_target, scope)
    VALUES (currval('data.entity_versions_id_seq'), v_route_instance_id, 20, '!tst! Утверждение', 'ROLE', 'CFO', 'ALL');
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Тестовая структура создана!';
    RAISE NOTICE 'Пользователь: !tst!mister_bin / mister_bin';
    RAISE NOTICE 'Для удаления: CALL meta.p_drop_test_structure();';
    RAISE NOTICE '========================================';
END;
$procedure$

```
---

#### Procedure `p_drop_test_structure`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.p_drop_test_structure()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_entity_employee_id INTEGER;
    v_entity_dept_id INTEGER;
    v_entity_person_id INTEGER;
    v_entity_staff_id INTEGER;
    v_entity_document_id INTEGER;
    v_entity_route_id INTEGER;
    v_entity_step_id INTEGER;
    v_test_role_user_id INTEGER;
    v_test_user_id INTEGER;
    v_class_staff_id INTEGER;
BEGIN
    -- =====================================================
    -- 1. Получение ID тестовых сущностей по calias
    -- =====================================================
    SELECT id INTO v_entity_person_id FROM meta.entitytypes WHERE calias = 'PERSON';
    SELECT id INTO v_entity_employee_id FROM meta.entitytypes WHERE calias = '!tst!EMPLOYEE';
    SELECT id INTO v_entity_dept_id FROM meta.entitytypes WHERE calias = '!tst!DEPT';
    SELECT id INTO v_entity_staff_id FROM meta.entitytypes WHERE calias = '!tst!STAFF_POSITION';
    SELECT id INTO v_entity_document_id FROM meta.entitytypes WHERE calias = '!tst!MEMO';
    SELECT id INTO v_entity_route_id FROM meta.entitytypes WHERE calias = '!tst!ROUTE';
    SELECT id INTO v_entity_step_id FROM meta.entitytypes WHERE calias = '!tst!ROUTE_STEP';
    
    SELECT id INTO v_class_staff_id FROM meta.entity_classes WHERE calias = 'STAFF_POSITION';
    
    -- =====================================================
    -- 2. Удаление данных из ext-таблиц
    -- =====================================================
    IF v_entity_employee_id IS NOT NULL THEN
        DELETE FROM ext.ext_employee WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_employee_id));
    END IF;
    
    IF v_entity_dept_id IS NOT NULL THEN
        DELETE FROM ext.ext_dept WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_dept_id));
    END IF;
    
    IF v_entity_staff_id IS NOT NULL THEN
        DELETE FROM ext.ext_staff_position WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_staff_id));
    END IF;
    
    IF v_entity_document_id IS NOT NULL THEN
        DELETE FROM ext.ext_memo WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_document_id));
    END IF;
    
    IF v_entity_route_id IS NOT NULL THEN
        DELETE FROM ext.ext_route WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_route_id));
    END IF;
    
    IF v_entity_step_id IS NOT NULL THEN
        DELETE FROM ext.ext_route_step WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_step_id));
    END IF;
    
    IF v_entity_person_id IS NOT NULL THEN
        DELETE FROM ext.ext_person WHERE versionid IN (SELECT id FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_person_id));
    END IF;
    
    -- =====================================================
    -- 3. Удаление данных из data.entity_versions и data.entity_instances
    -- =====================================================
    IF v_entity_route_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_route_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_route_id;
    END IF;
    
    IF v_entity_step_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_step_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_step_id;
    END IF;
    
    IF v_entity_document_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_document_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_document_id;
    END IF;
    
    IF v_entity_employee_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_employee_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_employee_id;
    END IF;
    
    IF v_entity_dept_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_dept_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_dept_id;
    END IF;
    
    IF v_entity_staff_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_staff_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_staff_id;
    END IF;
    
    IF v_entity_person_id IS NOT NULL THEN
        DELETE FROM data.entity_versions WHERE instanceid IN (SELECT id FROM data.entity_instances WHERE entitytypeid = v_entity_person_id);
        DELETE FROM data.entity_instances WHERE entitytypeid = v_entity_person_id;
    END IF;
    
    -- =====================================================
    -- 4. Удаление полей из meta.fields
    -- =====================================================
    DELETE FROM meta.fields WHERE entitytypeid IN (
        v_entity_employee_id, v_entity_dept_id, v_entity_staff_id,
        v_entity_document_id, v_entity_route_id, v_entity_step_id
    );
    
    -- =====================================================
    -- 5. Удаление ext-таблиц
    -- =====================================================
    IF v_entity_employee_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_employee CASCADE';
    END IF;
    
    IF v_entity_dept_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_dept CASCADE';
    END IF;
    
    IF v_entity_staff_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_staff_position CASCADE';
    END IF;
    
    IF v_entity_document_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_memo CASCADE';
    END IF;
    
    IF v_entity_route_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_route CASCADE';
    END IF;
    
    IF v_entity_step_id IS NOT NULL THEN
        EXECUTE 'DROP TABLE IF EXISTS ext.ext_route_step CASCADE';
    END IF;
    
    -- =====================================================
    -- 6. Удаление типов сущностей
    -- =====================================================
    DELETE FROM meta.entitytypes WHERE id IN (
        v_entity_employee_id, v_entity_dept_id, v_entity_staff_id,
        v_entity_document_id, v_entity_route_id, v_entity_step_id
    );
    
    -- =====================================================
    -- 7. Очистка разрешений
    -- =====================================================
    DELETE FROM auth.permissions WHERE entity_type_id IN (
        v_entity_employee_id, v_entity_dept_id, v_entity_staff_id,
        v_entity_document_id, v_entity_route_id, v_entity_step_id
    );
    
    -- =====================================================
    -- 8. Удаление тестовых пользователей и ролей
    -- =====================================================
    SELECT id INTO v_test_role_user_id FROM auth.roles WHERE calias = '!tst!USER_ROLE';
    IF v_test_role_user_id IS NOT NULL THEN
        DELETE FROM auth.userrolecontext WHERE roleid = v_test_role_user_id;
        DELETE FROM auth.permissions WHERE role_id = v_test_role_user_id;
        DELETE FROM auth.roles WHERE id = v_test_role_user_id;
    END IF;
    
    SELECT id INTO v_test_user_id FROM auth.users WHERE clogin = '!tst!mister_bin';
    IF v_test_user_id IS NOT NULL THEN
        DELETE FROM auth.userrolecontext WHERE userid = v_test_user_id;
        DELETE FROM auth.permissions WHERE grantor_id = v_test_user_id;
        DELETE FROM auth.users WHERE id = v_test_user_id;
    END IF;
    
    -- =====================================================
    -- 9. Удаление тестового класса STAFF_POSITION
    -- =====================================================
    IF v_class_staff_id IS NOT NULL THEN
        DELETE FROM meta.entity_classes WHERE id = v_class_staff_id;
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Тестовая структура удалена!';
    RAISE NOTICE 'Системные объекты не затронуты.';
    RAISE NOTICE '========================================';
END;
$procedure$

```
---

#### Procedure `p_field_sync`
- **Параметры:** `IN p_field_id integer`

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE meta.p_field_sync(IN p_field_id integer)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_entity_id     integer;
    v_entity_cname  varchar;  -- системное имя сущности (cname)
    v_field_name    varchar;
    v_field_type    char(1);
    v_ref_ent_id    integer;
    v_length        integer;
    v_decimals      integer;
    v_is_indexed    boolean;
    v_sql           text;
    v_table_name    text;
    v_comp          RECORD; 
    v_table_exists  boolean;
BEGIN
    -- 1. СБОР ПОЛНЫХ МЕТАДАННЫХ (с учетом реляционной связи ref_entitytypeid)
    SELECT 
        f.entitytypeid, 
        lower(t.cname),    -- используем cname, не calias
        lower(f.cfieldname), 
        upper(f.cfieldtype), 
        f.ref_entitytypeid,
        coalesce(f.nlength, 255), 
        coalesce(f.ndecimals, 0),
        f.lisindexed
    INTO 
        v_entity_id, v_entity_cname, v_field_name, 
        v_field_type, v_ref_ent_id, v_length, v_decimals, v_is_indexed
    FROM meta.fields f
    JOIN meta.entitytypes t ON f.entitytypeid = t.id
    WHERE f.id = p_field_id;

    v_table_name := 'ext.ext_' || v_entity_cname;

    -- Проверка существования таблицы
    SELECT count(*) > 0 INTO v_table_exists
    FROM information_schema.tables
    WHERE table_schema = 'ext' AND table_name = 'ext_' || v_entity_cname;

    -- Если таблицы нет, создаём её с минимальной структурой
    IF NOT v_table_exists THEN
        EXECUTE format('
            CREATE TABLE %I.%I (
                id SERIAL PRIMARY KEY,
                versionid INTEGER NOT NULL REFERENCES data.entity_versions(id) ON DELETE CASCADE
            )', 'ext', 'ext_' || v_entity_cname);
    END IF;

    -- 2. СИНХРОНИЗАЦИЯ ПУПОВИН (Композиция / Вложения)
    -- Если сущность - "ребенок", проверяем наличие полей-указателей на "родителей"
    FOR v_comp in 
        SELECT parent_entityid, lower(c_link_fieldname) as link_field
        FROM meta.entity_composition 
        WHERE child_entityid = v_entity_id
    LOOP
        -- Авто-регистрация в метаданных (если Демиург еще не создал поле в grid)
        IF NOT EXISTS (SELECT 1 FROM meta.fields WHERE entitytypeid = v_entity_id AND lower(cfieldname) = v_comp.link_field) THEN
            INSERT INTO meta.fields (entitytypeid, cfieldname, cfieldtype, calias, lisindexed, isortorder)
            VALUES (v_entity_id, v_comp.link_field, 'I', 'FK: ' || (SELECT calias FROM meta.entitytypes WHERE id = v_comp.parent_entityid), true, 0);
        END IF;

        -- Физика: Создаем поле-указатель и индекс
        EXECUTE 'ALTER TABLE ' || v_table_name || ' ADD COLUMN IF NOT EXISTS ' || v_comp.link_field || ' integer';
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_' || v_entity_cname || '_' || v_comp.link_field || ' ON ' || v_table_name || ' (' || v_comp.link_field || ')';
    END LOOP;

    -- 3. ГЕНЕРАЦИЯ ОСНОВНОГО ПОЛЯ (DDL)
    v_sql := 'ALTER TABLE ' || v_table_name;

    CASE v_field_type
        WHEN 'C' THEN -- Строка
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' varchar(' || v_length || ')';
        
        WHEN 'N' THEN -- Число
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' numeric(' || v_length || ',' || v_decimals || ')';
        
        WHEN 'I' THEN -- Целое
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' integer';
            
        WHEN 'R' THEN -- ССЫЛКА
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' integer';
            v_sql := v_sql || '; ALTER TABLE ' || v_table_name || 
                     ' ADD CONSTRAINT fk_' || v_entity_cname || '_' || v_field_name || 
                     ' FOREIGN KEY (' || v_field_name || ') REFERENCES data.entity_instances(id) ON DELETE RESTRICT';

        WHEN 'D' THEN -- Дата
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' date';
        
        WHEN 'T' THEN -- Дата/Время
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' timestamp without time zone';
        
        WHEN 'L' THEN -- Логика
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' boolean DEFAULT false';
        
        WHEN 'M' THEN -- Мемо
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' text';

        WHEN 'G', 'V', 'F' THEN -- Блобы
            v_sql := v_sql || ' ADD COLUMN IF NOT EXISTS ' || v_field_name || ' bytea, ' ||
                              ' ADD COLUMN IF NOT EXISTS ' || v_field_name || '_name varchar(255)';
        ELSE
            RAISE EXCEPTION 'Неизвестный тип Mozart: %', v_field_type;
    END CASE;

    EXECUTE v_sql;

    -- 4. ИНДЕКСАЦИЯ
    IF v_is_indexed AND v_field_type NOT IN ('G', 'V', 'F', 'M') THEN
        v_sql := 'CREATE INDEX IF NOT EXISTS ix_' || v_entity_cname || '_' || v_field_name || 
                 ' ON ' || v_table_name || ' (' || v_field_name || ')';
        EXECUTE v_sql;
        
        IF v_field_type IN ('G', 'V', 'F') THEN
             EXECUTE 'CREATE INDEX IF NOT EXISTS ix_' || v_entity_cname || '_' || v_field_name || '_name' ||
                     ' ON ' || v_table_name || ' (' || v_field_name || '_name)';
        END IF;
    END IF;

END;
$procedure$

```
---

#### Function `trg_rename_ext_table`
- **Сигнатура:** `trg_rename_ext_table()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION meta.trg_rename_ext_table()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    old_table_name TEXT;
    new_table_name TEXT;
BEGIN
    IF OLD.cname <> NEW.cname THEN
        old_table_name := 'ext.ext_' || OLD.cname;
        new_table_name := 'ext.ext_' || NEW.cname;
        
        -- Проверяем, существует ли старая таблица
        IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'ext' AND tablename = 'ext_' || OLD.cname) THEN
            EXECUTE format('ALTER TABLE %I.%I RENAME TO %I', 'ext', 'ext_' || OLD.cname, 'ext_' || NEW.cname);
        END IF;
    END IF;
    RETURN NEW;
END;
$function$

```
---

#### Триггер `trg_entitytypes_rename`
- **Таблица:** `meta.entitytypes`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_entitytypes_rename BEFORE UPDATE ON meta.entitytypes FOR EACH ROW EXECUTE FUNCTION meta.trg_rename_ext_table()
```
---
## Схема `data`

### Таблицы

#### `assignment_signatures`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.assignment_signatures_id_seq'::regclass) | ✅ |  |
| assignment_id | integer | ✅ |  |  |  |
| report_id | integer | ✅ |  |  |  |
| signer_user_id | integer | ❌ |  |  |  |
| certificate_id | integer | ❌ |  |  |  |
| signature_data | text | ❌ |  |  |  |
| signed_hash | character varying(64) | ❌ |  |  |  |
| signed_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

**Check-ограничения:**
- `assignment_signatures_check`: CHECK ((((assignment_id IS NOT NULL) AND (report_id IS NULL)) OR ((assignment_id IS NULL) AND (report_id IS NOT NULL))))

---

#### `doc_actions`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.doc_actions_id_seq'::regclass) | ✅ |  |
| doc_instance_id | integer | ❌ |  |  |  |
| step_instance_id | integer | ✅ |  |  |  |
| actor_user_id | integer | ❌ |  |  |  |
| on_behalf_user_id | integer | ✅ |  |  |  |
| action_type | character varying(30) | ❌ |  |  |  |
| comment | text | ✅ |  |  |  |
| created_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

**Check-ограничения:**
- `doc_actions_action_type_check`: CHECK (((action_type)::text = ANY ((ARRAY['CREATE'::character varying, 'SUBMIT'::character varying, 'APPROVE'::character varying, 'REJECT'::character varying, 'SIGN'::character varying, 'DELEGATE'::character varying, 'ADD_READER'::character varying, 'ADD_RESOLUTION'::character varying, 'ADD_ASSIGNMENT'::character varying, 'REPORT'::character varying, 'COMMENT'::character varying, 'EDIT'::character varying, 'ARCHIVE'::character varying])::text[])))

---

#### `doc_signatures`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.doc_signatures_id_seq'::regclass) | ✅ |  |
| doc_instance_id | integer | ❌ |  |  |  |
| signer_user_id | integer | ❌ |  |  |  |
| on_behalf_user_id | integer | ✅ |  |  |  |
| certificate_id | integer | ❌ |  |  |  |
| signature_data | text | ❌ |  |  |  |
| signed_hash | character varying(64) | ❌ |  |  |  |
| signed_at | timestamp with time zone | ❌ | now() |  |  |
| signature_type | character varying(20) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Check-ограничения:**
- `doc_signatures_signature_type_check`: CHECK (((signature_type)::text = ANY ((ARRAY['SIGN'::character varying, 'APPROVE'::character varying, 'REVIEW'::character varying])::text[])))

---

#### `entity_instances`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.entity_instances_id_seq'::regclass) | ✅ |  |
| entitytypeid | integer | ✅ |  |  |  |
| ownerbu_id | integer | ✅ |  |  |  |
| tdt_birth | timestamp without time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

---

#### `entity_linkage_items`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.entity_linkage_items_id_seq'::regclass) | ✅ |  |
| linkageid | integer | ❌ |  |  |  |
| instanceid | integer | ❌ |  |  |  |
| roleinstanceid | integer | ❌ |  |  |  |
| tdt_start | timestamp without time zone | ✅ | now() |  |  |
| tdt_end | timestamp without time zone | ✅ | '9999-12-31 23:59:59'::timestamp without time zone |  |  |
| user_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

---

#### `entity_linkages`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.entity_linkages_id_seq'::regclass) | ✅ |  |
| reftypeid | integer | ❌ |  |  |  |
| cname | character varying(500) | ✅ |  |  |  |
| ownerbu_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

---

#### `entity_versions`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.entity_versions_id_seq'::regclass) | ✅ |  |
| instanceid | integer | ✅ |  |  |  |
| parentinstanceid | integer | ✅ |  |  |  |
| tdt_start | timestamp without time zone | ✅ | now() |  |  |
| tdt_end | timestamp without time zone | ✅ | '9999-12-31 23:59:59'::timestamp without time zone |  |  |
| cversionstatus | character varying(20) | ✅ | 'Active'::character varying |  |  |
| cname | character varying(500) | ✅ |  |  |  |
| created_by_userid | integer | ✅ |  |  |  |
| modified_by_userid | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

---

#### `entity_visibility`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.entity_visibility_id_seq'::regclass) | ✅ |  |
| instanceid | integer | ❌ |  |  |  |
| balanceunitid | integer | ❌ |  |  |  |
| tdt_granted | timestamp without time zone | ✅ | now() |  |  |
| i_access_level | integer | ✅ | 1 |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `uk_entity_visibility`: (`instanceid, balanceunitid`)

---

#### `notifications`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('data.notifications_id_seq'::regclass) | ✅ |  |
| user_id | integer | ❌ |  |  |  |
| doc_instance_id | integer | ✅ |  |  |  |
| step_instance_id | integer | ✅ |  |  |  |
| assignment_id | integer | ✅ |  |  |  |
| notification_type | character varying(30) | ❌ |  |  |  |
| message | text | ✅ |  |  |  |
| is_read | boolean | ❌ | false |  |  |
| created_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

**Check-ограничения:**
- `notifications_notification_type_check`: CHECK (((notification_type)::text = ANY ((ARRAY['NEW_STEP'::character varying, 'STEP_OVERDUE'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'DELEGATED'::character varying, 'NEW_ASSIGNMENT'::character varying, 'ASSIGNMENT_DONE'::character varying, 'REPORT_REJECTED'::character varying, 'DOC_SIGNED'::character varying, 'READER_ADDED'::character varying, 'DOC_REJECTED'::character varying])::text[])))

---

### Хранимые процедуры, функции и триггеры

#### Function `f_getversionid`
- **Сигнатура:** `f_getversionid(p_iinstanceid integer, p_gdsystemdate timestamp without time zone DEFAULT NULL::timestamp without time zone)`
- **Возвращает:** integer

**Определение:**
```sql
CREATE OR REPLACE FUNCTION data.f_getversionid(p_iinstanceid integer, p_gdsystemdate timestamp without time zone DEFAULT NULL::timestamp without time zone)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_iVersionID integer;
BEGIN
    -- Если дата не указана (или это сегодня), ищем по метке 'Active' (Раздел 11.2 - Speed)
    IF p_gdSystemDate IS NULL OR p_gdSystemDate >= now() THEN
        SELECT ID INTO v_iVersionID
        FROM data.Entity_Versions
        WHERE InstanceID = p_iInstanceID 
          AND cVersionStatus = 'Active'
        LIMIT 1;
    
    -- Если указана дата в прошлом, включаем "Машину времени" (Раздел 11.2 - History)
    ELSE
        SELECT ID INTO v_iVersionID
        FROM data.Entity_Versions
        WHERE InstanceID = p_iInstanceID 
          AND p_gdSystemDate BETWEEN tDT_Start AND tDT_End
        ORDER BY tDT_Start DESC -- На случай наложений берем самую свежую
        LIMIT 1;
    END IF;

    RETURN v_iVersionID;
END;
$function$

```
---

#### Function `refresh_current_versions`
- **Сигнатура:** `refresh_current_versions()`
- **Возвращает:** void

**Определение:**
```sql
CREATE OR REPLACE FUNCTION data.refresh_current_versions()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY data.mv_current_versions;
END;
$function$

```
---

#### Function `trg_entity_versions_audit`
- **Сигнатура:** `trg_entity_versions_audit()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION data.trg_entity_versions_audit()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_userid INTEGER;
BEGIN
    -- Получаем ID текущего пользователя из настройки сессии
    BEGIN
        v_userid := current_setting('my.current_userid')::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        v_userid := NULL; -- если не установлено
    END;

    IF TG_OP = 'INSERT' THEN
        NEW.created_by_userid := v_userid;
        NEW.modified_by_userid := v_userid;
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.modified_by_userid := v_userid;
    END IF;
    RETURN NEW;
END;
$function$

```
---

#### Триггер `trg_entity_versions_audit`
- **Таблица:** `data.entity_versions`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** INSERT, UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_entity_versions_audit BEFORE INSERT OR UPDATE ON data.entity_versions FOR EACH ROW EXECUTE FUNCTION data.trg_entity_versions_audit()
```
---
## Схема `auth`

### Таблицы

#### `balanceunits`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.balanceunits_id_seq'::regclass) | ✅ |  |
| parentid | integer | ✅ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| calias | character varying(50) | ✅ |  |  |  |
| lisbalanceunit | boolean | ✅ | true |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `balanceunits_calias_key`: (`calias`)

---

#### `permission_actions`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.permission_actions_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `permission_actions_calias_key`: (`calias`)

---

#### `permission_values`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.permission_values_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `permission_values_calias_key`: (`calias`)

---

#### `permissions`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | bigint | ❌ | nextval('auth.permissions_id_seq'::regclass) | ✅ |  |
| role_id | integer | ❌ |  |  |  |
| entity_type_id | integer | ✅ |  |  |  |
| instance_id | integer | ✅ |  |  |  |
| action_id | integer | ❌ |  |  |  |
| value_id | integer | ❌ |  |  |  |
| grantor_id | integer | ✅ |  |  |  |
| tdt_granted | timestamp without time zone | ✅ | now() |  |  |
| tdt_expires | timestamp without time zone | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `permissions_role_id_entity_type_id_instance_id_action_id_key`: (`role_id, entity_type_id, instance_id, action_id`)

**Check-ограничения:**
- `permissions_check`: CHECK ((((entity_type_id IS NOT NULL) AND (instance_id IS NULL)) OR ((entity_type_id IS NULL) AND (instance_id IS NOT NULL)) OR ((entity_type_id IS NULL) AND (instance_id IS NULL))))

---

#### `role_types`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.role_types_id_seq'::regclass) | ✅ |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| mcomment | text | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `role_types_calias_key`: (`calias`)

---

#### `roles`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.roles_id_seq'::regclass) | ✅ |  |
| parentid | integer | ✅ |  |  |  |
| calias | character varying(50) | ❌ |  |  |  |
| cname | character varying(255) | ❌ |  |  |  |
| lisinterface | boolean | ✅ | false |  |  |
| cinterface_path | text | ✅ |  |  |  |
| mcomment | text | ✅ |  |  |  |
| role_type_id | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `roles_calias_key`: (`calias`)

---

#### `trustees`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.trustees_id_seq'::regclass) | ✅ |  |
| principal_user_id | integer | ❌ |  |  |  |
| trustee_user_id | integer | ❌ |  |  |  |
| scope | character varying(20) | ❌ | 'ALL'::character varying |  |  |
| scope_entitytype_id | integer | ✅ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| started_at | timestamp with time zone | ❌ | now() |  |  |
| expired_at | timestamp with time zone | ✅ |  |  |  |
| mcomment | text | ✅ |  |  |  |
| created_by_user_id | integer | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `trustees_principal_user_id_trustee_user_id_scope_scope_enti_key`: (`principal_user_id, trustee_user_id, scope, scope_entitytype_id`)

**Check-ограничения:**
- `trustees_scope_check`: CHECK (((scope)::text = ANY ((ARRAY['ALL'::character varying, 'DOC_CLASS'::character varying, 'ENTITY_TYPE'::character varying])::text[])))

---

#### `user_certificates`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.user_certificates_id_seq'::regclass) | ✅ |  |
| user_id | integer | ❌ |  |  |  |
| certificate_data | text | ❌ |  |  |  |
| serial_number | character varying(100) | ✅ |  |  |  |
| issuer | character varying(500) | ✅ |  |  |  |
| issued_at | date | ✅ |  |  |  |
| expires_at | date | ✅ |  |  |  |
| is_active | boolean | ❌ | true |  |  |
| public_key_fingerprint | character varying(64) | ✅ |  |  |  |
| created_at | timestamp with time zone | ❌ | now() |  |  |

**Первичный ключ:** `id`

---

#### `userrolecontext`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.userrolecontext_id_seq'::regclass) | ✅ |  |
| userid | integer | ❌ |  |  |  |
| roleid | integer | ❌ |  |  |  |
| balanceunitid | integer | ❌ |  |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `uk_user_role_bu`: (`userid, roleid, balanceunitid`)

---

#### `users`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('auth.users_id_seq'::regclass) | ✅ |  |
| person_instanceid | integer | ✅ |  |  |  |
| clogin | character varying(50) | ❌ |  |  |  |
| cpassword_hash | character varying(255) | ❌ |  |  |  |
| lactive | boolean | ✅ | true |  |  |
| tdt_last_login | timestamp without time zone | ✅ |  |  |  |
| is_system | boolean | ✅ | false |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `users_clogin_key`: (`clogin`)
- `users_person_instanceid_key`: (`person_instanceid`)

---

### Хранимые процедуры, функции и триггеры

#### Function `get_role_type`
- **Сигнатура:** `get_role_type(p_role_id integer)`
- **Возвращает:** character varying

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.get_role_type(p_role_id integer)
 RETURNS character varying
 LANGUAGE plpgsql
 STABLE
AS $function$
DECLARE
    v_type_alias VARCHAR(50);
BEGIN
    SELECT rt.calias INTO v_type_alias
    FROM auth.roles r
    JOIN auth.role_types rt ON r.role_type_id = rt.id
    WHERE r.id = p_role_id;
    
    RETURN v_type_alias;
END;
$function$

```
---

#### Function `get_role_type_id`
- **Сигнатура:** `get_role_type_id(p_role_id integer)`
- **Возвращает:** integer

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.get_role_type_id(p_role_id integer)
 RETURNS integer
 LANGUAGE plpgsql
 STABLE
AS $function$
DECLARE
    v_type_id INTEGER;
BEGIN
    IF p_role_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    SELECT role_type_id INTO v_type_id
    FROM auth.roles
    WHERE id = p_role_id;
    
    RETURN v_type_id;
END;
$function$

```
---

#### Function `trg_check_role_type_compatibility`
- **Сигнатура:** `trg_check_role_type_compatibility()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.trg_check_role_type_compatibility()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_parent_type INTEGER;
BEGIN
    -- Если есть родитель и пользователь явно указал тип
    IF NEW.parentid IS NOT NULL AND NEW.role_type_id IS NOT NULL THEN
        -- Получаем тип родителя
        SELECT role_type_id INTO v_parent_type
        FROM auth.roles
        WHERE id = NEW.parentid;
        
        -- Проверяем совпадение
        IF NEW.role_type_id != v_parent_type THEN
            RAISE EXCEPTION 'Child role type (%) must match parent role type (%)', 
                NEW.role_type_id, v_parent_type
            USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$function$

```
---

#### Function `trg_check_single_interface_role`
- **Сигнатура:** `trg_check_single_interface_role()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.trg_check_single_interface_role()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_role_type_alias VARCHAR(50);
    v_conflict_id INTEGER;
BEGIN
    -- Получаем алиас типа роли через существующую функцию
    v_role_type_alias := auth.get_role_type(NEW.roleid);
    
    -- Проверяем только для интерфейсных ролей (алиас = 'INTERFACE')
    IF v_role_type_alias = 'INTERFACE' THEN
        SELECT urc.id INTO v_conflict_id
        FROM auth.userrolecontext urc
        WHERE urc.userid = NEW.userid
          AND urc.balanceunitid = NEW.balanceunitid
          AND urc.id IS DISTINCT FROM NEW.id
          AND auth.get_role_type(urc.roleid) = 'INTERFACE'
        LIMIT 1;
        
        IF v_conflict_id IS NOT NULL THEN
            RAISE EXCEPTION 'User already has an interface role in this balance unit'
            USING ERRCODE = 'unique_violation';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$function$

```
---

#### Function `trg_inherit_role_type_from_parent`
- **Сигнатура:** `trg_inherit_role_type_from_parent()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.trg_inherit_role_type_from_parent()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Если указан родитель
    IF NEW.parentid IS NOT NULL THEN
        -- Берём тип от родителя
        SELECT role_type_id INTO NEW.role_type_id
        FROM auth.roles
        WHERE id = NEW.parentid;
        
        -- Если у родителя нет типа — ошибка
        IF NEW.role_type_id IS NULL THEN
            RAISE EXCEPTION 'Parent role % has no role_type_id', NEW.parentid
            USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$function$

```
---

#### Function `trg_prevent_type_change_if_has_children`
- **Сигнатура:** `trg_prevent_type_change_if_has_children()`
- **Возвращает:** trigger

**Определение:**
```sql
CREATE OR REPLACE FUNCTION auth.trg_prevent_type_change_if_has_children()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_child_count INTEGER;
BEGIN
    -- Если тип меняется
    IF OLD.role_type_id IS DISTINCT FROM NEW.role_type_id THEN
        -- Проверяем наличие прямых потомков
        SELECT COUNT(*) INTO v_child_count
        FROM auth.roles
        WHERE parentid = NEW.id;
        
        IF v_child_count > 0 THEN
            RAISE EXCEPTION 'Cannot change role type: role % (%) has % child(ren)', 
                NEW.id, NEW.cname, v_child_count
            USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$function$

```
---

#### Триггер `trg_check_role_type_compatibility`
- **Таблица:** `auth.roles`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** INSERT, UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_check_role_type_compatibility BEFORE INSERT OR UPDATE ON auth.roles FOR EACH ROW EXECUTE FUNCTION auth.trg_check_role_type_compatibility()
```
---

#### Триггер `trg_inherit_role_type_from_parent`
- **Таблица:** `auth.roles`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** INSERT, UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_inherit_role_type_from_parent BEFORE INSERT OR UPDATE ON auth.roles FOR EACH ROW EXECUTE FUNCTION auth.trg_inherit_role_type_from_parent()
```
---

#### Триггер `trg_prevent_type_change_if_has_children`
- **Таблица:** `auth.roles`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_prevent_type_change_if_has_children BEFORE UPDATE OF role_type_id ON auth.roles FOR EACH ROW EXECUTE FUNCTION auth.trg_prevent_type_change_if_has_children()
```
---

#### Триггер `trg_userrolecontext_check_interface`
- **Таблица:** `auth.userrolecontext`
- **Уровень:** ROW
- **Время:** BEFORE
- **События:** INSERT, UPDATE

**Определение:**
```sql
CREATE TRIGGER trg_userrolecontext_check_interface BEFORE INSERT OR UPDATE ON auth.userrolecontext FOR EACH ROW EXECUTE FUNCTION auth.trg_check_single_interface_role()
```
---
## Схема `autodoc`

### Таблицы

#### `schema_dumps`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('autodoc.schema_dumps_id_seq'::regclass) | ✅ |  |
| schema_name | text | ❌ |  |  |  |
| cleartable | text | ✅ |  |  |  |
| makeid | text | ✅ |  |  |  |
| autoinc | text | ✅ |  |  |  |
| index | text | ✅ |  |  |  |
| tablewithrule | text | ✅ |  |  |  |
| view | text | ✅ |  |  |  |
| procedure | text | ✅ |  |  |  |
| func | text | ✅ |  |  |  |
| triggers | text | ✅ |  |  |  |
| jsondata | jsonb | ✅ |  |  |  |
| created_at | timestamp with time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

---

### Хранимые процедуры, функции и триггеры

#### Procedure `dump_schema_to_table`
- **Параметры:** `IN p_schema_name text, IN p_save_data integer DEFAULT 0`

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE autodoc.dump_schema_to_table(IN p_schema_name text, IN p_save_data integer DEFAULT 0)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_cleartable TEXT := '';
    v_makeid TEXT := '';
    v_autoinc TEXT := '';
    v_index TEXT := '';
    v_tablewithrule TEXT := '';
    v_view TEXT := '';
    v_procedure TEXT := '';
    v_func TEXT := '';
    v_triggers TEXT := '';
    v_jsondata JSONB := NULL;

    v_rec RECORD;
    v_col RECORD;
    v_cols TEXT;
    v_is_serial BOOLEAN;
    v_seq_name TEXT;
    v_cons RECORD;
    v_has_id BOOLEAN;
    v_table_name TEXT;
    v_table_data JSONB;
    v_pk_columns TEXT;
BEGIN
    -- 1. cleartable: создание таблиц без ограничений, без ключей, serial -> bigint, все поля nullable
    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        BEGIN
            -- Собираем колонки таблицы
            v_cols := '';
            FOR v_col IN (
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.udt_name,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale
                FROM information_schema.columns c
                WHERE c.table_schema = p_schema_name AND c.table_name = v_rec.tablename
                ORDER BY c.ordinal_position
            ) LOOP
                -- Определяем, является ли колонка serial (автоинкремент)
                v_is_serial := (v_col.column_default LIKE 'nextval(%' AND v_col.udt_name IN ('int4', 'int8'));
                IF v_is_serial THEN
                    -- Заменяем на bigint (длинное целое)
                    v_cols := v_cols || '    ' || quote_ident(v_col.column_name) || ' bigint, ' || E'\n';
                ELSE
                    -- Обычный тип, всегда nullable (NOT NULL не добавляем)
                    CASE v_col.data_type
                        WHEN 'character varying' THEN
                            v_cols := v_cols || '    ' || quote_ident(v_col.column_name) || ' varchar(' || v_col.character_maximum_length || '), ' || E'\n';
                        WHEN 'numeric' THEN
                            v_cols := v_cols || '    ' || quote_ident(v_col.column_name) || ' numeric(' || v_col.numeric_precision || ',' || v_col.numeric_scale || '), ' || E'\n';
                        ELSE
                            v_cols := v_cols || '    ' || quote_ident(v_col.column_name) || ' ' || v_col.udt_name || ', ' || E'\n';
                    END CASE;
                END IF;
            END LOOP;
            -- Убираем последнюю запятую и перевод строки
            v_cols := rtrim(v_cols, ', ' || E'\n');

            -- Формируем CREATE TABLE
            v_cleartable := v_cleartable || 'CREATE TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) || ' (' || E'\n' ||
                            v_cols || E'\n' || ');' || E'\n\n';
        EXCEPTION WHEN OTHERS THEN
            v_cleartable := v_cleartable || '-- Ошибка при обработке таблицы ' || v_rec.tablename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 2. makeid: превращение поля id в первичный ключ (для каждой таблицы, где есть колонка id)
    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        -- Проверяем, есть ли в таблице колонка id
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = p_schema_name AND table_name = v_rec.tablename AND column_name = 'id'
        ) INTO v_has_id;
        IF v_has_id THEN
            v_makeid := v_makeid || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                        ' ADD PRIMARY KEY (id);' || E'\n';
        END IF;
    END LOOP;

    -- 3. autoinc: восстановление автоинкремента для serial-колонок с учётом максимального значения
    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        FOR v_col IN (
            SELECT 
                c.column_name,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema = p_schema_name AND c.table_name = v_rec.tablename
              AND c.column_default LIKE 'nextval(%'
        ) LOOP
            -- Извлекаем имя последовательности из дефолта
            v_seq_name := substring(v_col.column_default from 'nextval\(''([^'']*)''');
            IF v_seq_name IS NOT NULL THEN
                -- Создаём последовательность (если ещё не существует)
                v_autoinc := v_autoinc || 'CREATE SEQUENCE IF NOT EXISTS ' || v_seq_name || ';' || E'\n';
                -- Устанавливаем текущее значение последовательности равным максимуму в таблице (или 1, если таблица пуста)
                v_autoinc := v_autoinc || 'SELECT setval(' || quote_literal(v_seq_name) || 
                             ', COALESCE((SELECT MAX(' || quote_ident(v_col.column_name) || 
                             ') FROM ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) || 
                             '), 1));' || E'\n';
                -- Устанавливаем дефолт для колонки
                v_autoinc := v_autoinc || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                             ' ALTER COLUMN ' || quote_ident(v_col.column_name) || ' SET DEFAULT ' || v_col.column_default || ';' || E'\n';
                -- Привязываем последовательность к колонке
                v_autoinc := v_autoinc || 'ALTER SEQUENCE ' || v_seq_name || ' OWNED BY ' ||
                             quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) || '.' || quote_ident(v_col.column_name) || ';' || E'\n';
            END IF;
        END LOOP;
        v_autoinc := v_autoinc || E'\n';
    END LOOP;

    -- 4. index: все индексы, кроме тех, что являются первичными ключами
    FOR v_rec IN (
        SELECT i.indexdef
        FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_index idx ON idx.indexrelid = c.oid
        WHERE i.schemaname = p_schema_name
          AND NOT idx.indisprimary
        ORDER BY i.tablename, i.indexname
    ) LOOP
        v_index := v_index || v_rec.indexdef || ';' || E'\n';
    END LOOP;

    -- 5. tablewithrule: NOT NULL, DEFAULT (кроме nextval), внешние ключи, check-ограничения
    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        BEGIN
            -- 5.1 NOT NULL и DEFAULT (кроме автоинкремента)
            FOR v_col IN (
                SELECT 
                    c.column_name,
                    c.is_nullable,
                    c.column_default
                FROM information_schema.columns c
                WHERE c.table_schema = p_schema_name AND c.table_name = v_rec.tablename
                ORDER BY c.ordinal_position
            ) LOOP
                IF v_col.is_nullable = 'NO' THEN
                    v_tablewithrule := v_tablewithrule || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                                       ' ALTER COLUMN ' || quote_ident(v_col.column_name) || ' SET NOT NULL;' || E'\n';
                END IF;
                IF v_col.column_default IS NOT NULL AND v_col.column_default NOT LIKE 'nextval(%' THEN
                    v_tablewithrule := v_tablewithrule || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                                       ' ALTER COLUMN ' || quote_ident(v_col.column_name) || ' SET DEFAULT ' || v_col.column_default || ';' || E'\n';
                END IF;
            END LOOP;

            -- 5.2 Внешние ключи
            FOR v_cons IN (
                SELECT
                    conname,
                    pg_get_constraintdef(oid) AS cons_def
                FROM pg_constraint
                WHERE conrelid = (quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename))::regclass
                  AND contype = 'f'
            ) LOOP
                v_tablewithrule := v_tablewithrule || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                                   ' ADD CONSTRAINT ' || quote_ident(v_cons.conname) || ' ' || v_cons.cons_def || ';' || E'\n';
            END LOOP;

            -- 5.3 Check-ограничения
            FOR v_cons IN (
                SELECT
                    conname,
                    pg_get_constraintdef(oid) AS cons_def
                FROM pg_constraint
                WHERE conrelid = (quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename))::regclass
                  AND contype = 'c'
            ) LOOP
                v_tablewithrule := v_tablewithrule || 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) ||
                                   ' ADD CONSTRAINT ' || quote_ident(v_cons.conname) || ' ' || v_cons.cons_def || ';' || E'\n';
            END LOOP;

            v_tablewithrule := v_tablewithrule || E'\n';
        EXCEPTION WHEN OTHERS THEN
            v_tablewithrule := v_tablewithrule || '-- Ошибка при обработке ограничений таблицы ' || v_rec.tablename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 6. Представления
    FOR v_rec IN (
        SELECT viewname, definition
        FROM pg_views
        WHERE schemaname = p_schema_name
        ORDER BY viewname
    ) LOOP
        v_view := v_view || 'CREATE VIEW ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.viewname) || ' AS ' || E'\n' ||
                  v_rec.definition || ';' || E'\n\n';
    END LOOP;

    -- 7. Процедуры (prokind = 'p')
    FOR v_rec IN (
        SELECT p.proname, pg_get_functiondef(p.oid) AS funcdef
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = p_schema_name
          AND p.prokind = 'p'
        ORDER BY p.proname
    ) LOOP
        v_procedure := v_procedure || v_rec.funcdef || E'\n';
    END LOOP;

    -- 8. Функции (prokind = 'f')
    FOR v_rec IN (
        SELECT p.proname, pg_get_functiondef(p.oid) AS funcdef
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = p_schema_name
          AND p.prokind = 'f'
        ORDER BY p.proname
    ) LOOP
        v_func := v_func || v_rec.funcdef || E'\n';
    END LOOP;

    -- 9. Триггеры
    FOR v_rec IN (
        SELECT t.tgname, pg_get_triggerdef(t.oid) AS trigdef
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = p_schema_name
          AND NOT t.tgisinternal
        ORDER BY t.tgname
    ) LOOP
        v_triggers := v_triggers || v_rec.trigdef || ';' || E'\n';
    END LOOP;

    -- 10. Данные таблиц в JSON (если p_save_data = 1)
    IF p_save_data = 1 THEN
        FOR v_rec IN (
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = p_schema_name
            ORDER BY tablename
        ) LOOP
            BEGIN
                v_table_name := quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename);
                EXECUTE format('SELECT jsonb_agg(row_to_json(t)) FROM %s t', v_table_name) INTO v_table_data;
                IF v_jsondata IS NULL THEN
                    v_jsondata := jsonb_build_object(v_rec.tablename, v_table_data);
                ELSE
                    v_jsondata := v_jsondata || jsonb_build_object(v_rec.tablename, v_table_data);
                END IF;
            EXCEPTION WHEN OTHERS THEN
                -- Если таблица пуста или ошибка, добавляем пустой массив
                IF v_jsondata IS NULL THEN
                    v_jsondata := jsonb_build_object(v_rec.tablename, '[]'::jsonb);
                ELSE
                    v_jsondata := v_jsondata || jsonb_build_object(v_rec.tablename, '[]'::jsonb);
                END IF;
            END;
        END LOOP;
    END IF;

    -- Вставка результата
    INSERT INTO autodoc.schema_dumps (
        schema_name, cleartable, makeid, autoinc, index, tablewithrule,
        view, procedure, func, triggers, jsondata
    ) VALUES (
        p_schema_name,
        v_cleartable,
        v_makeid,
        v_autoinc,
        v_index,
        v_tablewithrule,
        v_view,
        v_procedure,
        v_func,
        v_triggers,
        v_jsondata
    );

    RAISE NOTICE 'Дамп схемы "%" сохранён в autodoc.schema_dumps (id: %)', p_schema_name, currval('autodoc.schema_dumps_id_seq');
    IF p_save_data = 1 THEN
        RAISE NOTICE 'Данные таблиц также сохранены в поле jsondata.';
    END IF;
END;
$procedure$

```
---
## Схема `lang`

### Таблицы

#### `translations`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('lang.translations_id_seq'::regclass) | ✅ |  |
| label_key | character varying(255) | ❌ |  |  |  |
| language | character varying(10) | ❌ |  |  |  |
| translation | text | ❌ |  |  |  |
| created_at | timestamp with time zone | ✅ | now() |  |  |
| updated_at | timestamp with time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

**Уникальные ограничения:**
- `translations_label_key_language_key`: (`label_key, language`)

---
## Схема `public`

### Таблицы

#### `schema_documentation`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('schema_documentation_id_seq'::regclass) | ✅ |  |
| schema_name | text | ❌ |  |  |  |
| doc_content | text | ❌ |  |  |  |
| created_at | timestamp with time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

---

#### `schema_dumps`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('schema_dumps_id_seq'::regclass) | ✅ |  |
| schema_name | text | ❌ |  |  |  |
| dump_content | text | ❌ |  |  |  |
| created_at | timestamp with time zone | ✅ | now() |  |  |
| user_name | text | ✅ | CURRENT_USER |  |  |
| database_name | text | ✅ | current_database() |  |  |
| objects_count | integer | ✅ |  |  |  |
| dump_size_bytes | integer | ✅ |  |  |  |

**Первичный ключ:** `id`

---

#### `schema_stats`

**Колонки:**
| Имя | Тип | Nullable | По умолчанию | Serial | Комментарий |
|-----|-----|----------|--------------|--------|-------------|
| id | integer | ❌ | nextval('schema_stats_id_seq'::regclass) | ✅ |  |
| schema_name | text | ❌ |  |  |  |
| entitytype_name | text | ✅ |  |  |  |
| object_type | text | ✅ |  |  |  |
| count | bigint | ✅ |  |  |  |
| size_bytes | bigint | ✅ |  |  |  |
| collected_at | timestamp with time zone | ✅ | now() |  |  |

**Первичный ключ:** `id`

---

### Хранимые процедуры, функции и триггеры

#### Procedure `dump_schema_objects`
- **Параметры:** `IN p_schema_name text, IN p_output_file text`

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE public.dump_schema_objects(IN p_schema_name text, IN p_output_file text)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_object_sql TEXT;
    v_file_content TEXT := '';
    v_extension TEXT;
    v_dir_path TEXT;
    v_file_name TEXT;
    v_rec RECORD;
BEGIN
    -- Определяем путь к файлу (можно изменить под вашу систему)
    -- Для Linux/Unix: '/tmp/' или другая доступная директория
    -- Для Windows: 'C:/temp/'
    v_dir_path := '/tmp/sql/'; -- Измените на нужный путь
    v_file_name := v_dir_path || p_output_file;
    
    -- Заголовок файла
    v_file_content := '-- Дамп объектов схемы: ' || p_schema_name || E'\n';
    v_file_content := v_file_content || '-- Создано: ' || CURRENT_TIMESTAMP || E'\n';
    v_file_content := v_file_content || '-- Пользователь: ' || current_user || E'\n';
    v_file_content := v_file_content || '-- База данных: ' || current_database() || E'\n';
    v_file_content := v_file_content || E'-- ============================================\n\n';

    -- 1. ТАБЛИЦЫ
    v_file_content := v_file_content || E'-- 1. ТАБЛИЦЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            tablename
        FROM pg_tables 
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        BEGIN
            v_object_sql := 'DROP TABLE IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || public.pg_get_tabledef(quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename)) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке таблицы ' || v_rec.tablename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 2. ПОСЛЕДОВАТЕЛЬНОСТИ (SEQUENCES)
    v_file_content := v_file_content || E'\n-- 2. ПОСЛЕДОВАТЕЛЬНОСТИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = p_schema_name
        ORDER BY sequence_name
    ) LOOP
        BEGIN
            v_object_sql := 'DROP SEQUENCE IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.sequence_name) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || public.pg_get_sequencedef(quote_ident(p_schema_name) || '.' || quote_ident(v_rec.sequence_name)) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке последовательности ' || v_rec.sequence_name || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 3. ИНДЕКСЫ
    v_file_content := v_file_content || E'\n-- 3. ИНДЕКСЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            i.indexname,
            c.oid as index_oid
        FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE i.schemaname = p_schema_name
            AND n.nspname = p_schema_name
        ORDER BY i.tablename, i.indexname
    ) LOOP
        BEGIN
            v_object_sql := '-- Индекс: ' || v_rec.indexname || E'\n';
            v_object_sql := v_object_sql || pg_get_indexdef(v_rec.index_oid) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке индекса ' || v_rec.indexname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 4. ТРИГГЕРЫ
    v_file_content := v_file_content || E'\n-- 4. ТРИГГЕРЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            t.tgname,
            t.oid as trigger_oid
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = p_schema_name
            AND NOT t.tgisinternal
        ORDER BY t.tgname
    ) LOOP
        BEGIN
            v_object_sql := '-- Триггер: ' || v_rec.tgname || E'\n';
            v_object_sql := v_object_sql || pg_get_triggerdef(v_rec.trigger_oid) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке триггера ' || v_rec.tgname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 5. ХРАНИМЫЕ ПРОЦЕДУРЫ И ФУНКЦИИ
    v_file_content := v_file_content || E'\n-- 5. ХРАНИМЫЕ ПРОЦЕДУРЫ И ФУНКЦИИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            p.proname,
            p.oid as proc_oid,
            pg_get_function_identity_arguments(p.oid) as func_args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = p_schema_name
        ORDER BY p.proname
    ) LOOP
        BEGIN
            v_object_sql := 'DROP FUNCTION IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.proname) || 
                            '(' || v_rec.func_args || ') CASCADE;' || E'\n';
            v_object_sql := v_object_sql || pg_get_functiondef(v_rec.proc_oid) || E'\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке функции ' || v_rec.proname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 6. ПРАВИЛА (RULES)
    v_file_content := v_file_content || E'\n-- 6. ПРАВИЛА\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            rulename,
            definition
        FROM pg_rules
        WHERE schemaname = p_schema_name
        ORDER BY rulename
    ) LOOP
        BEGIN
            v_object_sql := '-- Правило: ' || v_rec.rulename || E'\n';
            v_object_sql := v_object_sql || v_rec.definition || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке правила ' || v_rec.rulename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 7. ВНЕШНИЕ КЛЮЧИ (FOREIGN KEYS) - СВЯЗИ
    v_file_content := v_file_content || E'\n-- 7. ВНЕШНИЕ КЛЮЧИ (СВЯЗИ)\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            c.conname,
            c.conrelid,
            c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'f'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке внешнего ключа ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 8. ПЕРВИЧНЫЕ КЛЮЧИ (PRIMARY KEYS)
    v_file_content := v_file_content || E'\n-- 8. ПЕРВИЧНЫЕ КЛЮЧИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            c.conname,
            c.conrelid,
            c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'p'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке первичного ключа ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 9. УНИКАЛЬНЫЕ ОГРАНИЧЕНИЯ (UNIQUE CONSTRAINTS)
    v_file_content := v_file_content || E'\n-- 9. УНИКАЛЬНЫЕ ОГРАНИЧЕНИЯ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            c.conname,
            c.conrelid,
            c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'u'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке уникального ограничения ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 10. ПРЕДСТАВЛЕНИЯ (VIEWS)
    v_file_content := v_file_content || E'\n-- 10. ПРЕДСТАВЛЕНИЯ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT 
            viewname,
            definition
        FROM pg_views
        WHERE schemaname = p_schema_name
        ORDER BY viewname
    ) LOOP
        BEGIN
            v_object_sql := 'DROP VIEW IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.viewname) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || 'CREATE VIEW ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.viewname) || ' AS ' || E'\n';
            v_object_sql := v_object_sql || v_rec.definition || E';\n\n';
            v_file_content := v_file_content || v_object_sql;
        EXCEPTION WHEN OTHERS THEN
            v_file_content := v_file_content || '-- Ошибка при выгрузке представления ' || v_rec.viewname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- Запись в файл
    BEGIN
        -- Для PostgreSQL 9.3 и новее
        EXECUTE format('COPY (SELECT %L) TO %L', v_file_content, v_file_name);
        RAISE NOTICE 'Дамп успешно сохранен в файл: %', v_file_name;
        RAISE NOTICE 'Размер файла: % байт', length(v_file_content);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE WARNING 'Не удалось записать файл: %', SQLERRM;
            RAISE WARNING 'Убедитесь, что директория % существует и доступна для записи', v_dir_path;
            -- Альтернативный вывод на экран (только первые 1000 символов)
            RAISE NOTICE 'Первые 1000 символов дампа:';
            RAISE NOTICE '%', left(v_file_content, 1000);
    END;
END;
$procedure$

```
---

#### Procedure `dump_schema_to_table`
- **Параметры:** `IN p_schema_name text`

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE public.dump_schema_to_table(IN p_schema_name text)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_object_sql TEXT;
    v_dump_content TEXT := '';
    v_rec RECORD;
    v_object_count INTEGER := 0;
BEGIN
    -- Заголовок дампа
    v_dump_content := '-- Дамп объектов схемы: ' || p_schema_name || E'\n';
    v_dump_content := v_dump_content || '-- Создано: ' || CURRENT_TIMESTAMP || E'\n';
    v_dump_content := v_dump_content || '-- Пользователь: ' || current_user || E'\n';
    v_dump_content := v_dump_content || '-- База данных: ' || current_database() || E'\n';
    v_dump_content := v_dump_content || E'-- ============================================\n\n';

    -- 1. ТАБЛИЦЫ
    v_dump_content := v_dump_content || E'-- 1. ТАБЛИЦЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables 
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        BEGIN
            v_object_sql := 'DROP TABLE IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || public.pg_get_tabledef(quote_ident(p_schema_name) || '.' || quote_ident(v_rec.tablename)) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке таблицы ' || v_rec.tablename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 2. ПОСЛЕДОВАТЕЛЬНОСТИ
    v_dump_content := v_dump_content || E'\n-- 2. ПОСЛЕДОВАТЕЛЬНОСТИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = p_schema_name
        ORDER BY sequence_name
    ) LOOP
        BEGIN
            v_object_sql := 'DROP SEQUENCE IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.sequence_name) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || public.pg_get_sequencedef(quote_ident(p_schema_name) || '.' || quote_ident(v_rec.sequence_name)) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке последовательности ' || v_rec.sequence_name || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 3. ИНДЕКСЫ
    v_dump_content := v_dump_content || E'\n-- 3. ИНДЕКСЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT i.indexname, c.oid as index_oid
        FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE i.schemaname = p_schema_name
            AND n.nspname = p_schema_name
        ORDER BY i.tablename, i.indexname
    ) LOOP
        BEGIN
            v_object_sql := '-- Индекс: ' || v_rec.indexname || E'\n';
            v_object_sql := v_object_sql || pg_get_indexdef(v_rec.index_oid) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке индекса ' || v_rec.indexname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 4. ТРИГГЕРЫ
    v_dump_content := v_dump_content || E'\n-- 4. ТРИГГЕРЫ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT t.tgname, t.oid as trigger_oid
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = p_schema_name
            AND NOT t.tgisinternal
        ORDER BY t.tgname
    ) LOOP
        BEGIN
            v_object_sql := '-- Триггер: ' || v_rec.tgname || E'\n';
            v_object_sql := v_object_sql || pg_get_triggerdef(v_rec.trigger_oid) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке триггера ' || v_rec.tgname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 5. ФУНКЦИИ И ПРОЦЕДУРЫ
    v_dump_content := v_dump_content || E'\n-- 5. ХРАНИМЫЕ ПРОЦЕДУРЫ И ФУНКЦИИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT p.proname, p.oid as proc_oid, pg_get_function_identity_arguments(p.oid) as func_args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = p_schema_name
        ORDER BY p.proname
    ) LOOP
        BEGIN
            v_object_sql := 'DROP FUNCTION IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.proname) || 
                            '(' || v_rec.func_args || ') CASCADE;' || E'\n';
            v_object_sql := v_object_sql || pg_get_functiondef(v_rec.proc_oid) || E'\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке функции ' || v_rec.proname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 6. ПРАВИЛА
    v_dump_content := v_dump_content || E'\n-- 6. ПРАВИЛА\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT rulename, definition
        FROM pg_rules
        WHERE schemaname = p_schema_name
        ORDER BY rulename
    ) LOOP
        BEGIN
            v_object_sql := '-- Правило: ' || v_rec.rulename || E'\n';
            v_object_sql := v_object_sql || v_rec.definition || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке правила ' || v_rec.rulename || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 7. ВНЕШНИЕ КЛЮЧИ
    v_dump_content := v_dump_content || E'\n-- 7. ВНЕШНИЕ КЛЮЧИ (СВЯЗИ)\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT c.conname, c.conrelid, c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'f'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке внешнего ключа ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 8. ПЕРВИЧНЫЕ КЛЮЧИ
    v_dump_content := v_dump_content || E'\n-- 8. ПЕРВИЧНЫЕ КЛЮЧИ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT c.conname, c.conrelid, c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'p'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке первичного ключа ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 9. УНИКАЛЬНЫЕ ОГРАНИЧЕНИЯ
    v_dump_content := v_dump_content || E'\n-- 9. УНИКАЛЬНЫЕ ОГРАНИЧЕНИЯ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT c.conname, c.conrelid, c.oid as constraint_oid
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = p_schema_name
            AND c.contype = 'u'
        ORDER BY c.conname
    ) LOOP
        BEGIN
            v_object_sql := 'ALTER TABLE ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.conrelid::regclass::text) || 
                            ' ADD CONSTRAINT ' || quote_ident(v_rec.conname) || ' ' || 
                            pg_get_constraintdef(v_rec.constraint_oid) || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке уникального ограничения ' || v_rec.conname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- 10. ПРЕДСТАВЛЕНИЯ
    v_dump_content := v_dump_content || E'\n-- 10. ПРЕДСТАВЛЕНИЯ\n-- ============================================\n\n';
    
    FOR v_rec IN (
        SELECT viewname, definition
        FROM pg_views
        WHERE schemaname = p_schema_name
        ORDER BY viewname
    ) LOOP
        BEGIN
            v_object_sql := 'DROP VIEW IF EXISTS ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.viewname) || ' CASCADE;' || E'\n';
            v_object_sql := v_object_sql || 'CREATE VIEW ' || quote_ident(p_schema_name) || '.' || quote_ident(v_rec.viewname) || ' AS ' || E'\n';
            v_object_sql := v_object_sql || v_rec.definition || E';\n\n';
            v_dump_content := v_dump_content || v_object_sql;
            v_object_count := v_object_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_dump_content := v_dump_content || '-- Ошибка при выгрузке представления ' || v_rec.viewname || ': ' || SQLERRM || E'\n\n';
        END;
    END LOOP;

    -- Вставляем дамп в таблицу
    INSERT INTO public.schema_dumps (schema_name, dump_content, objects_count, dump_size_bytes)
    VALUES (p_schema_name, v_dump_content, v_object_count, length(v_dump_content));
    
    RAISE NOTICE 'Дамп схемы "%" сохранён в таблицу schema_dumps (id: %)', p_schema_name, currval('public.schema_dumps_id_seq');
    RAISE NOTICE 'Выгружено объектов: %, размер: % байт', v_object_count, length(v_dump_content);
END;
$procedure$

```
---

#### Procedure `gather_schema_stats`
- **Параметры:** ``

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE public.gather_schema_stats()
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    rec RECORD;
BEGIN
    -- Статистика по типам сущностей (количество инстансов)
    FOR rec IN (
        SELECT 
            e.cname AS entitytype_name,
            COUNT(i.id) AS instance_count
        FROM data.entity_instances i
        JOIN meta.entitytypes e ON e.id = i.entitytypeid
        GROUP BY e.cname
    ) LOOP
        INSERT INTO public.schema_stats (schema_name, entitytype_name, object_type, count)
        VALUES ('data', rec.entitytype_name, 'instances', rec.instance_count);
    END LOOP;

    -- Количество версий
    INSERT INTO public.schema_stats (schema_name, object_type, count)
    SELECT 'data', 'versions', COUNT(*) FROM data.entity_versions;

    -- Количество записей видимости
    INSERT INTO public.schema_stats (schema_name, object_type, count)
    SELECT 'data', 'visibility', COUNT(*) FROM data.entity_visibility;

    -- Размер таблиц (с использованием pg_total_relation_size)
    FOR rec IN (
        SELECT schemaname, tablename, pg_total_relation_size(schemaname||'.'||tablename) AS size
        FROM pg_tables
        WHERE schemaname IN ('meta', 'data', 'auth', 'ext')
    ) LOOP
        INSERT INTO public.schema_stats (schema_name, object_type, count, size_bytes)
        VALUES (rec.schemaname, 'table_'||rec.tablename, NULL, rec.size);
    END LOOP;

    RAISE NOTICE 'Статистика собрана.';
END;
$procedure$

```
---

#### Procedure `generate_schema_documentation`
- **Параметры:** `IN p_schema_name text`

**Определение:**
```sql
CREATE OR REPLACE PROCEDURE public.generate_schema_documentation(IN p_schema_name text)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_doc TEXT := '';
    v_rec RECORD;
    v_rec2 RECORD;
    v_table_comment TEXT;
    v_temp TEXT;
BEGIN
    -- Заголовок документа
    v_doc := '# Документация схемы ' || p_schema_name || E'\n';
    v_doc := v_doc || 'Сгенерировано: ' || CURRENT_TIMESTAMP || E'\n\n';

    -- =====================================================================
    -- 1. ТАБЛИЦЫ
    -- =====================================================================
    v_doc := v_doc || '## Таблицы' || E'\n\n';

    FOR v_rec IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = p_schema_name
        ORDER BY tablename
    ) LOOP
        -- Заголовок таблицы
        v_doc := v_doc || '### ' || v_rec.tablename || E'\n\n';

        -- Комментарий к таблице
        SELECT obj_description(c.oid) INTO v_table_comment
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = p_schema_name AND c.relname = v_rec.tablename AND c.relkind = 'r';

        IF v_table_comment IS NOT NULL AND v_table_comment != '' THEN
            v_doc := v_doc || '*Описание таблицы:* ' || v_table_comment || E'\n\n';
        END IF;

        -- Колонки
        v_doc := v_doc || '**Колонки:**' || E'\n\n';
        v_doc := v_doc || '| Имя | Тип данных | Размер | По умолчанию | Nullable | Комментарий |' || E'\n';
        v_doc := v_doc || '|-----|------------|--------|--------------|----------|-------------|' || E'\n';

        FOR v_rec2 IN (
            SELECT 
                cols.column_name,
                cols.data_type,
                cols.character_maximum_length,
                cols.numeric_precision,
                cols.numeric_scale,
                cols.column_default,
                cols.is_nullable,
                col_description(c.oid, cols.ordinal_position) AS comment
            FROM information_schema.columns cols
            JOIN pg_class c ON c.relname = cols.table_name
            JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = cols.table_schema
            WHERE cols.table_schema = p_schema_name AND cols.table_name = v_rec.tablename
            ORDER BY cols.ordinal_position
        ) LOOP
            v_doc := v_doc || '| ' || v_rec2.column_name || ' | ' || v_rec2.data_type;

            -- Размер/точность
            IF v_rec2.character_maximum_length IS NOT NULL THEN
                v_doc := v_doc || '(' || v_rec2.character_maximum_length || ')';
            ELSIF v_rec2.numeric_precision IS NOT NULL THEN
                v_doc := v_doc || '(' || v_rec2.numeric_precision || ',' || v_rec2.numeric_scale || ')';
            END IF;

            v_doc := v_doc || ' | ';  -- размер (уже учтён)
            v_doc := v_doc || coalesce(v_rec2.column_default, '') || ' | ';
            v_doc := v_doc || v_rec2.is_nullable || ' | ';
            v_doc := v_doc || coalesce(v_rec2.comment, '') || ' |' || E'\n';
        END LOOP;
        v_doc := v_doc || E'\n';

        -- Ограничения (первичные, внешние, уникальные, проверки)
        v_doc := v_doc || '**Ограничения:**' || E'\n\n';
        FOR v_rec2 IN (
            SELECT 
                c.conname,
                CASE c.contype
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 'c' THEN 'CHECK'
                    ELSE 'OTHER'
                END AS constraint_type,
                pg_get_constraintdef(c.oid) AS constraint_def
            FROM pg_constraint c
            JOIN pg_class cl ON cl.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = cl.relnamespace
            WHERE n.nspname = p_schema_name AND cl.relname = v_rec.tablename
            ORDER BY c.contype, c.conname
        ) LOOP
            v_doc := v_doc || '- **' || v_rec2.constraint_type || '** `' || v_rec2.conname || '`: ' || v_rec2.constraint_def || E'\n';
        END LOOP;
        v_doc := v_doc || E'\n';

        -- Индексы
        v_doc := v_doc || '**Индексы:**' || E'\n\n';
        FOR v_rec2 IN (
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = p_schema_name AND tablename = v_rec.tablename
            ORDER BY indexname
        ) LOOP
            v_doc := v_doc || '- `' || v_rec2.indexname || '`: ' || v_rec2.indexdef || E'\n';
        END LOOP;
        v_doc := v_doc || E'\n';

        -- Правила (rules)
        v_doc := v_doc || '**Правила (Rules):**' || E'\n\n';
        FOR v_rec2 IN (
            SELECT 
                r.rulename,
                r.definition,
                obj_description(c.oid) AS comment
            FROM pg_rules r
            JOIN pg_class c ON c.relname = r.tablename AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = r.schemaname)
            WHERE r.schemaname = p_schema_name AND r.tablename = v_rec.tablename
            ORDER BY r.rulename
        ) LOOP
            v_doc := v_doc || '- Правило `' || v_rec2.rulename || '`:' || E'\n';
            IF v_rec2.comment IS NOT NULL AND v_rec2.comment != '' THEN
                v_doc := v_doc || '  *Комментарий:* ' || v_rec2.comment || E'\n';
            END IF;
            v_doc := v_doc || '  ```sql' || E'\n';
            v_doc := v_doc || '  ' || replace(v_rec2.definition, E'\n', E'\n  ') || E'\n';
            v_doc := v_doc || '  ```' || E'\n';
        END LOOP;
        v_doc := v_doc || E'\n';

        -- Триггеры
        v_doc := v_doc || '**Триггеры:**' || E'\n\n';
        FOR v_rec2 IN (
            SELECT 
                t.tgname,
                pg_get_triggerdef(t.oid) AS trigger_def,
                obj_description(t.oid) AS comment
            FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = p_schema_name AND c.relname = v_rec.tablename
                AND NOT t.tgisinternal
            ORDER BY t.tgname
        ) LOOP
            v_doc := v_doc || '- Триггер `' || v_rec2.tgname || '`:' || E'\n';
            IF v_rec2.comment IS NOT NULL AND v_rec2.comment != '' THEN
                v_doc := v_doc || '  *Комментарий:* ' || v_rec2.comment || E'\n';
            END IF;
            v_doc := v_doc || '  ```sql' || E'\n';
            v_doc := v_doc || '  ' || replace(v_rec2.trigger_def, E'\n', E'\n  ') || E'\n';
            v_doc := v_doc || '  ```' || E'\n';
        END LOOP;
        v_doc := v_doc || E'\n';
    END LOOP;

    -- =====================================================================
    -- 2. ХРАНИМЫЕ ПРОЦЕДУРЫ И ФУНКЦИИ
    -- =====================================================================
    v_doc := v_doc || '## Хранимые процедуры и функции' || E'\n\n';

    FOR v_rec IN (
        SELECT 
            p.proname,
            p.oid,
            pg_get_function_identity_arguments(p.oid) AS args,
            pg_get_function_result(p.oid) AS result_type,
            l.lanname AS language,
            obj_description(p.oid) AS description
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language l ON l.oid = p.prolang
        WHERE n.nspname = p_schema_name
        ORDER BY p.proname
    ) LOOP
        v_doc := v_doc || '### ' || v_rec.proname || E'\n\n';
        v_doc := v_doc || '- **Сигнатура:** `' || v_rec.proname || '(' || v_rec.args || ')`' || E'\n';
        v_doc := v_doc || '- **Возвращаемый тип:** ' || coalesce(v_rec.result_type, 'void') || E'\n';
        v_doc := v_doc || '- **Язык:** ' || v_rec.language || E'\n';
        IF v_rec.description IS NOT NULL AND v_rec.description != '' THEN
            v_doc := v_doc || '- **Описание:** ' || v_rec.description || E'\n';
        END IF;
        v_doc := v_doc || E'\n';
    END LOOP;

    -- =====================================================================
    -- 3. ПРЕДСТАВЛЕНИЯ (VIEWS)
    -- =====================================================================
    v_doc := v_doc || '## Представления' || E'\n\n';

    FOR v_rec IN (
        SELECT 
            v.viewname,
            v.definition,
            obj_description(c.oid) AS description
        FROM pg_views v
        JOIN pg_class c ON c.relname = v.viewname
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE v.schemaname = p_schema_name AND n.nspname = p_schema_name
        ORDER BY v.viewname
    ) LOOP
        v_doc := v_doc || '### ' || v_rec.viewname || E'\n\n';
        IF v_rec.description IS NOT NULL AND v_rec.description != '' THEN
            v_doc := v_doc || '*Описание:* ' || v_rec.description || E'\n\n';
        END IF;
        v_doc := v_doc || '**Определение:**' || E'\n';
        v_doc := v_doc || '```sql' || E'\n';
        v_doc := v_doc || v_rec.definition || E'\n';
        v_doc := v_doc || '```' || E'\n\n';
    END LOOP;

    -- =====================================================================
    -- 4. ПРОЧИЕ ОБЪЕКТЫ (последовательности, составные типы, перечисления)
    -- =====================================================================
    v_doc := v_doc || '## Прочие объекты' || E'\n\n';

    -- Последовательности
    v_doc := v_doc || '### Последовательности' || E'\n\n';
    FOR v_rec IN (
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = p_schema_name
        ORDER BY sequence_name
    ) LOOP
        v_doc := v_doc || '- `' || v_rec.sequence_name || '`' || E'\n';
    END LOOP;
    v_doc := v_doc || E'\n';

    -- Типы (составные, перечисления)
    v_doc := v_doc || '### Типы' || E'\n\n';
    FOR v_rec IN (
        SELECT 
            t.typname,
            obj_description(t.oid) AS description
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = p_schema_name
            AND t.typtype IN ('c', 'e')  -- composite, enum
        ORDER BY t.typname
    ) LOOP
        v_doc := v_doc || '- `' || v_rec.typname || '`';
        IF v_rec.description IS NOT NULL AND v_rec.description != '' THEN
            v_doc := v_doc || ': ' || v_rec.description;
        END IF;
        v_doc := v_doc || E'\n';
    END LOOP;
    v_doc := v_doc || E'\n';

    -- Вставляем результат в таблицу
    INSERT INTO public.schema_documentation (schema_name, doc_content)
    VALUES (p_schema_name, v_doc);

    RAISE NOTICE 'Документация для схемы "%" сохранена в таблицу schema_documentation (id: %)', 
                 p_schema_name, currval('public.schema_documentation_id_seq');
END;
$procedure$

```
---

#### Function `armor`
- **Сигнатура:** `armor(bytea)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.armor(bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_armor$function$

```
---

#### Function `armor`
- **Сигнатура:** `armor(bytea, text[], text[])`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.armor(bytea, text[], text[])
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_armor$function$

```
---

#### Function `crypt`
- **Сигнатура:** `crypt(text, text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.crypt(text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_crypt$function$

```
---

#### Function `dearmor`
- **Сигнатура:** `dearmor(text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.dearmor(text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_dearmor$function$

```
---

#### Function `decrypt`
- **Сигнатура:** `decrypt(bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.decrypt(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_decrypt$function$

```
---

#### Function `decrypt_iv`
- **Сигнатура:** `decrypt_iv(bytea, bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.decrypt_iv(bytea, bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_decrypt_iv$function$

```
---

#### Function `digest`
- **Сигнатура:** `digest(text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.digest(text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_digest$function$

```
---

#### Function `digest`
- **Сигнатура:** `digest(bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.digest(bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_digest$function$

```
---

#### Function `encrypt`
- **Сигнатура:** `encrypt(bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.encrypt(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_encrypt$function$

```
---

#### Function `encrypt_iv`
- **Сигнатура:** `encrypt_iv(bytea, bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.encrypt_iv(bytea, bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_encrypt_iv$function$

```
---

#### Function `gen_random_bytes`
- **Сигнатура:** `gen_random_bytes(integer)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.gen_random_bytes(integer)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_random_bytes$function$

```
---

#### Function `gen_random_uuid`
- **Сигнатура:** `gen_random_uuid()`
- **Возвращает:** uuid

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.gen_random_uuid()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/pgcrypto', $function$pg_random_uuid$function$

```
---

#### Function `gen_salt`
- **Сигнатура:** `gen_salt(text, integer)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.gen_salt(text, integer)
 RETURNS text
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_gen_salt_rounds$function$

```
---

#### Function `gen_salt`
- **Сигнатура:** `gen_salt(text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.gen_salt(text)
 RETURNS text
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_gen_salt$function$

```
---

#### Function `get_entity_hierarchy_iterative`
- **Сигнатура:** `get_entity_hierarchy_iterative(p_alias text, p_date timestamp without time zone DEFAULT now())`
- **Возвращает:** TABLE(id integer, parentid integer, level integer, data jsonb)

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.get_entity_hierarchy_iterative(p_alias text, p_date timestamp without time zone DEFAULT now())
 RETURNS TABLE(id integer, parentid integer, level integer, data jsonb)
 LANGUAGE plpgsql
AS $function$
DECLARE
    entitytype_id integer;
    v_level integer := 0;
    v_count integer;
    v_selected_ids integer[] := '{}';
BEGIN
    SELECT id INTO entitytype_id FROM meta.entitytypes WHERE calias = p_alias;
    IF entitytype_id IS NULL THEN
        RAISE EXCEPTION 'Тип сущности % не найден', p_alias;
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS temp_entity_hierarchy (
        id integer PRIMARY KEY,
        parentid integer,
        level integer,
        data jsonb
    ) ON COMMIT DROP;

    -- Выбираем корни (parentinstanceid IS NULL в версии на дату)
    INSERT INTO temp_entity_hierarchy (id, parentid, level, data)
    SELECT i.id, v.parentinstanceid, 0,
           jsonb_build_object(
               'instanceid', i.id,
               'versionid', v.id,
               'cname', v.cname,
               'parentinstanceid', v.parentinstanceid,
               'tdt_start', v.tdt_start,
               'tdt_end', v.tdt_end,
               'cversionstatus', v.cversionstatus
           ) || to_jsonb(i.*) || to_jsonb(v.*)  -- все поля instance и version
    FROM data.entity_instances i
    JOIN data.entity_versions v ON i.id = v.instanceid
    WHERE i.entitytypeid = entitytype_id
      AND v.cversionstatus = 'Active'
      AND v.tdt_start <= p_date
      AND v.tdt_end > p_date
      AND v.parentinstanceid IS NULL;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    IF v_count > 0 THEN
        SELECT array_agg(id) INTO v_selected_ids FROM temp_entity_hierarchy WHERE level = 0;
    END IF;

    WHILE v_count > 0 LOOP
        v_level := v_level + 1;

        INSERT INTO temp_entity_hierarchy (id, parentid, level, data)
        SELECT i.id, v.parentinstanceid, v_level,
               jsonb_build_object(
                   'instanceid', i.id,
                   'versionid', v.id,
                   'cname', v.cname,
                   'parentinstanceid', v.parentinstanceid,
                   'tdt_start', v.tdt_start,
                   'tdt_end', v.tdt_end,
                   'cversionstatus', v.cversionstatus
               ) || to_jsonb(i.*) || to_jsonb(v.*)
        FROM data.entity_instances i
        JOIN data.entity_versions v ON i.id = v.instanceid
        WHERE i.entitytypeid = entitytype_id
          AND v.cversionstatus = 'Active'
          AND v.tdt_start <= p_date
          AND v.tdt_end > p_date
          AND v.parentinstanceid = ANY(v_selected_ids)
          AND i.id NOT IN (SELECT id FROM temp_entity_hierarchy);

        GET DIAGNOSTICS v_count = ROW_COUNT;
        IF v_count > 0 THEN
            SELECT array_agg(id) INTO v_selected_ids FROM temp_entity_hierarchy;
        END IF;
    END LOOP;

    RETURN QUERY SELECT th.id, th.parentid, th.level, th.data FROM temp_entity_hierarchy th ORDER BY th.level, th.id;
END;
$function$

```
---

#### Function `get_hierarchy_iterative`
- **Сигнатура:** `get_hierarchy_iterative(p_table text, p_id_field text, p_parent_field text, p_fields text[] DEFAULT NULL::text[])`
- **Возвращает:** TABLE(id integer, parentid integer, level integer, data jsonb)

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.get_hierarchy_iterative(p_table text, p_id_field text, p_parent_field text, p_fields text[] DEFAULT NULL::text[])
 RETURNS TABLE(id integer, parentid integer, level integer, data jsonb)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_sql text;
    v_level integer := 0;
    v_count integer;
    v_selected_ids integer[] := '{}';
BEGIN
    -- Создаём временную таблицу для накопления результатов
    CREATE TEMP TABLE IF NOT EXISTS temp_hierarchy (
        id integer PRIMARY KEY,
        parentid integer,
        level integer,
        data jsonb
    ) ON COMMIT DROP;

    -- Шаг 1: выбираем корни (parentid IS NULL)
    v_sql := format('
        INSERT INTO temp_hierarchy (id, parentid, level, data)
        SELECT t.%I, t.%I, 0, row_to_json(t.*)
        FROM %s t
        WHERE t.%I IS NULL',
        p_id_field, p_parent_field, p_table, p_parent_field
    );
    EXECUTE v_sql;
    GET DIAGNOSTICS v_count = ROW_COUNT;

    -- Если корни есть, сохраняем их ID
    IF v_count > 0 THEN
        EXECUTE 'SELECT array_agg(id) FROM temp_hierarchy WHERE level = 0' INTO v_selected_ids;
    END IF;

    -- Цикл: пока добавляются новые записи
    WHILE v_count > 0 LOOP
        v_level := v_level + 1;

        -- Выбираем детей уже выбранных узлов, которые ещё не добавлены
        v_sql := format('
            INSERT INTO temp_hierarchy (id, parentid, level, data)
            SELECT t.%I, t.%I, %L, row_to_json(t.*)
            FROM %s t
            WHERE t.%I = ANY(%L)
              AND t.%I NOT IN (SELECT id FROM temp_hierarchy)',
            p_id_field, p_parent_field, v_level, p_table,
            p_parent_field, v_selected_ids,
            p_id_field
        );
        EXECUTE v_sql;
        GET DIAGNOSTICS v_count = ROW_COUNT;

        -- Обновляем список выбранных ID (теперь все накопленные)
        IF v_count > 0 THEN
            EXECUTE 'SELECT array_agg(id) FROM temp_hierarchy' INTO v_selected_ids;
        END IF;
    END LOOP;

    -- Возвращаем результат, отсортированный по уровню и ID
    RETURN QUERY
    SELECT th.id, th.parentid, th.level, th.data
    FROM temp_hierarchy th
    ORDER BY th.level, th.id;
END;
$function$

```
---

#### Function `hmac`
- **Сигнатура:** `hmac(text, text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.hmac(text, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_hmac$function$

```
---

#### Function `hmac`
- **Сигнатура:** `hmac(bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.hmac(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_hmac$function$

```
---

#### Function `pg_get_sequencedef`
- **Сигнатура:** `pg_get_sequencedef(p_sequencename text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pg_get_sequencedef(p_sequencename text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_result TEXT;
    v_start BIGINT;
    v_minimum BIGINT;
    v_maximum BIGINT;
    v_increment BIGINT;
    v_cycle BOOLEAN;
    v_cache BIGINT;
    v_last_value BIGINT;
BEGIN
    BEGIN
        EXECUTE 'SELECT start_value, minimum_value, maximum_value, increment_by, cycle, cache_size 
                 FROM ' || p_sequencename
        INTO v_start, v_minimum, v_maximum, v_increment, v_cycle, v_cache;
    EXCEPTION
        WHEN undefined_column THEN
            EXECUTE 'SELECT last_value, min_value, max_value, increment_by, is_cycled, cache_value 
                     FROM ' || p_sequencename
            INTO v_last_value, v_minimum, v_maximum, v_increment, v_cycle, v_cache;
            v_start := v_last_value;
    END;
    
    v_result := 'CREATE SEQUENCE ' || p_sequencename ||
                ' INCREMENT ' || v_increment ||
                ' MINVALUE ' || v_minimum ||
                ' MAXVALUE ' || v_maximum ||
                ' START ' || v_start ||
                ' CACHE ' || v_cache ||
                CASE WHEN v_cycle THEN ' CYCLE' ELSE '' END;
    
    RETURN v_result;
END;
$function$

```
---

#### Function `pg_get_tabledef`
- **Сигнатура:** `pg_get_tabledef(p_tablename text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pg_get_tabledef(p_tablename text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_result TEXT;
    v_schema_name TEXT;
    v_table_name TEXT;
    v_parts TEXT[];
BEGIN
    v_parts := string_to_array(replace(p_tablename, '"', ''), '.');
    v_schema_name := v_parts[1];
    v_table_name := v_parts[2];
    
    SELECT 'CREATE TABLE ' || p_tablename || E' (\n' ||
           string_agg(column_def, E',\n') ||
           E'\n)' INTO v_result
    FROM (
        SELECT 
            '    ' || quote_ident(column_name) || ' ' || 
            udt_name || 
            CASE 
                WHEN character_maximum_length IS NOT NULL 
                THEN '(' || character_maximum_length || ')'
                WHEN numeric_precision IS NOT NULL AND numeric_scale IS NOT NULL AND numeric_scale > 0
                THEN '(' || numeric_precision || ',' || numeric_scale || ')'
                WHEN numeric_precision IS NOT NULL AND (numeric_scale IS NULL OR numeric_scale = 0)
                THEN '(' || numeric_precision || ')'
                ELSE ''
            END ||
            CASE 
                WHEN is_nullable = 'NO' THEN ' NOT NULL'
                ELSE ''
            END ||
            CASE 
                WHEN column_default IS NOT NULL 
                THEN ' DEFAULT ' || column_default
                ELSE ''
            END as column_def
        FROM information_schema.columns
        WHERE table_schema = v_schema_name AND table_name = v_table_name
        ORDER BY ordinal_position
    ) t;
    
    RETURN v_result;
END;
$function$

```
---

#### Function `pgp_armor_headers`
- **Сигнатура:** `pgp_armor_headers(text, OUT key text, OUT value text)`
- **Возвращает:** SETOF record

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_armor_headers(text, OUT key text, OUT value text)
 RETURNS SETOF record
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_armor_headers$function$

```
---

#### Function `pgp_key_id`
- **Сигнатура:** `pgp_key_id(bytea)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_key_id(bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_key_id_w$function$

```
---

#### Function `pgp_pub_decrypt`
- **Сигнатура:** `pgp_pub_decrypt(bytea, bytea)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

```
---

#### Function `pgp_pub_decrypt`
- **Сигнатура:** `pgp_pub_decrypt(bytea, bytea, text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

```
---

#### Function `pgp_pub_decrypt`
- **Сигнатура:** `pgp_pub_decrypt(bytea, bytea, text, text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea, text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

```
---

#### Function `pgp_pub_decrypt_bytea`
- **Сигнатура:** `pgp_pub_decrypt_bytea(bytea, bytea, text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

```
---

#### Function `pgp_pub_decrypt_bytea`
- **Сигнатура:** `pgp_pub_decrypt_bytea(bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

```
---

#### Function `pgp_pub_decrypt_bytea`
- **Сигнатура:** `pgp_pub_decrypt_bytea(bytea, bytea)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

```
---

#### Function `pgp_pub_encrypt`
- **Сигнатура:** `pgp_pub_encrypt(text, bytea)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt(text, bytea)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_text$function$

```
---

#### Function `pgp_pub_encrypt`
- **Сигнатура:** `pgp_pub_encrypt(text, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt(text, bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_text$function$

```
---

#### Function `pgp_pub_encrypt_bytea`
- **Сигнатура:** `pgp_pub_encrypt_bytea(bytea, bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_bytea$function$

```
---

#### Function `pgp_pub_encrypt_bytea`
- **Сигнатура:** `pgp_pub_encrypt_bytea(bytea, bytea)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_bytea$function$

```
---

#### Function `pgp_sym_decrypt`
- **Сигнатура:** `pgp_sym_decrypt(bytea, text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt(bytea, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_text$function$

```
---

#### Function `pgp_sym_decrypt`
- **Сигнатура:** `pgp_sym_decrypt(bytea, text, text)`
- **Возвращает:** text

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt(bytea, text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_text$function$

```
---

#### Function `pgp_sym_decrypt_bytea`
- **Сигнатура:** `pgp_sym_decrypt_bytea(bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt_bytea(bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_bytea$function$

```
---

#### Function `pgp_sym_decrypt_bytea`
- **Сигнатура:** `pgp_sym_decrypt_bytea(bytea, text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt_bytea(bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_bytea$function$

```
---

#### Function `pgp_sym_encrypt`
- **Сигнатура:** `pgp_sym_encrypt(text, text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt(text, text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_text$function$

```
---

#### Function `pgp_sym_encrypt`
- **Сигнатура:** `pgp_sym_encrypt(text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt(text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_text$function$

```
---

#### Function `pgp_sym_encrypt_bytea`
- **Сигнатура:** `pgp_sym_encrypt_bytea(bytea, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt_bytea(bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_bytea$function$

```
---

#### Function `pgp_sym_encrypt_bytea`
- **Сигнатура:** `pgp_sym_encrypt_bytea(bytea, text, text)`
- **Возвращает:** bytea

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt_bytea(bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_bytea$function$

```
---

#### Function `sync_ext_comments`
- **Сигнатура:** `sync_ext_comments(p_entitytypeid integer DEFAULT NULL::integer)`
- **Возвращает:** void

**Определение:**
```sql
CREATE OR REPLACE FUNCTION public.sync_ext_comments(p_entitytypeid integer DEFAULT NULL::integer)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
DECLARE
    rec RECORD;
    v_comment TEXT;
BEGIN
    FOR rec IN (
        SELECT 
            f.entitytypeid,
            f.cfieldname,
            f.calias,
            e.calias AS entity_alias
        FROM meta.fields f
        JOIN meta.entitytypes e ON e.id = f.entitytypeid
        WHERE (p_entitytypeid IS NULL OR f.entitytypeid = p_entitytypeid)
    ) LOOP
        -- Формируем комментарий: бизнес-имя + доп. информация
        v_comment := format('Поле: %s (системное имя: %s)', rec.calias, rec.cfieldname);
        -- Добавляем информацию о ссылке, если есть
        -- (можно расширить)
        
        -- Выполняем COMMENT
        EXECUTE format('COMMENT ON COLUMN ext.%I.%I IS %L',
                       'ext_' || lower(rec.entity_alias),
                       rec.cfieldname,
                       v_comment);
    END LOOP;
END;
$function$

```
---
