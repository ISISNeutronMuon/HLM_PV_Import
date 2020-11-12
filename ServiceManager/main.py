import traceback
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ServiceManager.GUI.main_window import UIMainWindow
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.settings import icon_path, Settings


class DebugApp:
    app = QApplication([])
    app.setWindowIcon(QIcon(icon_path))

    # Set-up service path
    Settings.init_manager_settings()
    service_path = Settings.Manager.get_service_path()
    if not service_path:
        window = UIServicePathDialog()
    else:
        window = UIMainWindow()

    window.show()

    @staticmethod
    def raise_error():
        assert False


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    QApplication.quit()
    # or QtWidgets.QApplication.exit(0)


sys.excepthook = excepthook
e = DebugApp()
ret = e.app.exec_()
print("event loop exited")
e.app.quit()
sys.exit(ret)
