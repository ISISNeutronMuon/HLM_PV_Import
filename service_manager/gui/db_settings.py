from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5 import uic

from service_manager.constants import db_settings_ui
from service_manager.utilities import is_admin, make_bold, set_colored_text, \
    apply_unsaved_changes_dialog
from service_manager.settings import Settings


class UIDBSettings(QDialog):
    update_db_connection_status = pyqtSignal()

    def __init__(self):
        super(UIDBSettings, self).__init__()
        uic.loadUi(uifile=db_settings_ui, baseinstance=self)
        self.setModal(True)

        # Initialize attributes for storing current settings
        self.settings_host = None  # Store the DB host from settings.ini
        self.settings_db = None  # Store the DB name from settings.ini
        self.reg_user = None  # Store the DB user from Windows Registry
        self.reg_pass = None  # Store the DB password from Windows Registry

        # Remove the "?" QWhatsThis button from the dialog
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        # Assign slots to button signals
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
        Make the labels of LineEdits that were modified bold, and enables the Apply button,
        and OK submit functionality, if at least one setting has been changed.
        """
        any_setting_changed = False
        settings_to_check = [(self.host.text() != self.settings_host, self.host_label, False),
                             (self.db.text() != self.settings_db, self.db_label, False),
                             (self.user.text() != self.reg_user, self.user_label, True),
                             (self.password.text() != self.reg_pass, self.password_label, True)]

        for setting_changed, label, admin_req in settings_to_check:
            if not (admin_req is True and is_admin() is False):
                any_setting_changed |= setting_changed
            if not admin_req or is_admin():
                make_bold(label, setting_changed)

        # If at least one field was updated, enable the apply button.
        self.apply_btn.setEnabled(any_setting_changed)

    def on_accepted(self):
        # if apply button is disabled, it means there is nothing new to save
        if self.apply_btn.isEnabled():
            self.save_new_settings()
        self.close()

    def on_rejected(self):
        self.close()

    def save_new_settings(self):
        Settings.Service.HeliumDB.host = self.host.text()
        Settings.Service.HeliumDB.name = self.db.text()

        if is_admin():
            try:
                Settings.Service.HeliumDB.user = self.user.text()
                Settings.Service.HeliumDB.password = self.password.text()

                registry_user = Settings.Service.HeliumDB.user
                registry_pass = Settings.Service.HeliumDB.password

                if registry_user == self.user.text() and registry_pass == self.password.text():
                    set_colored_text(label=self.message, text='Updated DB configuration.',
                                     color=QColor('green'))
                else:
                    set_colored_text(label=self.message,
                                     text='User/Password could not be updated.\nPlease verify the '
                                          ''                                                      
                                          'service is found.',
                                     color=QColor('red'))
            except Exception as e:
                set_colored_text(label=self.message, text=f'{e}', color=QColor('red'))

        else:
            set_colored_text(label=self.message, text='Updated DB configuration.',
                             color=QColor('green'))

        self.reset_styles()

        # Establish new DB connection and get result
        connected = Settings.Service.connect_to_db()
        if connected is True:
            set_colored_text(label=self.message, text=f'{self.message.text()}\nConnected to DB.',
                             color=QColor('green'))
        elif connected is False:
            set_colored_text(label=self.message,
                             text=f'{self.message.text()}\nCould not establish DB connection, '
                                  f'please check log for details.',
                             color=QColor('red')
                             )
        self.update_db_connection_status.emit()

    def closeEvent(self, event: QCloseEvent):
        """ Upon dialog close """
        # Remove message upon window close
        set_colored_text(label=self.message, text='', color=QColor('black'))
        apply_unsaved_changes_dialog(event, self.save_new_settings, self.apply_btn.isEnabled())

    def showEvent(self, event: QShowEvent):
        self.update_fields()
        self.reset_styles()

    def reset_styles(self):
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
            for widget in [self.user, self.password]:
                widget.setPlaceholderText(msg)
                widget.setToolTip(
                    'Please restart the app in Administrator Mode to edit this setting.')
        else:
            self.reg_user = Settings.Service.HeliumDB.user
            self.reg_pass = Settings.Service.HeliumDB.password
            self.user.setText(self.reg_user)
            self.password.setText(self.reg_pass)

        # Check if host and db name are already in the settings.ini, and if so add them to the
        # fields
        self.settings_host = Settings.Service.HeliumDB.host
        self.settings_db = Settings.Service.HeliumDB.name

        if self.settings_host:
            self.host.setText(self.settings_host)

        if self.settings_db:
            self.db.setText(self.settings_db)
