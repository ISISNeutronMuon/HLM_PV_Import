from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QListWidget, QLineEdit, QDialogButtonBox, QLabel, QListWidgetItem, \
    QAbstractItemView, QStyledItemDelegate, QWidget, QStyleOptionViewItem, QMessageBox
from PyQt5 import uic
from ServiceManager.settings import ca_settings_ui, Settings


class UICASettings(QDialog):
    def __init__(self):
        super(UICASettings, self).__init__()
        uic.loadUi(uifile=ca_settings_ui, baseinstance=self)

        self._settings_changed = False

        # Get widgets
        self.addr_list = self.findChild(QListWidget, 'addressList')
        self.addr_new_btn = self.findChild(QPushButton, 'newAddress')
        self.addr_edit_btn = self.findChild(QPushButton, 'editAddress')
        self.addr_del_btn = self.findChild(QPushButton, 'deleteAddress')

        self.pv_prefix_ln = self.findChild(QLineEdit, 'pVPrefixLineEdit')
        self.pv_domain_ln = self.findChild(QLineEdit, 'pVDomainLineEdit')
        self.pv_stale_ln = self.findChild(QLineEdit, 'pVDataStaleLineEdit')
        self.pv_timeout_ln = self.findChild(QLineEdit, 'pVConnTimeoutLineEdit')

        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)
        self.apply_btn.setEnabled(False)
        self.message = self.findChild(QLabel, 'message')

        # Connect signals to slots
        self.addr_new_btn.clicked.connect(self.new_address)
        self.addr_edit_btn.clicked.connect(self.edit_address)
        self.addr_del_btn.clicked.connect(self.delete_address)

        self.pv_timeout_ln.textChanged.connect(lambda _: self.settings_changed(True))
        self.pv_stale_ln.textChanged.connect(lambda _: self.settings_changed(True))
        self.pv_prefix_ln.textChanged.connect(lambda _: self.settings_changed(True))
        self.pv_domain_ln.textChanged.connect(lambda _: self.settings_changed(True))

        self.button_box.rejected.connect(self.on_rejected)
        self.button_box.accepted.connect(self.on_accepted)
        self.apply_btn.clicked.connect(self.on_apply)

        # Editor delegate to emit signals when list item editing is started/finished
        self.editor_delegate = EditableListStyledItemDelegate()
        self.editor_delegate.editStarted.connect(self.edit_started)
        self.editor_delegate.editFinished.connect(self.edit_finished)
        self.addr_list.setItemDelegate(self.editor_delegate)

        # Fill widgets with current settings
        self.update_fields()

        self.settings_changed(False)

    def apply_new_settings(self):
        # Epics CA Addr. List
        address_list = [self.addr_list.item(i).text() for i in range(self.addr_list.count())]
        Settings.Service.CA.set_addr_list(address_list)

        # PV Settings
        pv_prefix = self.pv_prefix_ln.text()
        pv_domain = self.pv_domain_ln.text()
        pv_stale_threshold = self.pv_stale_ln.text()
        conn_timeout = self.pv_timeout_ln.text()
        
        Settings.Service.CA.set_pv_prefix(pv_prefix)
        Settings.Service.CA.set_pv_domain(pv_domain)
        Settings.Service.CA.set_pv_stale_after(pv_stale_threshold)
        Settings.Service.CA.set_conn_timeout(conn_timeout)

    def update_fields(self):
        """
        Update the widgets with the current settings.
        """
        # Update CA Addr List
        self.addr_list.clear()  # Clear the list items, then add the updated ones
        ca_address_list = Settings.Service.CA.get_addr_list(as_list=True)
        self.addr_list.addItems(ca_address_list)
        for index in range(self.addr_list.count()):
            item = self.addr_list.item(index)
            item.setFlags(item.flags() | Qt.ItemIsEditable)

        # Update PV Settings
        pv_prefix = Settings.Service.CA.get_pv_prefix()
        pv_domain = Settings.Service.CA.get_pv_domain()
        pv_stale = Settings.Service.CA.get_pv_stale_after()
        pv_timeout = Settings.Service.CA.get_conn_timeout()

        self.pv_prefix_ln.setText(pv_prefix)
        self.pv_domain_ln.setText(pv_domain)
        self.pv_stale_ln.setText(pv_stale)
        self.pv_timeout_ln.setText(pv_timeout)

    def on_accepted(self):
        self.on_apply()
        self.close()

    def on_rejected(self):
        self.close()

    def on_apply(self):
        self.apply_new_settings()
        self.update_fields()
        self.settings_changed(False)

    def closeEvent(self, event: QCloseEvent):
        self.update_fields()
        if self._settings_changed:
            quit_msg = "Any changes will be lost. Cancel anyway?"
            reply = QMessageBox.question(self, 'HLM PV Import',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def showEvent(self, event: QShowEvent):
        self.update_fields()
        self.settings_changed(False)

    def new_address(self):
        item = QListWidgetItem()
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setSelected(True)
        self.addr_list.addItem(item)
        self.addr_list.setCurrentItem(item)
        self.addr_list.scrollToItem(item, QAbstractItemView.PositionAtTop)
        self.addr_list.editItem(item)
        self.settings_changed()

    def edit_address(self):
        selected_item = self.addr_list.currentItem()
        self.addr_list.editItem(selected_item)

    def delete_address(self):
        selected_item = self.addr_list.currentItem()
        item_row = self.addr_list.row(selected_item)
        self.addr_list.takeItem(item_row)
        # Items removed from a list widget will not be managed by Qt, and will need to be deleted manually.
        del selected_item
        self.settings_changed()

    def edit_started(self):
        self.addr_del_btn.setEnabled(False)

    def edit_finished(self):
        item = self.addr_list.currentItem()
        text_no_space = item.text().replace(' ', '')
        item.setText(text_no_space)
        if not item.text():
            self.delete_address()
        self.addr_del_btn.setEnabled(True)
        self.settings_changed()

    def settings_changed(self, _=True):
        self._settings_changed = _
        self.apply_btn.setEnabled(_)


class EditableListStyledItemDelegate(QStyledItemDelegate):
    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = pyqtSignal(QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = pyqtSignal(QModelIndex, name='editFinished')

    _is_editing = None

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor = super().createEditor(parent, option, index)
        if editor is not None:
            self.editStarted.emit(index)
            self._is_editing = True
        return editor

    def destroyEditor(self, editor: QWidget, index: QModelIndex):
        self.editFinished.emit(index)
        self._is_editing = False
        return super().destroyEditor(editor, index)

    def is_editing(self):
        return self._is_editing
