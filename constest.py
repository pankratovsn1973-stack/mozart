import sys
from PySide6.QtWidgets import QApplication
from ide_core import goProject
from database import DatabaseService
from dialogs.class_edit_dialog import ClassEditDialog

app = QApplication(sys.argv)
goProject.db_host = "localhost"; goProject.db_port = "5432"
goProject.db_name = "mozart_erp"; goProject.db_user = "postgres"
goProject.db_pass = "SQLSerIra"
ok, msg = goProject.p_Connect()
if not ok: sys.exit(1)
goProject.set_db_service(DatabaseService())

dlg = ClassEditDialog(None, db=DatabaseService(), version_id=17, mode='edit')
print(f"\nЭлементов: {len(dlg.collection._elements)}")
for eid, elem in dlg.collection._elements.items():
    col = dlg.collection.get_property_collection(eid)
    print(f"  {eid} '{elem.get('calias')}' ({elem.get('cclass')}): "
          f"collection={'OK (' + str(len(col)) + ')' if col else 'None'}")

# Симулируем клик по 19 (Ref_TextEdit)
dlg.collection.select_element(19, additive=False)
dlg.update_properties_panel()
print(f"\nПосле клика по 19: строк в инспекторе = {dlg.properties_table.rowCount()}")

if goProject.db_conn:
    goProject.db_conn.close()