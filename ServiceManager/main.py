from PyQt5.QtWidgets import *
from ServiceManager.GUI.main_window import UIMainWindow

app = QApplication([])

window = UIMainWindow()
window.show()

app.exec_()
