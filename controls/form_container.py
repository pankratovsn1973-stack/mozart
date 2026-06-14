# -*- coding: utf-8 -*-
# /home/sergey/Documents/configurate/controls/form_container.py

from PySide6.QtWidgets import QMdiArea, QMdiSubWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Signal


class FormContainer(QWidget):
    form_opened = Signal(object)
    form_closed = Signal(object)
    form_activated = Signal(object)

    def __init__(self, parent=None, mode='mdi'):
        super().__init__(parent)
        self.mode = mode
        self._forms = {}
        self._active_form = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if self.mode == 'mdi':
            self.mdi_area = QMdiArea()
            layout.addWidget(self.mdi_area)
        else:
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabsClosable(True)
            self.tab_widget.tabCloseRequested.connect(self.close_tab)
            layout.addWidget(self.tab_widget)

    def add_form(self, form, title=None):
        if not title:
            title = form.title or "Форма"
        if self.mode == 'mdi':
            sub = QMdiSubWindow()
            sub.setWidget(form)
            sub.setWindowTitle(title)
            self.mdi_area.addSubWindow(sub)
            sub.show()
            self._forms[id(form)] = form
        else:
            index = self.tab_widget.addTab(form, title)
            self.tab_widget.setCurrentIndex(index)
            self._forms[title] = form
        form.form_closed.connect(lambda: self._on_form_closed(form))
        self.form_opened.emit(form)

    def remove_form(self, form):
        if self.mode == 'mdi':
            for sub in self.mdi_area.subWindowList():
                if sub.widget() == form:
                    sub.close()
                    break
        else:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == form:
                    self.tab_widget.removeTab(i)
                    break
        self._on_form_closed(form)

    def close_tab(self, index):
        form = self.tab_widget.widget(index)
        if form and form.on_close():
            self.tab_widget.removeTab(index)
            form.deleteLater()
            self._on_form_closed(form)

    def _on_form_closed(self, form):
        if self.mode == 'mdi':
            self._forms.pop(id(form), None)
        else:
            for title, f in list(self._forms.items()):
                if f == form:
                    self._forms.pop(title, None)
                    break
        self.form_closed.emit(form)

    def get_active_form(self):
        if self.mode == 'mdi':
            sub = self.mdi_area.activeSubWindow()
            if sub:
                return sub.widget()
        else:
            index = self.tab_widget.currentIndex()
            if index >= 0:
                return self.tab_widget.widget(index)
        return None