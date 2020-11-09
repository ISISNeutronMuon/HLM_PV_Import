from PyQt5.QtCore import QUrl
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import os


class UIAbout(QDialog):
    def __init__(self):
        super(UIAbout, self).__init__()
        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts', 'about.ui')
        uic.loadUi(ui_file_path, self)

        self.ok_button = self.findChild(QPushButton, 'ok')
        self.ok_button.clicked.connect(self.ok_pressed)

        self.logo_button = self.findChild(QPushButton, 'logo')
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'isis-logo.png')
        self.logo_button.setIcon(QIcon(logo_path))
        self.logo_button.clicked.connect(self.logo_pressed)

    def ok_pressed(self):
        self.close()

    @staticmethod
    def logo_pressed():
        url = QUrl("https://www.isis.stfc.ac.uk/Pages/home.aspx")
        QDesktopServices.openUrl(url)
