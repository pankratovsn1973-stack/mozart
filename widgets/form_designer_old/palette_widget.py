# widgets/form_designer_old/palette_widget.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QFont


class DraggableLabel(QLabel):
    """Метка для перетаскивания контрола"""

    def __init__(self, control_type, text, parent=None):
        super().__init__(text, parent)
        self.control_type = control_type
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(32)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.control_type)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)


class PaletteWidget(QWidget):
    """Палитра контролов для перетаскивания"""

    CONTROLS = [
        ('textbox', '📝 Текстовое поле'),
        ('numberbox', '#️⃣ Числовое поле'),
        ('datebox', '📅 Дата'),
        ('checkbox', '☑ Флажок'),
        ('optiongroup', '🔘 Группа радиокнопок'),
        ('memo', '📄 Многострочный текст'),
        ('reference', '🔗 Ссылка'),
        ('button', '🔘 Кнопка'),
        ('label', '🏷 Метка'),
        ('group', '🗋 Группа'),
        ('grid', '▦ Таблица'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Контролы")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(5)

        for ctype, text in self.CONTROLS:
            btn = DraggableLabel(ctype, text)
            content_layout.addWidget(btn)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)