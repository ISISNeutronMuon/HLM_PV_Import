from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton
from PyQt5 import uic
from ServiceManager.settings import service_path_dlg_ui


class UIServicePathDialog(QDialog):
    def __init__(self):
        super(UIServicePathDialog, self).__init__()
        uic.loadUi(uifile=service_path_dlg_ui, baseinstance=self)
