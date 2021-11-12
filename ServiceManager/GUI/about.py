from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from ServiceManager.constants import VER, B_DATE, ISIS_URL, about_ui, about_logo_path


class UIAbout(QDialog):
    def __init__(self):
        super(UIAbout, self).__init__()
        uic.loadUi(uifile=about_ui, baseinstance=self)
        self.setModal(True)

        # Remove the "?" QWhatsThis button from the About dialog
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        # Set the version and build date
        self.version.setText(self.version.text() + VER)
        self.build_date.setText(self.build_date.text() + B_DATE)

        self.ok.clicked.connect(self.close)
        self.logo.setIcon(QIcon(about_logo_path))
        self.logo.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(ISIS_URL))
        )
        self.logo.setToolTip(ISIS_URL)
