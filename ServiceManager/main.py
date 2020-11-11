import traceback
import sys
from PyQt5.QtWidgets import *
from ServiceManager.GUI.main_window import UIMainWindow


class DebugApp:
    app = QApplication([])
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
sys.exit(ret)
