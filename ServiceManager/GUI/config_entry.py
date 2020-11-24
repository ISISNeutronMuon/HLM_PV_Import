from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QShowEvent, QDesktopServices
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QDialogButtonBox, QFileDialog, QMessageBox, QFrame, \
    QLayout, QComboBox
from PyQt5 import uic
from ServiceManager.settings import Settings, config_entry_ui
from ServiceManager.db_utilities import get_all_object_names, get_object_id, get_object_type, get_object_class


class CustomSignals(QObject):
    serviceUpdated = pyqtSignal()


class UIConfigEntryDialog(QDialog):
    def __init__(self):
        super(UIConfigEntryDialog, self).__init__()
        uic.loadUi(uifile=config_entry_ui, baseinstance=self)

        # region Attributes
        self.last_details_update_obj = None
        # endregion

        # region Get widgets
        self.obj_details_btn = self.findChild(QPushButton, 'objectDetailsButton')
        self.obj_details_frame = self.findChild(QFrame, 'detailsFrame')
        self.obj_name_cb = self.findChild(QComboBox, 'objectNameCB')
        self.obj_name_cb.setInsertPolicy(QComboBox.NoInsert)
        self.obj_detail_id = self.findChild(QLineEdit, 'objectIdLineEdit')
        self.obj_detail_type = self.findChild(QLineEdit, 'objectTypeLineEdit')
        self.obj_detail_class = self.findChild(QLineEdit, 'objectClassLineEdit')
        self.obj_detail_func = self.findChild(QLineEdit, 'objectFunctionLineEdit')
        self.obj_detail_sdl_name = self.findChild(QLineEdit, 'SLDNameLineEdit')
        self.obj_detail_sdl_id = self.findChild(QLineEdit, 'SLDIDLineEdit')
        # endregion

        # region Basic signals to slots
        self.obj_details_btn.clicked.connect(self.object_details_clicked)

        self.obj_name_cb.lineEdit().returnPressed.connect(self.update_details)
        self.obj_name_cb.currentIndexChanged.connect(self.update_details)
        self.obj_name_cb.focusOutEvent = self.update_details


        # endregion

        # region Events
        self.obj_details_frame.showEvent = lambda x: self.obj_details_btn.setText('Hide details')
        self.obj_details_frame.hideEvent = lambda x: self.obj_details_btn.setText('Show details')
        # endregion

        self.update_fields()

    def object_details_clicked(self):
        if self.obj_details_frame.isHidden():
            self.obj_details_frame.show()
        else:
            self.obj_details_frame.hide()

    def update_fields(self):
        names_list = get_all_object_names()
        self.obj_name_cb.addItems(names_list)
        self.obj_name_cb.lineEdit().setPlaceholderText('Please enter the object name')
        self.obj_name_cb.lineEdit().clear()

    def update_details(self, *args):
        current_object = self.obj_name_cb.currentText()
        # If no name or object already has details, return
        if not current_object or current_object == self.last_details_update_obj:
            return

        obj_id = get_object_id(current_object)

        # If object was found, otherwise obj_id will be None
        if obj_id:
            self.obj_detail_id.setText(f'{obj_id}')
            self.obj_detail_type.setText(get_object_type(object_id=obj_id, name_only=True))
            self.obj_detail_class.setText(get_object_class(object_id=obj_id, name_only=True))

        # self.obj_detail_func
        # self.obj_detail_sdl_name
        # self.obj_detail_sdl_id

        self.last_details_update_obj = current_object
