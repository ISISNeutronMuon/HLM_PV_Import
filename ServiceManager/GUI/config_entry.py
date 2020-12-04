from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QThread, Qt, QSize
from PyQt5.QtGui import QShowEvent, QCloseEvent, QFont, QMovie
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QDialogButtonBox, QFrame, \
    QLayout, QComboBox, QLabel, QProgressBar, QSpinBox, QMessageBox, QApplication, QHBoxLayout, QWidget, QVBoxLayout, \
    QCheckBox
from PyQt5 import uic

from ServiceManager.constants import config_entry_ui, loading_animation
from ServiceManager.settings import Settings, get_full_pv_name
from ServiceManager.utilities import get_pv_value
from ServiceManager.db_utilities import DBUtils
from ServiceManager.logger import logger

from caproto import CaprotoTimeoutError


class UIConfigEntryDialog(QDialog):
    def __init__(self):
        super(UIConfigEntryDialog, self).__init__()
        uic.loadUi(uifile=config_entry_ui, baseinstance=self)

        # region Attributes
        self._settings_changed = None
        self.last_details_update_obj = None
        self.check_pvs_btn_default_text = None
        self.loading_msg = LoadingPopupWindow()
        self.on_accepted_obj_id = None
        self.on_accepted_already_exists = None
        # endregion

        # region Get widgets
        self.obj_details_btn = self.findChild(QPushButton, 'objectDetailsButton')
        self.obj_details_frame = self.findChild(QFrame, 'detailsFrame')

        self.obj_name_label = self.findChild(QLabel, 'objectNameLabel')
        self.obj_name_cb = self.findChild(QComboBox, 'objectNameCB')
        self.obj_name_cb.lineEdit().setPlaceholderText('Please enter the object name')
        self.obj_name_cb.setInsertPolicy(QComboBox.NoInsert)
        self.obj_name_frame = self.findChild(QFrame, 'objectNameFrame')

        self.log_interval_sb = self.findChild(QSpinBox, 'logIntervalSpinBox')

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
        self.mea_pvs_frame = self.findChild(QFrame, 'measurementsPVNamesFrame')

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

        self.message_lbl = self.findChild(QLabel, 'message_lbl')

        self.ok_btn = self.findChild(QPushButton, 'dialog_btn_ok')
        self.cancel_btn = self.findChild(QPushButton, 'dialog_btn_cancel')
        self.help_btn = self.findChild(QPushButton, 'dialog_btn_help')
        # endregion

        # region Basic signals to slots
        self.obj_details_btn.clicked.connect(self.object_details_btn_clicked)

        self.obj_name_cb.lineEdit().returnPressed.connect(self.update_data)
        self.obj_name_cb.currentIndexChanged.connect(self.update_data)
        self.obj_name_cb.lineEdit().textChanged.connect(lambda _: self.settings_changed(True))
        self.obj_name_cb.lineEdit().textChanged.connect(
            lambda: self.obj_name_frame.setStyleSheet(f'QFrame#{self.obj_name_frame.objectName()} {{}}')
        )

        self.object_name_filter = ObjectNameCBFilter()  # instantiate event filter with custom signals
        self.obj_name_cb.installEventFilter(self.object_name_filter)  # install filter to widget
        self.object_name_filter.focusOut.connect(self.update_data)  # connect filter custom signal to slot

        self.log_interval_sb.valueChanged.connect(lambda _: self.settings_changed(True))

        # For each PV Name line edit, on text change, clear the PV connection status label text
        for index, mea_pv_name in enumerate(self.mea_pv_names):
            mea_pv_name.textChanged.connect(lambda _, i=index: self.measurement_pv_text_changed(i))
            mea_pv_name.textChanged.connect(
                lambda: self.mea_pvs_frame.setStyleSheet(f'QFrame#{self.mea_pvs_frame.objectName()} {{}}')
            )

        self.check_pvs_btn.clicked.connect(self.start_measurement_pvs_check)

        self.ok_btn.clicked.connect(self.on_accepted)
        self.cancel_btn.clicked.connect(self.on_cancel)
        self.help_btn.clicked.connect(self.on_help)
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
        self.pvs_connection_thread.finished_check_before_add_config.connect(self.add_entry_pv_check_finished)

        # QThread graceful exit on app close
        QApplication.instance().aboutToQuit.connect(self.pvs_connection_thread.stop)
        # endregion

        # region Events
        self.obj_details_frame.showEvent = lambda x: self.obj_details_btn.setText('Hide details')
        self.obj_details_frame.hideEvent = lambda x: self.obj_details_btn.setText('Show details')
        # endregion

    # region Override events
    def showEvent(self, e: QShowEvent):
        self.update_fields()

    def closeEvent(self, e: QCloseEvent):
        self.pvs_connection_thread.stop()
        self.loading_msg.close()

    # endregion

    # region Widget refresh & updates
    def update_fields(self):
        names_list = DBUtils.get_all_object_names()

        self.obj_name_cb.clear()
        self.obj_name_cb.lineEdit().clear()
        self.obj_name_cb.addItem(None)
        self.obj_name_cb.addItems(names_list)

        self.log_interval_sb.setValue(Settings.Manager.get_default_meas_update_interval())

        self.clear_details()
        self.clear_pvs_connection_status()
        self.clear_measurement_type_labels()
        self.clear_measurement_pv_names()

        self.message_lbl.clear()
        self.obj_name_frame.setStyleSheet(f'QFrame#{self.obj_name_frame.objectName()} {{}}')
        self.mea_pvs_frame.setStyleSheet(f'QFrame#{self.mea_pvs_frame.objectName()} {{}}')

        self.enable_or_disable_check_pvs_btn()

        self.settings_changed(False)
        self.connection_results = None

    def settings_changed(self, changed=True):
        self._settings_changed = changed

    def measurements_have_pv(self):
        # True if at least one measurement line edit widget is not empty.
        enabled = False
        for line_edit in self.mea_pv_names:
            if line_edit.text():
                enabled = True
                break

        return enabled

    # endregion

    # region Accept, Reject, Save
    def on_accepted(self):

        # Validate and display invalid input message + red highlight relevant frames if invalid
        if not self.input_fields_valid():
            return

        object_name = self.obj_name_cb.lineEdit().text()
        object_id = DBUtils.get_object_id(object_name)

        # Object not in DB, ask if create with default vals
        if not object_id:
            # todo: dialog asking if create obj with default values. Type must be specified from combo box. Types will
            # todo: be fetched from the default values settings file in Manager
            # todo: Types and their default values should be configurable through general settings.
            print('Not exist - create with default vals?')
            return

        # Check if object already has a PV configuration
        existing_ids = Settings.Service.PVConfig.get_entry_object_ids()
        already_exists = False
        if object_id in existing_ids:  # if it does, ask if overwrite
            already_exists = True
            msg_box = OverwriteMessageBox(object_id, object_name)
            resp = msg_box.exec()
            if resp != QMessageBox.Ok:
                return

        # Test PV connections if auto-check is enabled
        auto_pv_check_enabled = Settings.Manager.get_new_entry_auto_pv_check()
        if auto_pv_check_enabled:
            self.on_accepted_obj_id = object_id
            self.on_accepted_already_exists = already_exists
            self.start_measurement_pvs_check(on_add_config=True)
            self.loading_msg.show()
        else:
            self.add_entry(object_id=object_id, overwrite=already_exists)

    def add_entry_pv_check_finished(self):
        """
        If auto PV conn. check on new entry is enabled, call the start check method with flag to mark it's a check
        before adding the entry.
        While the connection checks are being made, show a loading message pop-up.
        When the PV conn thread finishes after its test was started with the flag, it will emit a signal
        to call this method, which closes the loading message and checks for failed connections.
        If there are any, ask the user if they want to add the config anyway via another message box, and if so,
        finally call the add entry method.

        If auto PV check is disabled in settings, this step will be skipped and add entry will be called directly
        from the on accepted slot.
        """
        self.loading_msg.close()
        failed_connections = self.pvs_connection_thread.results['failed']
        if failed_connections:
            msg_box = QMessageBox.warning(self, 'PV Connection Failed',
                                          'Could not establish connection to one or more PVs.\n'
                                          'Add configuration anyway? (not recommended)',
                                          QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if msg_box == QMessageBox.Yes:
                self.add_entry(object_id=self.on_accepted_obj_id, overwrite=self.on_accepted_already_exists)

    def add_entry(self, object_id: int, overwrite: bool):
        """
        Prepare the config data to add a new entry or overwrites an existing one.

        Args:
            object_id (int): The object ID.
            overwrite (bool): If object already has config, overwrite entry. If False, append as normal.
        """
        log_period = self.log_interval_sb.value()
        mea_pv_names_text = [x.text() for x in self.mea_pv_names]
        measurement_pvs = {}
        for index, pv_name in enumerate(mea_pv_names_text):
            measurement_pvs[f'{index + 1}'] = pv_name if pv_name else None

        config_data = {
            Settings.Service.PVConfig.OBJ: object_id,
            Settings.Service.PVConfig.LOG_PERIOD: log_period,
            Settings.Service.PVConfig.MEAS: measurement_pvs
        }

        if overwrite:
            Settings.Service.PVConfig.add_entry(config_data, overwrite=True)
        else:
            Settings.Service.PVConfig.add_entry(config_data)

    def input_fields_valid(self):
        invalid_input = False
        # if no object name
        if not self.obj_name_cb.lineEdit().text():
            self.message_lbl.setStyleSheet('color: red;')
            self.message_lbl.setText('Object name is required.\n')
            self.obj_name_frame.setStyleSheet(f'QFrame#{self.obj_name_frame.objectName()} {{border: 1px solid red;}}')
            invalid_input = True

        # if no measurement PV (at least one)
        if not self.measurements_have_pv():
            self.message_lbl.setStyleSheet('color: red;')
            self.message_lbl.setText(f'{self.message_lbl.text()}At least one measurement is required.\n')
            self.mea_pvs_frame.setStyleSheet(f'QFrame#{self.mea_pvs_frame.objectName()} {{border: 1px solid red;}}')
            invalid_input = True

        return False if invalid_input else True

    def on_cancel(self):
        self.close()

    def on_help(self):
        # todo
        self.loading_msg.show()
        pass

    # endregion

    # region Object details
    def object_details_btn_clicked(self):
        if self.obj_details_frame.isHidden():
            self.obj_details_frame.show()
        else:
            self.obj_details_frame.hide()

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

    def update_data(self, *args):
        current_object = self.obj_name_cb.currentText()
        # If no name or object data already displayed, return
        if not current_object or current_object == self.last_details_update_obj:
            return

        obj_id = DBUtils.get_object_id(current_object)

        if not obj_id:
            return

        self.clear_details()
        self.update_details(obj_id, current_object)

        self.clear_measurement_pv_names()
        self.update_measurements(obj_id)

    def update_details(self, obj_id: int, current_object: str):
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

    def update_measurements(self, obj_id: int):
        obj_entry = Settings.Service.PVConfig.get_entry_with_id(obj_id)
        if not obj_entry:
            return
        mea_pvs = obj_entry[Settings.Service.PVConfig.MEAS]
        for index, pv_name_line_edit in enumerate(self.mea_pv_names):
            try:
                pv_name_line_edit.setText(mea_pvs[f'{index+1}'])
            except KeyError:
                continue

    # endregion

    # region Measurement PVs
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

    def update_measurement_types(self, mea_types: dict):
        # mea_type_labels = list of QLabel widgets
        # mea_types (arg) = dictionary containing [Mea. Number/Type Description] pairs (e.g. {1: 'Temperature (K)', ...}
        for index, type_lbl in enumerate(self.mea_type_labels):
            type_lbl.setText(mea_types[index + 1])

    def update_check_pvs_widgets(self, pvs_check_running: bool):
        if pvs_check_running:
            self.check_pvs_btn.setText('Checking connections ...')
            self.check_pvs_btn.setEnabled(False)
            for line_edit in self.mea_pv_names:
                line_edit.setEnabled(False)
            self.obj_name_cb.setEnabled(False)
        else:
            self.check_pvs_btn.setText(self.check_pvs_btn_default_text)
            self.check_pvs_btn.setEnabled(True)
            for line_edit in self.mea_pv_names:
                line_edit.setEnabled(True)
            self.obj_name_cb.setEnabled(True)

    def start_measurement_pvs_check(self, on_add_config: bool = False):
        """
        Check all line edits. If no text, skip. If text, take PV name (should accept both FULL and PARTIAL names).
        Starts the PV connection check thread.
        For each PV, thread tries to connect and get value. If success, change label and set green,
        if timeout set red etc.
        While loading, change label text or add loading animation

        Args:
            on_add_config (bool): Whether to emit the signal to add configuration on finish or not.
                This is used when the check is started automatically by the Add Configuration button,
                if automatic PV check is enabled in general settings.
        """
        names = []
        for pv_name in self.mea_pv_names:
            name = pv_name.text()
            if name:
                full_name = get_full_pv_name(name)
                names.append(full_name)
            else:
                names.append(None)
        self.pvs_connection_thread.on_add_config(on_add_config)
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
        self.settings_changed(True)
        self.enable_or_disable_check_pvs_btn()
        self.message_lbl.clear()

    def enable_or_disable_check_pvs_btn(self):
        self.check_pvs_btn.setEnabled(False)
        for line_edit in self.mea_pv_names:
            if line_edit.text():
                self.check_pvs_btn.setEnabled(True)
                break

    def pvs_connection_check_started(self):
        self.update_check_pvs_widgets(pvs_check_running=True)
        self.clear_pvs_connection_status()
        self.ok_btn.setEnabled(False)
        self.message_lbl.setText('Checking measurement PVs ...')
        self.message_lbl.setStyleSheet('color: green;')

    def pvs_connection_check_finished(self):
        self.update_check_pvs_widgets(pvs_check_running=False)
        self.ok_btn.setEnabled(True)

        results = self.pvs_connection_thread.results
        failed_pvs = len(results['failed'])
        if not failed_pvs:
            self.message_lbl.setStyleSheet('color: green;')
            self.message_lbl.setText('PV connection test finished.\n'
                                     'All PVs connected.')
        else:
            self.message_lbl.setStyleSheet('color: red;')
            self.message_lbl.setText('PV connection test finished.\n'
                                     f'{failed_pvs} PVs failed to connect.')

    # endregion Measurement PVs


class CustomSignals(QObject):
    serviceUpdated = pyqtSignal()


class ObjectNameCBFilter(QObject):
    focusOut = pyqtSignal()
    focusIn = pyqtSignal()

    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QEvent.FocusOut:
            # Custom actions
            self.focusOut.emit()
        elif event.type() == QEvent.FocusIn:
            self.focusIn.emit()

        # return False so that the widget will also handle the event
        return False


class CheckPVsThread(QThread):
    mea_status_update = pyqtSignal(int, bool)
    progress_bar_update = pyqtSignal(int)
    display_progress_bar = pyqtSignal(bool)
    finished_check_before_add_config = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.finished.connect(self.clear_progress_bar)
        self.finished.connect(lambda: self.finished_check_before_add_config.emit() if self._on_add_config else None)
        self.pv_names = None
        self._running = None
        self.results = None

        # Whether to emit the signal to add configuration on finish or not. This is used
        # when the check is started automatically by the Add Configuration button, if
        # automatic PV check is enabled in general settings.
        self._on_add_config = None

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

            self.progress_bar_update.emit(index + 1)

        if self._running:
            logger.info(f'PV connection check finished. Connected: {connected}. Failed: {failed}')

        self.results = {'connected': connected, 'failed': failed}

    def set_pv_names(self, pv_names: list):
        self.pv_names = pv_names

    def clear_progress_bar(self):
        self.progress_bar_update.emit(0)
        self.display_progress_bar.emit(False)

    def on_add_config(self, add_config_clicked: bool):
        self._on_add_config = add_config_clicked


class LoadingPopupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(210, 100)
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        layout = QHBoxLayout()

        self.label_msg = QLabel()
        self.label_msg.setText('Checking PVs ...')
        font = QFont()
        font.setPointSize(10)
        self.label_msg.setFont(font)

        self.load_animation_lbl = QLabel()
        self.movie = QMovie(loading_animation)
        self.load_animation_lbl.setMovie(self.movie)

        size = QSize(50, 50)
        self.movie.setScaledSize(size)

        layout.addWidget(self.load_animation_lbl)
        layout.addWidget(self.label_msg)

        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setGeometry(self.geometry())
        frame.setLayout(layout)

    def showEvent(self, e: QShowEvent):
        self.movie.start()

    def closeEvent(self, e: QCloseEvent):
        self.movie.stop()


class OverwriteMessageBox(QMessageBox):
    def __init__(self, object_name, object_id):
        super().__init__()

        self.setWindowTitle('Configuration already exists')
        self.setText(f'{object_name} (ID: {object_id}) already has a PV configuration.\n'
                     f'Overwrite existing configuration?')
        self.setIcon(QMessageBox.Warning)
        self.addButton(QMessageBox.Ok)
        ok_btn = self.button(QMessageBox.Ok)
        ok_btn.setText('Overwrite')
        self.addButton(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)
