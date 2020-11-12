from PyQt5.QtWidgets import QDialog, QPushButton, QListWidget, QLineEdit, QDialogButtonBox
from PyQt5 import uic
from ServiceManager.settings import general_settings_ui, service_settings


class UIGeneralSettings(QDialog):
    def __init__(self):
        super(UIGeneralSettings, self).__init__()
        uic.loadUi(uifile=general_settings_ui, baseinstance=self)

        # Get widgets
        self.addr_list = self.findChild(QListWidget, 'addressList')
        self.addr_new = self.findChild(QPushButton, 'newAddress')
        self.addr_edit = self.findChild(QPushButton, 'editAddress')
        self.addr_del = self.findChild(QPushButton, 'deleteAddress')
        self.service_path = self.findChild(QLineEdit, 'servicePath')
        self.service_browse = self.findChild(QPushButton, 'browsePath')
        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')

        # Fill widgets with current settings
        self.update_fields()

    def update_fields(self):
        """
        Update the widgets with the current settings.
        """
        # Update CA Addr List
        ca_address_list = service_settings.CA.get_addr_list(as_list=True)
        for addr in ca_address_list:
            self.addr_list.addItem(addr)

        # Update service path

