from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QLabel, QListWidget
from PyQt5 import uic
import os
from ServiceManager.GUI.about import UIAbout
from ServiceManager.GUI.db_settings import UIDBSettings
from ServiceManager.GUI.general_settings import UIGeneralSettings
from ServiceManager.utilities import is_admin


class UIMainWindow(QMainWindow):
    def __init__(self):
        super(UIMainWindow, self).__init__()

        # External windows
        self.about_w = None
        self.db_settings_w = None
        self.general_settings_w = None

        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts', 'MainWindow.ui')
        uic.loadUi(ui_file_path, self)

        if is_admin():
            self.setWindowTitle(self.windowTitle() + ' (Administrator)')

        self.button = self.findChild(QPushButton, 'pushButton')
        self.button.clicked.connect(self.pushButtonPressed)

        self.version = self.findChild(QLabel, '')

        # Menu actions
        self.about_action = self.findChild(QAction, 'actionAbout')
        self.about_action.triggered.connect(self.trigger_about)
        self.db_settings_action = self.findChild(QAction, 'actionDB_Connection')
        self.db_settings_action.triggered.connect(self.trigger_db_settings)
        self.general_settings_action = self.findChild(QAction, 'actionGeneral')
        self.general_settings_action.triggered.connect(self.trigger_general_settings)

        self.pv_list = self.findChild(QListWidget, 'listWidget')

    def trigger_about(self):
        if self.about_w is None:
            self.about_w = UIAbout()
        self.about_w.show()
        self.about_w.activateWindow()

    def trigger_db_settings(self):
        if self.db_settings_w is None:
            self.db_settings_w = UIDBSettings()
        self.db_settings_w.show()
        self.db_settings_w.activateWindow()

    def trigger_general_settings(self):
        if self.general_settings_w is None:
            self.general_settings_w = UIGeneralSettings()
        self.general_settings_w.show()
        self.general_settings_w.activateWindow()


    def pushButtonPressed(self):
        print('printButtonPressed')
        self.pv_list.addItem('wow')
