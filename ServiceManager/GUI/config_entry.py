from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QThread
from PyQt5.QtGui import QShowEvent, QCloseEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QDialogButtonBox, QFrame, \
    QLayout, QComboBox, QLabel, QProgressBar
from PyQt5 import uic

from ServiceManager.constants import config_entry_ui
from ServiceManager.settings import Settings, get_full_pv_name
from ServiceManager.utilities import get_pv_value
from ServiceManager.db_utilities import DBUtils
from ServiceManager.logger import logger

from caproto import CaprotoTimeoutError


class CustomSignals(QObject):
    serviceUpdated = pyqtSignal()


class FocusOutFilter(QObject):

    focusOut = pyqtSignal()

    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QEvent.FocusOut:
            # Custom actions
            self.focusOut.emit()
            # return False so that the widget will also handle the event
            # otherwise it won't focus out
            return False
        else:
            return False   # don't care about other events


class UIConfigEntryDialog(QDialog):
    def __init__(self):
        super(UIConfigEntryDialog, self).__init__()
        uic.loadUi(uifile=config_entry_ui, baseinstance=self)

        # region Attributes
        self.last_details_update_obj = None
        self.check_pvs_btn_default_text = None
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

        self.mea_pv_name_1 = self.findChild(QLineEdit, 'measurement1LineEdit')
        self.mea_pv_name_2 = self.findChild(QLineEdit, 'measurement2LineEdit')
        self.mea_pv_name_3 = self.findChild(QLineEdit, 'measurement3LineEdit')
        self.mea_pv_name_4 = self.findChild(QLineEdit, 'measurement4LineEdit')
        self.mea_pv_name_5 = self.findChild(QLineEdit, 'measurement5LineEdit')
        self.mea_pv_names = [
            self.mea_pv_name_1, self.mea_pv_name_2, self.mea_pv_name_3, self.mea_pv_name_4, self.mea_pv_name_5
        ]

        self.mea_type_lbl_1 = self.findChild(QLabel, 'mea1TypeLabel')
        self.mea_type_lbl_2 = self.findChild(QLabel, 'mea2TypeLabel')
        self.mea_type_lbl_3 = self.findChild(QLabel, 'mea3TypeLabel')
        self.mea_type_lbl_4 = self.findChild(QLabel, 'mea4TypeLabel')
        self.mea_type_lbl_5 = self.findChild(QLabel, 'mea5TypeLabel')
        self.mea_type_labels = [
            self.mea_type_lbl_1, self.mea_type_lbl_2, self.mea_type_lbl_3, self.mea_type_lbl_4, self.mea_type_lbl_5
        ]

        self.mea_status_lbl_1 = self.findChild(QLabel, 'meaStatus_1')
        self.mea_status_lbl_2 = self.findChild(QLabel, 'meaStatus_2')
        self.mea_status_lbl_3 = self.findChild(QLabel, 'meaStatus_3')
        self.mea_status_lbl_4 = self.findChild(QLabel, 'meaStatus_4')
        self.mea_status_lbl_5 = self.findChild(QLabel, 'meaStatus_5')
        self.mea_status_labels = [
            self.mea_status_lbl_1, self.mea_status_lbl_2, self.mea_status_lbl_3, self.mea_status_lbl_4,
            self.mea_status_lbl_5
        ]

        self.check_pvs_progress_bar = self.findChild(QProgressBar, 'checkMeasProgressBar')
        self.check_pvs_progress_bar.hide()
        self.check_pvs_btn = self.findChild(QPushButton, 'checkPvsButton')
        self.check_pvs_btn_default_text = self.check_pvs_btn.text()

        # endregion

        # region Basic signals to slots
        self.obj_details_btn.clicked.connect(self.object_details_clicked)

        self.obj_name_cb.lineEdit().returnPressed.connect(self.update_details)
        self.obj_name_cb.currentIndexChanged.connect(self.update_details)
        self.focus_out_filter = FocusOutFilter()  # instantiate event filter which signals upon widget focus out event
        self.obj_name_cb.installEventFilter(self.focus_out_filter)  # install filter to widget
        self.focus_out_filter.focusOut.connect(self.update_details)  # connect filter custom signal to slot

        # For each PV Name line edit, on text change, clear the PV connection status label text
        for index, mea_pv_name in enumerate(self.mea_pv_names):
            mea_pv_name.textChanged.connect(lambda _, i=index: self.measurement_pv_text_changed(i))

        self.check_pvs_btn.clicked.connect(self.check_measurement_pvs)
        # endregion

        # region Threads
        self.pvs_connection_thread = CheckPVsThread()
        self.pvs_connection_thread.mea_status_update.connect(self.update_measurements_pvs_status)
        self.pvs_connection_thread.display_progress_bar.connect(
            lambda x: self.check_pvs_progress_bar.show() if x else self.check_pvs_progress_bar.hide()
        )
        self.pvs_connection_thread.progress_bar_update.connect(
            lambda val: self.check_pvs_progress_bar.setValue(val)
        )
        self.pvs_connection_thread.started.connect(self.pvs_connection_check_started)
        self.pvs_connection_thread.finished.connect(self.pvs_connection_check_finished)
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

    def closeEvent(self, e: QCloseEvent):
        self.pvs_connection_thread.stop()

    def update_fields(self):
        names_list = DBUtils.get_all_object_names()

        self.obj_name_cb.clear()
        self.obj_name_cb.lineEdit().clear()
        self.obj_name_cb.addItem(None)
        self.obj_name_cb.addItems(names_list)

        self.clear_details()
        self.clear_pvs_connection_status()
        self.clear_measurement_type_labels()
        self.clear_measurement_pv_names()

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

    def clear_pvs_connection_status(self):
        for status_lbl in self.mea_status_labels:
            status_lbl.clear()
            status_lbl.setStyleSheet('')

    def clear_measurement_type_labels(self):
        for label in self.mea_type_labels:
            label.clear()

    def clear_measurement_pv_names(self):
        for line_edit in self.mea_pv_names:
            line_edit.clear()

    def update_details(self, *args):
        current_object = self.obj_name_cb.currentText()
        # If no name or object already has details, return
        if not current_object or current_object == self.last_details_update_obj:
            return

        obj_id = DBUtils.get_object_id(current_object)

        if not obj_id:
            return

        obj_record = DBUtils.get_object(obj_id)
        obj_class_record = DBUtils.get_object_class(object_id=obj_id)
        self.obj_detail_comment.setText(obj_record[0][4])
        self.obj_detail_name.setText(DBUtils.get_object_name(obj_id))
        self.obj_detail_id.setText(f'{obj_id}')
        self.obj_detail_type.setText(DBUtils.get_object_type(object_id=obj_id, name_only=True))
        self.obj_detail_class.setText(obj_class_record[0][2])
        self.obj_detail_func.setText(DBUtils.get_object_function(object_id=obj_id, name_only=True))

        sld_record = DBUtils.get_object_sld(object_id=obj_id)
        if sld_record:
            self.obj_detail_sdl_name.setText(sld_record[0][2])
            self.obj_detail_sdl_id.setText(sld_record[0][0])

        self.last_details_update_obj = current_object

        # Update the measurement types labels
        mea_types = DBUtils.get_class_measurement_types(class_id=obj_class_record[0][0])
        self.update_measurement_types(mea_types)

    def update_measurement_types(self, mea_types: dict):
        # mea_type_labels = list of QLabel widgets
        # mea_types (arg) = dictionary containing [Mea. Number/Type Description] pairs (e.g. {1: 'Temperature (K)', ...}
        for index, type_lbl in enumerate(self.mea_type_labels):
            type_lbl.setText(mea_types[index+1])

    def update_check_pvs_btn(self, pvs_check_running: bool):
        if pvs_check_running:
            self.check_pvs_btn.setText('Checking connections ...')
            self.check_pvs_btn.setEnabled(False)
        else:
            self.check_pvs_btn.setText(self.check_pvs_btn_default_text)
            self.check_pvs_btn.setEnabled(True)

    def check_measurement_pvs(self):
        """
        Check all line edits. If no text, skip. If text, take PV name (should accept both FULL and PARTIAL names),
        and try to connect and get value. If success, change label and set green, if timeout set red etc.
        While loading, change label text or add loading animation
        """
        names = []
        for pv_name in self.mea_pv_names:
            name = pv_name.text()
            if name:
                full_name = get_full_pv_name(name)
                names.append(full_name)
            else:
                names.append(None)
        self.pvs_connection_thread.set_pv_names(pv_names=names)
        self.pvs_connection_thread.start()

    def update_measurements_pvs_status(self, index: int, connected: bool):
        status_lbl = self.mea_status_labels[index]
        if connected:
            status_lbl.setText('OK')
            status_lbl.setStyleSheet('color: green;')
        else:
            status_lbl.setText('ERR')
            status_lbl.setStyleSheet('color: red;')

    def measurement_pv_text_changed(self, mea_no: int):
        self.mea_status_labels[mea_no].clear()

    def pvs_connection_check_started(self):
        self.update_check_pvs_btn(pvs_check_running=True)
        self.clear_pvs_connection_status()

    def pvs_connection_check_finished(self):
        self.update_check_pvs_btn(pvs_check_running=False)


class CheckPVsThread(QThread):

    mea_status_update = pyqtSignal(int, bool)
    progress_bar_update = pyqtSignal(int)
    display_progress_bar = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.finished.connect(self.clear_progress_bar)
        self.pv_names = None
        self._running = None

    def __del__(self):
        self.wait()

    def stop(self):
        self._running = False
        self.exit()

    def run(self):
        self._running = True
        logger.info(f'Checking connection of measurement PVs: {self.pv_names}')
        connected = []
        failed = []
        self.display_progress_bar.emit(True)
        for index, pv_name in enumerate(self.pv_names):
            if pv_name:
                try:
                    get_pv_value(name=pv_name, timeout=2)
                    if not self._running:
                        logger.info('Stopped PV connection check.')
                        break
                    self.mea_status_update.emit(index, True)
                    connected.append(pv_name)
                except CaprotoTimeoutError:
                    if not self._running:
                        logger.info('Stopped PV connection check.')
                        break
                    self.mea_status_update.emit(index, False)
                    failed.append(pv_name)

            self.progress_bar_update.emit(index+1)

        if self._running:
            logger.info(f'PV connection check finished. Connected: {connected}. Failed: {failed}')

    def set_pv_names(self, pv_names: list):
        self.pv_names = pv_names

    def clear_progress_bar(self):
        self.progress_bar_update.emit(0)
        self.display_progress_bar.emit(False)
