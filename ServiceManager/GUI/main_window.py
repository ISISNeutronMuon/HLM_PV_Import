from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import os
from ServiceManager.GUI.about import UIAbout


class UIMainWindow(QMainWindow):
    def __init__(self):
        super(UIMainWindow, self).__init__()
        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts', 'MainWindow.ui')
        uic.loadUi(ui_file_path, self)

        self.button = self.findChild(QPushButton, 'pushButton')
        self.button.clicked.connect(self.pushButtonPressed)

        self.about = self.findChild(QAction, 'actionAbout')
        self.about.triggered.connect(self.show_about)

    def show_about(self):
        self.about = UIAbout()
        self.about.show()

    def pushButtonPressed(self):
        print('printButtonPressed')
