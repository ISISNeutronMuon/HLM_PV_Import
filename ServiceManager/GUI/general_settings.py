from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from ServiceManager.constants import general_settings_ui


class UIGeneralSettings(QDialog):
    def __init__(self):
        super(UIGeneralSettings, self).__init__()
        uic.loadUi(uifile=general_settings_ui, baseinstance=self)
