from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QDialogButtonBox, QFileDialog, QMessageBox, \
    QApplication
from PyQt5 import uic
from ServiceManager.settings import service_path_dlg_ui, Settings, SERVICE_SETTINGS_FILE_NAME
import os


class CustomSignals(QObject):
    showMainWindow = pyqtSignal()


class UIServicePathDialog(QDialog):
    def __init__(self):
        super(UIServicePathDialog, self).__init__()
        uic.loadUi(uifile=service_path_dlg_ui, baseinstance=self)

        # Custom signals the App can pick up
        self.custom_signals = CustomSignals()

        # Get widgets
        self.service_path = self.findChild(QLineEdit, 'servicePath')
        self.service_browse = self.findChild(QPushButton, 'browsePath')
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.message_lbl = self.findChild(QLabel, 'message')

        # Assign slots to signals and events
        self.service_path.mouseDoubleClickEvent = lambda _: self.service_path.selectAll()
        self.service_path.textChanged.connect(self.clear_message)
        self.service_browse.clicked.connect(self.browse_file_dialog)
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)
        self.help_btn = self.button_box.button(QDialogButtonBox.Help)
        self.help_btn.clicked.connect(self.on_help)

        self.update_fields()

    def update_fields(self):
        curr_path = Settings.Manager.get_service_path()
        if curr_path:
            self.service_path.setText(curr_path)

    def on_accepted(self):
        path = self.service_path.text()
        if os.path.exists(path):
            settings_file = os.path.join(path, SERVICE_SETTINGS_FILE_NAME)
            if os.path.isfile(settings_file):  # setting file exists
                Settings.Manager.set_service_path(path)
                service_settings_path = Settings.Manager.get_service_path()
                Settings.init_service_settings(service_settings_path)
                self.custom_signals.showMainWindow.emit()  # emit custom signal to show main window
                self.close()
            else:  # ask user if they want to create new settings file
                settings_not_found_msg = f'Service settings file "{SERVICE_SETTINGS_FILE_NAME}" ' \
                                         f'not found in "{path}". Create new blank settings file?'
                reply = QMessageBox.warning(self, 'HLM PV Import',
                                            settings_not_found_msg, QMessageBox.Yes, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    Settings.Manager.set_service_path(path)
                    service_settings_path = Settings.Manager.get_service_path()
                    Settings.init_service_settings(service_settings_path)
                    self.custom_signals.showMainWindow.emit()  # emit custom signal to show main window
                    self.close()
        else:
            self.message_lbl.setText('Path does not exist, please verify path is correct.')

    def on_rejected(self):
        self.close()

    def on_help(self):
        self.close()

    def browse_file_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.service_path.setText(dir_path)

    def clear_message(self):
        self.message_lbl.clear()

    def showEvent(self, event: QShowEvent):
        self.update_fields()
