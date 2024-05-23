import os

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QShowEvent, QDesktopServices
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt5 import uic

from service_manager.constants import SERVICE_SETTINGS_FILE_NAME, service_path_dlg_ui
from service_manager.logger import manager_logger
from service_manager.settings import Settings


class UIServicePathDialog(QDialog):
    service_updated = pyqtSignal()

    def __init__(self):
        super(UIServicePathDialog, self).__init__()
        uic.loadUi(uifile=service_path_dlg_ui, baseinstance=self)

        self.initial_service_path = None
        self.ok_btn = self.button_box.button(QDialogButtonBox.Ok)

        # Assign slots to signals and events
        self.service_path.mouseDoubleClickEvent = lambda _: self.service_path.selectAll()
        self.service_path.textChanged.connect(self.clear_message)
        self.service_browse.clicked.connect(self.browse_file_dialog)
        self.button_box.accepted.connect(self.ok_pressed)
        self.button_box.rejected.connect(self.reject)
        self.help_btn = self.button_box.button(QDialogButtonBox.Help)
        self.help_btn.clicked.connect(on_help)

        self.service_path.textChanged.connect(self.check_if_path_changed)

        self.finished.connect(self.on_finished)

        self.update_fields()

    def update_fields(self):
        curr_path = Settings.Manager.service_path
        self.service_path.setText(curr_path)
        self.initial_service_path = curr_path
        self.ok_btn.setEnabled(False)

    def ok_pressed(self):
        path = self.service_path.text()
        if os.path.exists(path):
            settings_file = os.path.join(path, SERVICE_SETTINGS_FILE_NAME)
            if os.path.isfile(settings_file):  # setting file exists
                self.accept()
            else:
                # ask user if they want to create new settings file
                settings_not_found_msg = f'Service settings file "{SERVICE_SETTINGS_FILE_NAME}" ' \
                                         f'not found in "{path}". Create new blank settings file?'
                reply = QMessageBox.warning(self, 'HLM PV Import',
                                            settings_not_found_msg, QMessageBox.Yes, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    self.accept()
        else:
            self.message_lbl.setText('Path does not exist, please verify path is correct.')

    def on_finished(self, result):
        if result == QDialog.Accepted:
            path = self.service_path.text()
            Settings.Manager.service_path = path
            manager_logger.info('Service directory path changed.')
            service_settings_path = Settings.Manager.service_path
            # Init/Update Service settings with path
            Settings.init_service_settings(service_settings_path)
            self.service_updated.emit()

    def browse_file_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.service_path.setText(dir_path)

    def clear_message(self):
        self.message_lbl.clear()

    def check_if_path_changed(self):
        self.ok_btn.setEnabled(self.service_path.text() != self.initial_service_path)

    def showEvent(self, event: QShowEvent):
        self.update_fields()


def on_help():
    url = QUrl("https://github.com/ISISNeutronMuon/HLM_PV_Import/wiki")
    # noinspection PyArgumentList
    QDesktopServices.openUrl(url)
