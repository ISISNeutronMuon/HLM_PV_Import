from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCloseEvent
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QDialogButtonBox
from PyQt5 import uic

from ServiceManager.utilities import is_admin, make_bold, set_colored_text
from ServiceManager.settings import db_settings_ui, Settings


class UIDBSettings(QDialog):
    def __init__(self):
        super(UIDBSettings, self).__init__()
        uic.loadUi(uifile=db_settings_ui, baseinstance=self)

        # Initialize attributes for storing current settings
        self.settings_host = None   # Store the DB host from settings.ini
        self.settings_db = None     # Store the DB name from settings.ini
        self.reg_user = None        # Store the DB user from Windows Registry
        self.reg_pass = None        # Store the DB password from Windows Registry

        # Remove the "?" QWhatsThis button from the dialog
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        # Get the widgets from the UI
        self.message = self.findChild(QLabel, 'message')
        self.host_label = self.findChild(QLabel, 'hostLabel')
        self.db_label = self.findChild(QLabel, 'dBNameLabel')
        self.user_label = self.findChild(QLabel, 'userLabel')
        self.password_label = self.findChild(QLabel, 'passLabel')
        self.host = self.findChild(QLineEdit, 'hostLineEdit')
        self.db = self.findChild(QLineEdit, 'dBNameLineEdit')
        self.user = self.findChild(QLineEdit, 'userLineEdit')
        self.password = self.findChild(QLineEdit, 'passLineEdit')

        # Add the current settings to the LineEdit widgets (input fields).
        self.update_fields()

        # Assign slots to button signals
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)
        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)
        self.apply_btn.clicked.connect(self.save_new_settings)

        # Enable apply button on text change
        self.apply_btn.setEnabled(False)
        self.host.textChanged.connect(self.new_settings)
        self.db.textChanged.connect(self.new_settings)
        self.user.textChanged.connect(self.new_settings)
        self.password.textChanged.connect(self.new_settings)

    def new_settings(self):
        """
        Make the labels of LineEdits that were modified bold, and enables the Apply button, and OK submit functionality,
        if at least one setting has been changed.
        """
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

        if is_admin():  # If not in admin, these settings can't be changed anyway so ignore them
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

        # If at least one field was updated, enable the apply button.
        if setting_changed:
            self.apply_btn.setEnabled(True)
        else:
            self.apply_btn.setEnabled(False)

    def on_accepted(self):
        if self.apply_btn.isEnabled():  # if apply button is disabled, it means there is nothing new to save
            self.save_new_settings()
        self.close()

    def on_rejected(self):
        self.close()

    def save_new_settings(self):
        Settings.Service.HeliumDB.set_host(self.host.text())
        Settings.Service.HeliumDB.set_name(self.db.text())

        if is_admin():
            try:
                Settings.Service.HeliumDB.set_user(self.user.text())
                Settings.Service.HeliumDB.set_pass(self.password.text())

                set_colored_text(label=self.message, text='Updated DB configuration.', color=QColor('green'))
            except Exception as e:
                set_colored_text(label=self.message, text=f'{e}', color=QColor('red'))

        else:
            set_colored_text(label=self.message, text='Updated DB configuration.', color=QColor('green'))

        self.refresh()

    def closeEvent(self, event: QCloseEvent):
        """ Upon dialog close """
        set_colored_text(label=self.message, text='', color=QColor('black'))  # Remove message upon window close
        self.refresh()
        event.accept()

    def refresh(self):
        """ Reset widgets to default, fetch current settings. """
        self.apply_btn.setEnabled(False)

        self.update_fields()

        make_bold(self.host_label, False)
        make_bold(self.db_label, False)
        make_bold(self.user_label, False)
        make_bold(self.password_label, False)

    def update_fields(self):
        """
        Update the QLineEdit widgets with data from the current settings (.ini and registry).
        """
        # If app is not running with administrator privileges, cannot edit windows registry,
        # so disable name and pass fields, and hide user/password.
        if not is_admin():
            self.user.setEnabled(False)
            self.password.setEnabled(False)
            msg = 'Admin privileges required.'
            self.user.setText(None)
            self.user.setPlaceholderText(msg)
            self.user.setToolTip('Please restart the app in Administrator Mode to edit this setting.')
            self.password.setPlaceholderText(msg)
            self.password.setToolTip('Please restart the app in Administrator Mode to edit this setting.')
        else:
            # Check if user and password are already in the registry and if so add them to the fields
            self.reg_user = Settings.Service.HeliumDB.get_user()
            self.reg_pass = Settings.Service.HeliumDB.get_pass()

            if self.reg_user:
                self.user.setText(self.reg_user)

            if self.reg_pass:
                self.password.setText(self.reg_pass)

        # Check if host and db name are already in the settings.ini, and if so add them to the fields
        self.settings_host = Settings.Service.HeliumDB.get_host()
        self.settings_db = Settings.Service.HeliumDB.get_name()

        if self.settings_host:
            self.host.setText(self.settings_host)

        if self.settings_db:
            self.db.setText(self.settings_db)
