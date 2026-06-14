# /home/sergey/Documents/configurate/widgets/form_designer_old/form_widget.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont


class FormWidget(QWidget):
    """Виджет формы, который будет встраиваться в сцену"""

    size_changed = Signal(int, int)
    close_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Стиль с тенью и 3D-эффектом
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f8f8, stop:0.5 #ebebeb, stop:1 #d6d6d6);
                border: 1px solid #b0b0b0;
            }
        """)

        # Основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Заголовок
        title_bar = QWidget(self)
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5090d0, stop:1 #3060a0);
                border: none;
            }
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(5)

        self.title_label = QLabel("Форма")
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        self.title_label.setFont(QFont("Arial", 9, QFont.Bold))
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        # Кнопки окна
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setFixedSize(16, 16)
        self.btn_minimize.setStyleSheet("""
            QPushButton {
                background-color: #d0d0d0;
                border: 1px solid #a0a0a0;
                border-radius: 2px;
                color: #404040;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        title_layout.addWidget(self.btn_minimize)

        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setFixedSize(16, 16)
        self.btn_maximize.setStyleSheet("""
            QPushButton {
                background-color: #d0d0d0;
                border: 1px solid #a0a0a0;
                border-radius: 2px;
                color: #404040;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.btn_maximize.clicked.connect(self.maximize_clicked.emit)
        title_layout.addWidget(self.btn_maximize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(16, 16)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #d05050;
                border: 1px solid #a03030;
                border-radius: 2px;
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e06060;
            }
        """)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        title_layout.addWidget(self.btn_close)

        layout.addWidget(title_bar)

        # Контентная область (сюда будут добавляться контролы)
        self.content_area = QWidget(self)
        self.content_area.setStyleSheet("background-color: #f0f0f0;")
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.content_area, 1)

        # Для перемещения формы
        self._drag_pos = None
        self._title_bar = title_bar

    def set_form_title(self, title):
        self.title_label.setText(title)

    def get_content_area(self):
        """Возвращает контентную область для добавления контролов"""
        return self.content_area

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Проверяем, что клик по заголовку
            pos = event.pos()
            if pos.y() <= self._title_bar.height():
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.size_changed.emit(self.width(), self.height())