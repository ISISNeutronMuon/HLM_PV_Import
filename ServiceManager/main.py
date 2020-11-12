import traceback
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ServiceManager.GUI.main_window import UIMainWindow
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.settings import icon_path, Settings


class App:
    def __init__(self):
        self.app = QApplication([])
        self.app.setWindowIcon(QIcon(icon_path))

        self.window = None

        # Set-up service path
        Settings.init_manager_settings()
        service_settings_path = Settings.Manager.get_service_path()
        if not service_settings_path:

            self.window = UIServicePathDialog()
            self.window.show()
            self.window.custom_signals.showMainWindow.connect(self.show_main_window)

        else:
            self.show_main_window()

    def show_main_window(self):
        service_settings_path = Settings.Manager.get_service_path()
        Settings.init_service_settings(service_settings_path)

        self.window = UIMainWindow()
        self.window.show()

    @staticmethod
    def raise_error():
        assert False


def except_hook(exc_type, exc_value, exc_tb):
    traceback_ = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print('Error caught:')
    print("Error message:\n", traceback_)
    QApplication.quit()  # or QtWidgets.QApplication.exit(0)



sys.excepthook = except_hook
e = App()
ret = e.app.exec_()
print("Event loop exited.")
e.app.quit()
sys.exit(ret)
