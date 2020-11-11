from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QDesktopServices, QPalette, QColor, QCloseEvent
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QDialogButtonBox
from PyQt5 import uic
import os
import sys
import ctypes
import win32serviceutil

from ServiceManager.utilities import is_admin, make_bold
from ServiceManager.settings import config, update_config


class UIDBSettings(QDialog):
    def __init__(self):
        super(UIDBSettings, self).__init__()
        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts', 'DBSettings.ui')
        uic.loadUi(ui_file_path, self)

        # Remove the "?" QWhatsThis button from the dialog
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.message = self.findChild(QLabel, 'message')

        self.host_label = self.findChild(QLabel, 'hostLabel')
        self.db_label = self.findChild(QLabel, 'dBNameLabel')
        self.user_label = self.findChild(QLabel, 'userLabel')
        self.password_label = self.findChild(QLabel, 'passLabel')


        self.host = self.findChild(QLineEdit, 'hostLineEdit')
        self.db = self.findChild(QLineEdit, 'dBNameLineEdit')
        self.user = self.findChild(QLineEdit, 'userLineEdit')
        self.password = self.findChild(QLineEdit, 'passLineEdit')

        # If app is not running with administrator privileges, cannot edit windows registry,
        # so disable name and pass fields, and hide user/password.
        if not is_admin():
            self.user.setEnabled(False)
            self.password.setEnabled(False)
            msg = 'Admin privileges required.'
            self.user.setText(msg)
            self.user.setToolTip('Please restart the app in Administrator Mode to edit this setting.')
            self.password.setText(msg)
            self.password.setToolTip('Please restart the app in Administrator Mode to edit this setting.')
        else:
            # Check if user and password are already in the registry and if so add them to the fields
            self.service_name = config['Service']['Name']
            self.reg_user = win32serviceutil.GetServiceCustomOption(serviceName=self.service_name, option='DB_HE_USER')
            self.reg_pass = win32serviceutil.GetServiceCustomOption(serviceName=self.service_name, option='DB_HE_PASS')

            if self.reg_user:
                self.user.setText(self.reg_user)

            if self.reg_pass:
                self.password.setText(self.reg_pass)

        # Check if host and db name are already in the settings.ini, and if so add them to the fields
        self.settings_host = config['HeRecoveryDB']['Host']
        self.settings_db = config['HeRecoveryDB']['Name']

        if self.settings_host:
            self.host.setText(self.settings_host)

        if self.settings_db:
            self.db.setText(self.settings_db)

        # Connect dialog box buttons
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)
        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)
        self.apply_btn.clicked.connect(self.save_new_settings)

        # Enable apply button on text change
        self.apply_btn.setEnabled(False)
        self.host.textChanged.connect(self.enable_apply)
        self.db.textChanged.connect(self.enable_apply)
        self.user.textChanged.connect(self.enable_apply)
        self.password.textChanged.connect(self.enable_apply)

    def enable_apply(self):
        if self.new_settings():
            self.apply_btn.setEnabled(True)
        else:
            self.apply_btn.setEnabled(False)

    def new_settings(self):
        setting_changed = False
        if self.host.text() != self.settings_host:
            setting_changed = True
            make_bold(self.host_label, True)
        else:
            make_bold(self.host_label, False)

        if self.db.text() != self.settings_db:
            setting_changed = True
            make_bold(self.db_label, True)
        else:
            make_bold(self.db_label, False)

        if self.user.text() != self.reg_user:
            setting_changed = True
            make_bold(self.user_label, True)
        else:
            make_bold(self.user_label, False)

        if self.password.text() != self.reg_pass:
            setting_changed = True
            make_bold(self.password_label, True)
        else:
            make_bold(self.password_label, False)

        return setting_changed

    def on_accepted(self):
        if self.apply_btn.isEnabled():
            self.save_new_settings()
        self.close()

    def on_rejected(self):
        self.close()

    def save_new_settings(self):

        config.set('HeRecoveryDB', 'Host', self.host.text())
        config.set('HeRecoveryDB', 'Name', self.db.text())
        update_config()

        if is_admin():
            try:
                win32serviceutil.SetServiceCustomOption(
                    serviceName=self.service_name, option='DB_HE_USER', value=self.user.text()
                )
                win32serviceutil.SetServiceCustomOption(
                    serviceName=self.service_name, option='DB_HE_PASS', value=self.password.text()
                )

                pal = self.message.palette()
                pal.setColor(QPalette.WindowText, QColor('green'))
                self.message.setPalette(pal)
                self.message.setText('Updated DB configuration.')
            except Exception as e:
                pal = self.message.palette()
                pal.setColor(QPalette.WindowText, QColor('red'))
                self.message.setPalette(pal)
                self.message.setText(f'{e}')

        else:
            pal = self.message.palette()
            pal.setColor(QPalette.WindowText, QColor('green'))
            self.message.setPalette(pal)
            self.message.setText('Updated DB configuration.')

        self.refresh()

    def closeEvent(self, event: QCloseEvent):
        """ Upon dialog close """
        pal = self.message.palette()
        pal.setColor(QPalette.WindowText, QColor('black'))
        self.message.setPalette(pal)
        self.message.setText('')

    def refresh(self):
        self.apply_btn.setEnabled(False)

        make_bold(self.host_label, False)
        make_bold(self.db_label, False)
        make_bold(self.user_label, False)
        make_bold(self.password_label, False)

        # Update current config settings to detect further changes
        self.settings_host = self.host.text()
        self.settings_db = self.db.text()

        if is_admin():
            # Update current registry settings to detect further changes
            self.reg_user = self.user.text()
            self.reg_pass = self.password.text()
