from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton
from PyQt5 import uic
from ServiceManager.constants import VER, B_DATE, about_ui, about_logo_path


class UIAbout(QDialog):
    def __init__(self):
        super(UIAbout, self).__init__()
        uic.loadUi(uifile=about_ui, baseinstance=self)

        # Remove the "?" QWhatsThis button from the About dialog
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        # Set the version and build date
        self.version = self.findChild(QLabel, 'version')
        temp = self.version.text()
        temp += VER
        self.version.setText(temp)
        self.bDate = self.findChild(QLabel, 'build_date')
        temp = self.bDate.text()
        temp += B_DATE
        self.bDate.setText(temp)

        self.ok_button = self.findChild(QPushButton, 'ok')
        self.ok_button.clicked.connect(self.ok_pressed)

        self.logo_button = self.findChild(QPushButton, 'logo')
        self.logo_button.setIcon(QIcon(about_logo_path))
        self.logo_button.clicked.connect(self.logo_pressed)

    def ok_pressed(self):
        self.close()

    @staticmethod
    def logo_pressed():
        url = QUrl("https://www.isis.stfc.ac.uk/Pages/home.aspx")
        # noinspection PyArgumentList
        QDesktopServices.openUrl(url)
