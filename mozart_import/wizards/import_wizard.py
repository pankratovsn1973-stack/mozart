# mozart_import/wizards/import_wizard.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWizard
from PySide6.QtCore import QEvent
from lang.local_translator import LocalTranslator
from database import DatabaseService
from .source_page import SourcePage
from .schema_page import SchemaPage
from .relation_page import RelationPage
from .mapping_detail_page import MappingDetailPage
from .execute_page import ExecutePage


class ImportWizard(QWizard):
    def __init__(self, db: DatabaseService, parent=None):
        super().__init__(parent)
        self.db = db
        self.translator = LocalTranslator()
        self.setWindowTitle(self.translator.tr('wizard_title'))
        self.resize(1200, 800)
        self.setWizardStyle(QWizard.ModernStyle)

        # Данные, передаваемые между страницами
        self.connector = None
        self.schema = None
        self.source_nodes = []
        self.links = []
        self.pending_entities = []
        self.import_links = []

        # Страницы
        self.source_page = SourcePage(self)
        self.schema_page = SchemaPage(self)
        self.relation_page = RelationPage(self)
        self.detail_page = MappingDetailPage(self)
        self.execute_page = ExecutePage(self)

        self.addPage(self.source_page)
        self.addPage(self.schema_page)
        self.addPage(self.relation_page)
        self.addPage(self.detail_page)
        self.addPage(self.execute_page)

        self.setButtonText(QWizard.FinishButton, self.translator.tr('wizard_finish'))
        self.setButtonText(QWizard.CancelButton, self.translator.tr('btn_cancel'))

    def retranslate_ui(self):
        self.setWindowTitle(self.translator.tr('wizard_title'))
        self.setButtonText(QWizard.FinishButton, self.translator.tr('wizard_finish'))
        self.setButtonText(QWizard.CancelButton, self.translator.tr('btn_cancel'))
        self.source_page.retranslate_ui()
        self.schema_page.retranslate_ui()
        self.relation_page.retranslate_ui()
        self.detail_page.retranslate_ui()
        self.execute_page.retranslate_ui()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)