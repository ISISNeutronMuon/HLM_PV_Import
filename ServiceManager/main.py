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
        self.main_window = None

        # Set-up manager settings
        Settings.init_manager_settings()

        # Look for the service path in manager settings
        service_settings_path = Settings.Manager.get_service_path()

        # If service path is found, initialize service settings and open main window
        # Otherwise, open Service Path dialog and ask for the service directory path.
        # Once a path has been provided and service settings initialized from the dialog, close it and open main window.
        if service_settings_path:
            Settings.init_service_settings(service_settings_path)
            self.show_main_window()
        else:
            self.window = UIServicePathDialog()
            self.window.show()
            self.window.custom_signals.showMainWindow.connect(self.show_main_window)

    def show_main_window(self):
        if self.main_window is None:
            self.main_window = UIMainWindow()
        self.main_window.show()

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
