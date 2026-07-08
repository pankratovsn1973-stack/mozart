# Полный путь: dialogs/signals_dialog.py
"""
Диалог управления сигналами класса.
Слева отображаются все возможные сигналы объекта (нередактируемые),
справа - QComboBox со списком методов для привязки.
При выборе метода в комбобоксе автоматически сохраняется связь.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGridLayout, QScrollArea,
    QWidget, QMessageBox
)
from PySide6.QtCore import Qt

from database import DatabaseService
from services.class_data_service import ClassDataService
from lang.local_translator import LocalTranslator


class SignalsDialog(QDialog):
    """
    Диалог управления сигналами класса.

    Свойства:
        - db: DatabaseService - экземпляр БД
        - class_service: ClassDataService - сервис классов
        - translator: LocalTranslator - переводы
        - version_id: int - ID версии класса
        - element_id: int - ID элемента в коллекции
        - signal_widgets: dict - виджеты сигналов {signal_id: (label, combo)}

    Методы:
        - setup_ui() - настройка интерфейса
        - load_signals() - загрузка сигналов
        - load_methods() - загрузка методов
        - assign_method(signal_id, method_id) - привязка метода
        - on_combo_changed() - обработка изменения комбобокса
    """

    def __init__(self, parent=None, db: DatabaseService = None,
                 version_id: int = -1, element_id: int = -1):
        super().__init__(parent)
        self.db = db
        self.class_service = ClassDataService(db) if db else None
        self.translator = LocalTranslator()
        self.version_id = version_id
        self.element_id = element_id
        self.signal_widgets = {}

        self.setWindowTitle(self.translator.tr('btn_signals'))
        self.resize(600, 500)

        self.setup_ui()
        self.load_signals()
        self.load_methods()

    def setup_ui(self):
        """Настройка интерфейса диалога."""
        layout = QVBoxLayout(self)

        # Заголовок
        layout.addWidget(QLabel(self.translator.tr('field_signals_list') + ":"))

        # Прокручиваемая область для сигналов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.signals_widget = QWidget()
        self.signals_layout = QGridLayout(self.signals_widget)
        self.signals_layout.setColumnStretch(0, 1)
        self.signals_layout.setColumnStretch(1, 2)

        # Заголовки таблицы
        self.signals_layout.addWidget(QLabel(self.translator.tr('field_signal_name')), 0, 0)
        self.signals_layout.addWidget(QLabel(self.translator.tr('field_method')), 0, 1)

        scroll.setWidget(self.signals_widget)
        layout.addWidget(scroll)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton(self.translator.tr('btn_close'))
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def load_signals(self):
        """Загрузка сигналов класса."""
        if not self.class_service or self.version_id <= 0:
            return

        # Очищаем старые виджеты
        for signal_id, (label, combo) in self.signal_widgets.items():
            self.signals_layout.removeWidget(label)
            self.signals_layout.removeWidget(combo)
            label.deleteLater()
            combo.deleteLater()
        self.signal_widgets.clear()

        # Загружаем сигналы
        signals = self.class_service.get_class_signals(self.version_id)

        row = 1  # Начинаем с 1 (после заголовков)
        for signal in signals:
            signal_id = signal.get('id')
            signal_name = signal.get('c_signal', '')
            method_id = signal.get('method_id')

            # Метка с именем сигнала
            label = QLabel(signal_name)
            label.setStyleSheet("font-weight: bold; color: #333;")

            # ComboBox с методами
            combo = QComboBox()
            combo.addItem("-- " + self.translator.tr('no_method') + " --", None)
            combo.setProperty('signal_id', signal_id)
            combo.currentIndexChanged.connect(
                lambda idx, sid=signal_id, cb=combo: self.on_combo_changed(sid, cb)
            )

            # Сохраняем виджеты
            self.signal_widgets[signal_id] = (label, combo)

            # Добавляем в сетку
            self.signals_layout.addWidget(label, row, 0)
            self.signals_layout.addWidget(combo, row, 1)
            row += 1

        # Обновляем выбор методов
        self.load_methods()

    def load_methods(self):
        """Загрузка методов в ComboBox."""
        if not self.class_service:
            return

        # Получаем все методы
        methods = self.class_service.get_all_methods()

        # Обновляем каждый ComboBox
        for signal_id, (label, combo) in self.signal_widgets.items():
            # Сохраняем текущий выбор
            current_data = combo.currentData()

            # Очищаем ComboBox
            combo.clear()
            combo.addItem("-- " + self.translator.tr('no_method') + " --", None)

            # Добавляем методы
            for method in methods:
                combo.addItem(method.get('c_name', ''), method.get('id'))

            # Восстанавливаем выбор
            if current_data is not None:
                idx = combo.findData(current_data)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

    def assign_method(self, signal_id: int, method_id: int):
        """
        Привязка метода к сигналу.

        Вход:
            signal_id: int - ID сигнала
            method_id: int - ID метода (None для отвязки)

        Выход: None
        """
        if not self.class_service:
            return

        try:
            self.class_service.assign_signal_method(signal_id, method_id)
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translator.tr('error'),
                f"Ошибка привязки метода: {str(e)}"
            )

    def on_combo_changed(self, signal_id: int, combo: QComboBox):
        """
        Обработка изменения ComboBox.

        Вход:
            signal_id: int - ID сигнала
            combo: QComboBox - измененный ComboBox

        Выход: None
        """
        method_id = combo.currentData()
        self.assign_method(signal_id, method_id)