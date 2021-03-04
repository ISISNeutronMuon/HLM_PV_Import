from multiprocessing import freeze_support
import sys
import traceback

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QErrorMessage

from ServiceManager.GUI.main_window import UIMainWindow
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.constants import icon_path
from ServiceManager.logger import logger
from ServiceManager.settings import Settings


class App:
    def __init__(self):
        self.app = QApplication([])
        self.app.setWindowIcon(QIcon(icon_path))

        self.window = None
        self.main_window = None

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
            self.window.custom_signals.serviceUpdated.connect(self.show_main_window)

    def show_main_window(self):
        if self.main_window is None:
            self.main_window = UIMainWindow()
        self.main_window.show()

    @staticmethod
    def raise_error():
        assert False


def excepthook(exc_type, exc_value, exc_tb):
    traceback_ = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    err_msg = f'An unhandled exception has occurred:\n {traceback_}'
    logger.error(err_msg)
    err_msg = err_msg.replace('\n', '<br>')
    error_dialog = QErrorMessage()
    error_dialog.setWindowTitle('HLM PV Import - Error')
    error_dialog.resize(600, 300)
    error_dialog.setFont(QFont('Lucida Console', 9))
    error_dialog.showMessage(err_msg)
    error_dialog.exec()
    # QApplication.quit()  # or QtWidgets.QApplication.exit(0)


def main():
    # Pyinstaller fix
    freeze_support()

    sys.excepthook = excepthook
    print("Starting application.")
    e = App()
    ret = e.app.exec_()
    print("Event loop exited.")
    e.app.quit()
    sys.exit(ret)


if __name__ == '__main__':
    main()
