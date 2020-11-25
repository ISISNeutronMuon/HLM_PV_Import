from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QDialogButtonBox,  QFrame, \
    QLayout, QComboBox
from PyQt5 import uic

from ServiceManager.constants import config_entry_ui
from ServiceManager.settings import Settings
from ServiceManager.db_utilities import DBUtils


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
        self.obj_name_cb.lineEdit().setPlaceholderText('Please enter the object name')
        self.obj_name_cb.setInsertPolicy(QComboBox.NoInsert)

        self.obj_detail_name = self.findChild(QLineEdit, 'objectNameDetailsLineEdit')
        self.obj_detail_id = self.findChild(QLineEdit, 'objectIdLineEdit')
        self.obj_detail_type = self.findChild(QLineEdit, 'objectTypeLineEdit')
        self.obj_detail_class = self.findChild(QLineEdit, 'objectClassLineEdit')
        self.obj_detail_func = self.findChild(QLineEdit, 'objectFunctionLineEdit')
        self.obj_detail_comment = self.findChild(QLineEdit, 'objectCommentLineEdit')
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

    def object_details_clicked(self):
        if self.obj_details_frame.isHidden():
            self.obj_details_frame.show()
        else:
            self.obj_details_frame.hide()

    def showEvent(self, e: QShowEvent):
        self.update_fields()

    def update_fields(self):
        names_list = DBUtils.get_all_object_names()

        self.obj_name_cb.clear()
        self.obj_name_cb.lineEdit().clear()
        self.obj_name_cb.addItem(None)
        self.obj_name_cb.addItems(names_list)

        self.clear_details()

    def update_details(self, *args):
        current_object = self.obj_name_cb.currentText()
        # If no name or object already has details, return
        if not current_object or current_object == self.last_details_update_obj:
            return

        obj_id = DBUtils.get_object_id(current_object)
        obj_record = DBUtils.get_object(obj_id)

        # If object was found, otherwise obj_id will be None
        if obj_id:
            self.obj_detail_name.setText(DBUtils.get_object_name(obj_id))
            self.obj_detail_id.setText(f'{obj_id}')
            self.obj_detail_type.setText(DBUtils.get_object_type(object_id=obj_id, name_only=True))
            self.obj_detail_class.setText(DBUtils.get_object_class(object_id=obj_id, name_only=True))
            self.obj_detail_func.setText(DBUtils.get_object_function(object_id=obj_id, name_only=True))
            self.obj_detail_comment.setText(obj_record[0][4])
            sld_record = DBUtils.get_object_sld(object_id=obj_id)
            if sld_record:
                self.obj_detail_sdl_name.setText(sld_record[0][2])
                self.obj_detail_sdl_id.setText(sld_record[0][0])

        self.last_details_update_obj = current_object

    def clear_details(self):
        self.obj_detail_name.clear()
        self.obj_detail_id.clear()
        self.obj_detail_type.clear()
        self.obj_detail_class.clear()
        self.obj_detail_func.clear()
        self.obj_detail_comment.clear()
        self.obj_detail_sdl_name.clear()
        self.obj_detail_sdl_id.clear()

        self.last_details_update_obj = None
