# /home/sergey/Documents/configurate/widgets/form_designer_old/designer_data_model.py
"""
Модуль: Локальная In-Memory СУБД для изоляции ERP-классов от графических масок.

Роль в архитектуре Mozart ERP:
    - Хранение свойств контролов и формы во время редактирования.
    - Поддержка дельта-изменений (буфер изменений перед коммитом).
    - Реализация двухфазной инициализации формы (перенос свойств с "0" на реальный ID).
    - Единый источник истины для панели свойств и инспектора.

Ключевые зависимости:
    - FormObjectsRegistry - использует ID из реестра как ключи.
    - SceneLoaderMixin - вызывает move_values() при загрузке данных из БД.
    - PropertyEditor - читает значения через get_value().
"""


class DesignerDataModel:
    """
    Синглтон-модель данных дизайнера форм.

    Свойства:
        - properties_instances: dict[(str, str), Any] - Основные свойства объектов.
          Ключ = кортеж (control_id, property_name).
        - properties_delta: dict[(str, str), Any] - Буфер несохраненных изменений.
        - metadata: dict[str, dict] - Описание типов и меток свойств.

    Основные методы:
        - set_value(): Установка свойства (сразу или в буфер).
        - get_value(): Чтение свойства (приоритет у буфера).
        - move_values(): Перенос всех свойств с одного ID на другой (для фазы 2).
        - commit_delta(): Применение буфера к основным данным.
        - clear(): Полная очистка модели.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DesignerDataModel, cls).__new__(cls, *args, **kwargs)
            cls._instance.properties_instances = {}
            cls._instance.properties_delta = {}
            cls._instance._init_metadata()
        return cls._instance

    def _init_metadata(self):
        """Реестр метаданных low-code свойств форм и контролов ERP."""
        self.metadata = {
            "control_id": {"label": "Идентификатор ID", "type": "str"},
            "control_type": {"label": "Класс контрола", "type": "str"},
            "form_alias": {"label": "Алиас контрола", "type": "str"},
            "title": {"label": "Заголовок окна", "type": "str"},
            "x": {"label": "Параметр X", "type": "int"},
            "y": {"label": "Параметр Y", "type": "int"},
            "width": {"label": "Параметр WIDTH", "type": "int"},
            "height": {"label": "Параметр HEIGHT", "type": "int"},
            "label": {"label": "Текст надписи", "type": "str"},
            "binding_field": {"label": "Поле СУБД привязки", "type": "str"},
            "entity_alias": {"label": "Сущность-источник", "type": "str"},
            "display_field": {"label": "Отображаемое поле", "type": "str"},
            "selector_form": {"label": "Форма выбора", "type": "str"},
            "is_required": {"label": "Обязательное", "type": "bool"},
            "is_readonly": {"label": "Только чтение", "type": "bool"}
        }

    def get_metadata(self, prop_name):
        """
        Возвращает описание свойства по имени.

        Args:
            prop_name: str - Имя свойства

        Returns:
            dict - Метаданные свойства (label, type)
        """
        return self.metadata.get(prop_name, {"label": str(prop_name), "type": "str"})

    # ==================== ПУНКТ 3: ПЕРЕНОС СВОЙСТВ ====================
    def move_values(self, old_key: str, new_key: str):
        """
        Атомарно переносит ВСЕ свойства с old_key на new_key.

        Используется при двухфазной инициализации формы:
        Фаза 1: форма регистрируется с ID="0"
        Фаза 2: при загрузке из БД ID меняется на реальный (например, "841")
        Этот метод переносит width, height, title и др. с "0" на "841".

        Args:
            old_key: str - Старый ключ (например, "0")
            new_key: str - Новый ключ (например, "841")
        """
        old_key = str(old_key).strip()
        new_key = str(new_key).strip()

        if old_key == new_key:
            return

        moved_count = 0

        # Переносим из основных экземпляров
        keys_to_delete = []
        for (cid, prop_name), value in list(self.properties_instances.items()):
            if cid == old_key:
                self.properties_instances[(new_key, prop_name)] = value
                keys_to_delete.append((cid, prop_name))
                moved_count += 1

        for key in keys_to_delete:
            del self.properties_instances[key]

        # Переносим из буфера дельта-изменений
        delta_keys_to_delete = []
        for (cid, prop_name), value in list(self.properties_delta.items()):
            if cid == old_key:
                self.properties_delta[(new_key, prop_name)] = value
                delta_keys_to_delete.append((cid, prop_name))

        for key in delta_keys_to_delete:
            del self.properties_delta[key]

        print(f"[DataModel] Перенесено {moved_count} свойств: '{old_key}' -> '{new_key}'")

    def set_value(self, control_id, prop_name, value, is_delta=False):
        """
        Устанавливает значение свойства.

        Args:
            control_id: str - ID контрола
            prop_name: str - Имя свойства
            value: Any - Значение (сохраняется в оригинальном типе)
            is_delta: bool - Если True, записать в буфер изменений
        """
        cid = str(control_id).strip()

        # ✅ СОХРАНЯЕМ ОРИГИНАЛЬНЫЙ ТИП (не приводим к str)
        target = self.properties_delta if is_delta else self.properties_instances
        target[(cid, prop_name)] = value

    def get_value(self, control_id, prop_name):
        """
        Получает значение свойства (приоритет у буфера дельта-изменений).

        Args:
            control_id: str - ID контрола
            prop_name: str - Имя свойства

        Returns:
            Any - Значение свойства или пустая строка
        """
        cid = str(control_id).strip()

        # Сначала проверяем буфер изменений
        if (cid, prop_name) in self.properties_delta:
            return self.properties_delta[(cid, prop_name)]

        # Затем основные данные
        return self.properties_instances.get((cid, prop_name), "")

    def commit_delta(self):
        """
        Применяет все изменения из буфера к основным данным.
        Вызывается после успешного сохранения формы в БД.
        """
        for (cid, prop_name), val in self.properties_delta.items():
            self.properties_instances[(cid, prop_name)] = val
        self.properties_delta.clear()
        print("[DataModel] Дельта-изменения применены.")

    def clear(self):
        """
        Полная очистка всех данных модели.
        Вызывается при открытии новой формы или закрытии дизайнера.
        """
        self.properties_instances.clear()
        self.properties_delta.clear()
        print("[DataModel] Модель данных полностью очищена.")