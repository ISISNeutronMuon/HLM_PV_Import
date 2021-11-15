from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, QAbstractItemView, QStyledItemDelegate, \
    QWidget, QStyleOptionViewItem
from PyQt5 import uic

from ServiceManager.constants import ca_settings_ui
from ServiceManager.settings import Settings
from ServiceManager.utilities import apply_unsaved_changes_dialog


class UICASettings(QDialog):
    def __init__(self):
        super(UICASettings, self).__init__()
        uic.loadUi(uifile=ca_settings_ui, baseinstance=self)
        self.setModal(True)
        
        self._settings_changed = False

        # region Get widgets
        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)
        # endregion

        # region Connect signals to slots
        self.addr_new_btn.clicked.connect(self.new_address)
        self.addr_edit_btn.clicked.connect(self.edit_address)
        self.addr_del_btn.clicked.connect(self.delete_address)

        self.text_settings = [self.pv_timeout_ln, self.pv_stale_ln, self.pv_prefix_ln, self.pv_domain_ln]
        [line_edit.textChanged.connect(lambda _: self.settings_changed(True)) for line_edit in self.text_settings]
        self.add_stale_pvs.stateChanged.connect(lambda _: self.settings_changed(True))

        self.button_box.rejected.connect(self.close)
        self.button_box.accepted.connect(self.on_accepted)
        self.apply_btn.clicked.connect(self.on_apply)
        # endregion

        # Editor delegate to emit signals when list item editing is started/finished
        self.editor_delegate = EditableListStyledItemDelegate()
        self.editor_delegate.editStarted.connect(self.edit_started)
        self.editor_delegate.editFinished.connect(self.edit_finished)
        self.addr_list.setItemDelegate(self.editor_delegate)

    def apply_new_settings(self):
        # Epics CA Addr. List
        address_list = [self.addr_list.item(i).text() for i in range(self.addr_list.count())]
        Settings.Service.CA.addr_list = address_list

        # PV Settings
        Settings.Service.CA.stale = self.pv_stale_ln.text()
        Settings.Service.CA.timeout = self.pv_timeout_ln.text()
        Settings.Service.CA.prefix = self.pv_prefix_ln.text()
        Settings.Service.CA.domain = self.pv_domain_ln.text()
        Settings.Service.CA.add_stale = self.add_stale_pvs.isChecked()

    def update_fields(self):
        """
        Update the widgets with the current settings.
        """
        # Update CA Addr List
        self.addr_list.clear()  # Clear the list items, then add the updated ones
        addr_list = Settings.Service.CA.addr_list.split(' ')  # split the addresses into python list
        self.addr_list.addItems(addr_list)
        for index in range(self.addr_list.count()):
            item = self.addr_list.item(index)
            item.setFlags(item.flags() | Qt.ItemIsEditable)

        # Update PV Settings
        self.pv_stale_ln.setText(Settings.Service.CA.stale)
        self.pv_timeout_ln.setText(Settings.Service.CA.timeout)
        self.pv_prefix_ln.setText(Settings.Service.CA.prefix)
        self.pv_domain_ln.setText(Settings.Service.CA.domain)
        self.add_stale_pvs.setChecked(Settings.Service.CA.add_stale)
        self.message.clear()

    def on_accepted(self):
        if self._settings_changed:
            self.on_apply()
        self.close()

    def on_apply(self):
        self.apply_new_settings()
        self.update_fields()
        self.settings_changed(False)
        self.message.setText('Settings updated.')

    def closeEvent(self, event: QCloseEvent):
        apply_unsaved_changes_dialog(event, self.apply_new_settings, self._settings_changed)

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
        # https://doc.qt.io/qt-5/qlistwidget.html#takeItem
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

    def settings_changed(self, changed=True):
        self._settings_changed = changed
        self.apply_btn.setEnabled(changed)


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
