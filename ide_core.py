


# ide_core.py
import psycopg2
import json
import os


class GoProject:
    def __init__(self):
        # --- Закладка 1: БАЗА ДАННЫХ (Layer 1) ---
        self.db_host = "localhost"
        self.db_port = "5432"
        self.db_name = "mozart_erp"
        self.db_user = "postgres"
        self.db_pass = ""
        self.db_conn = None  # Активное соединение psycopg2
        self.current_user_id = None  # ID текущего пользователя (конфигуратора)

        # --- Закладка 2: СРЕДНИЙ СЛОЙ (Layer 2) ---
        self.l2_path = os.getcwd() + "/layer2_server"
        self.l2_port = 8000
        self.l2_process = None

        # --- Закладка 3: КЛИЕНТ (Layer 3) ---
        self.l3_path = os.getcwd() + "/layer3_client"
        self.l3_starter = "starter.py"
        self.l3_process = None

    def p_Connect(self):
        """
        Установка физического соединения с PostgreSQL.
        Проверяет, что пользователь имеет роль конфигуратора.
        """
        try:
            # Закрываем старое соединение, если оно было
            if self.db_conn:
                self.db_conn.close()

            self.db_conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass,
                connect_timeout=5
            )
            self.db_conn.autocommit = True

            # Проверяем, является ли текущий пользователь конфигуратором
            with self.db_conn.cursor() as cur:
                # Сначала получаем ID пользователя по логину
                cur.execute("SELECT id FROM auth.users WHERE clogin = %s", (self.db_user,))
                row = cur.fetchone()
                if not row:
                    self.db_conn.close()
                    self.db_conn = None
                    return False, f"Пользователь {self.db_user} не найден в системе."

                user_id = row[0]

                # Проверяем наличие роли с типом 'CONFIG'
                cur.execute("""
                    SELECT u.id 
                    FROM auth.users u
                    JOIN auth.userrolecontext urc ON u.id = urc.userid
                    JOIN auth.roles r ON urc.roleid = r.id
                    JOIN auth.role_types rt ON r.role_type_id = rt.id
                    WHERE u.id = %s AND rt.calias = 'CONFIG'
                """, (user_id,))
                if not cur.fetchone():
                    self.db_conn.close()
                    self.db_conn = None
                    return False, "У вас нет прав конфигуратора. Доступ запрещён."

            self.current_user_id = user_id
            return True, "Соединение со Слоном установлено успешно. Добро пожаловать, конфигуратор!"
        except Exception as e:
            self.db_conn = None
            return False, f"Ошибка подключения: {str(e)}"

    def f_Execute(self, sql, params=None):
        """
        Выполнение SQL-запроса (SELECT).
        Возвращает коллекцию строк (loResult). [0.3]
        """
        if not self.db_conn:
            return []

        try:
            with self.db_conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:  # Если запрос возвращает данные (SELECT)
                    return cur.fetchall()
                return []
        except Exception as e:
            print(f"SQL Error: {e}")
            return []

    def p_SaveProject(self, file_path):
        """ Сохранение манифеста проекта в .mzt файл (JSON) """
        data = {
            "db": {
                "host": self.db_host, "port": self.db_port,
                "name": self.db_name, "user": self.db_user, "pass": self.db_pass
            },
            "l2": {"path": self.l2_path, "port": self.l2_port},
            "l3": {"path": self.l3_path, "starter": self.l3_starter}
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def p_LoadProject(self, file_path):
        """ Загрузка параметров проекта из .mzt файла """
        if not os.path.exists(file_path):
            return False, "Файл проекта не найден."

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.db_host = data['db'].get('host', 'localhost')
            self.db_port = data['db'].get('port', '5432')
            self.db_name = data['db'].get('name', '')
            self.db_user = data['db'].get('user', 'postgres')
            self.db_pass = data['db'].get('pass', '')

            self.l2_path = data['l2'].get('path', '')
            self.l2_port = data['l2'].get('port', 8000)

            self.l3_path = data['l3'].get('path', '')
            self.l3_starter = data['l3'].get('starter', 'starter.py')

            return True, "Проект загружен."
        except Exception as e:
            return False, f"Ошибка чтения файла: {str(e)}"


# Создаем единственный экземпляр объекта управления проектом
goProject = GoProject()