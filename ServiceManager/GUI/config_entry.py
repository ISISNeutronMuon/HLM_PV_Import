from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QThread, Qt, QSize
from PyQt5.QtGui import QShowEvent, QCloseEvent, QFont, QMovie
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QFrame, \
    QComboBox, QLabel, QProgressBar, QSpinBox, QMessageBox, QApplication, QHBoxLayout, QWidget
from PyQt5 import uic

from ServiceManager.constants import config_entry_ui, loading_animation
from ServiceManager.settings import Settings, get_full_pv_name
from ServiceManager.utilities import get_pv_value
from ServiceManager.db_utilities import DBUtils, DBUtilsObjectNameAlreadyExists
from ServiceManager.logger import logger

from caproto import CaprotoTimeoutError


class UIConfigEntryDialog(QDialog):
    config_updated = pyqtSignal()

    def __init__(self):
        super(UIConfigEntryDialog, self).__init__()
        uic.loadUi(uifile=config_entry_ui, baseinstance=self)

        # region Attributes
        self.last_details_update_obj = None         # Name of object whose details were last updated and displayed
        self.check_pvs_btn_default_text = None      # Default text of the Check PVs button (For "Loading ...")
        self.loading_msg = LoadingPopupWindow()     # Loading splash screen when testing PV connection
        self.pv_check_obj_id = None                 # For PV auto-check. Save object ID and whether it already exists
        self.pv_check_obj_already_exists = None     # before starting the connection test thread.
        self.existing_config_frame_visible = None   # For alternating between the Load config and PV check progress bar
        self.existing_config_pvs = {}               # Store existing object config measurement PVs when 'Load' clicked
        self.type_and_comment_updated = False       # If the object type and comment were updated by an existing object
        # endregion

        # region Get widgets
        self.obj_name_label = self.findChild(QLabel, 'objectNameLabel')
        self.obj_name_cb = self.findChild(QComboBox, 'objectNameCB')
        self.obj_name_cb.lineEdit().setPlaceholderText('Enter new object name or select existing')
        self.obj_name_cb.setInsertPolicy(QComboBox.NoInsert)
        self.obj_name_frame = self.findChild(QFrame, 'objectNameFrame')
        self.log_interval_sb = self.findChild(QSpinBox, 'logIntervalSpinBox')
        self.obj_type_cb = self.findChild(QComboBox, 'objectTypeCB')
        self.obj_type_frame = self.findChild(QFrame, 'objectTypeFrame')
        self.obj_comment = self.findChild(QLineEdit, 'objectCommentLineEdit')

        self.obj_details_btn = self.findChild(QPushButton, 'objectDetailsButton')
        self.obj_details_btn.setAutoDefault(False)
        self.obj_details_frame = self.findChild(QFrame, 'detailsFrame')
        self.obj_details_frame.showEvent = lambda x: self.obj_details_btn.setText('Hide details')
        self.obj_details_frame.hideEvent = lambda x: self.obj_details_btn.setText('Show details')
        self.obj_detail_name = self.findChild(QLineEdit, 'objectNameDetailsLineEdit')
        self.obj_detail_id = self.findChild(QLineEdit, 'objectIdLineEdit')
        self.obj_detail_class = self.findChild(QLineEdit, 'objectClassLineEdit')
        self.obj_detail_func = self.findChild(QLineEdit, 'objectFunctionLineEdit')
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

        self.existing_config_frame = self.findChild(QFrame, 'existingConfigFrame')
        self.existing_config_frame.hide()
        self.existing_config_load_btn = self.findChild(QPushButton, 'loadExistingConfigButton')
        self.existing_config_load_btn.setEnabled(False)
        self.check_pvs_progress_bar = self.findChild(QProgressBar, 'checkMeasProgressBar')
        self.check_pvs_progress_bar.hide()
        self.check_pvs_btn = self.findChild(QPushButton, 'checkPvsButton')
        self.check_pvs_btn_default_text = self.check_pvs_btn.text()

        self.message_lbl = self.findChild(QLabel, 'message_lbl')

        self.ok_btn = self.findChild(QPushButton, 'dialog_btn_ok')
        self.cancel_btn = self.findChild(QPushButton, 'dialog_btn_cancel')
        self.delete_btn = self.findChild(QPushButton, 'dialog_btn_delete')
        # endregion

        # region Signals & Slots
        self.obj_name_cb.currentIndexChanged.connect(self.update_data)
        self.obj_name_cb.lineEdit().returnPressed.connect(self.update_data)
        self.obj_name_cb.lineEdit().textChanged.connect(lambda: self.set_red_border(self.obj_name_frame, False))
        self.object_name_filter = ObjectNameCBFilter()                  # instantiate event filter with custom signals
        self.object_name_filter.focusOut.connect(self.update_data)      # connect filter custom signal to slot
        self.obj_name_cb.installEventFilter(self.object_name_filter)    # install filter to widget

        self.obj_type_cb.currentTextChanged.connect(self.message_lbl.clear)
        self.obj_type_cb.currentTextChanged.connect(lambda: self.set_red_border(self.obj_type_frame, False))

        self.obj_details_btn.clicked.connect(self.toggle_details_frame)

        # Connect signals for each measurement PV name line edit
        for index, mea_pv_name in enumerate(self.mea_pv_names):
            mea_pv_name.textChanged.connect(lambda _, i=index: self.on_mea_pv_text_change(i))
            # If any PV name has been changed, if the load existing config frame is visible, enable the load button
            # and update its text. (Disabled, 'Loaded' --> Enabled, 'Load')
            mea_pv_name.textEdited.connect(self.update_load_existing_config_btn)

        self.existing_config_load_btn.clicked.connect(self.load_existing_config_pvs)

        self.progress_bar_filter = ProgressBarFilter()
        self.progress_bar_filter.showEventSignal.connect(self.on_progress_bar_show_event)
        self.progress_bar_filter.hideEventSignal.connect(self.on_progress_bar_hide_event)
        self.check_pvs_progress_bar.installEventFilter(self.progress_bar_filter)

        self.check_pvs_btn.clicked.connect(self.start_measurement_pvs_check)

        self.ok_btn.clicked.connect(self.on_accepted)
        self.cancel_btn.clicked.connect(self.on_cancel)
        self.delete_btn.clicked.connect(self.on_delete)
        # endregion

        # region Thread - PV Connection Check
        self.pvs_connection_thread = CheckPVsThread()
        self.pvs_connection_thread.mea_status_update.connect(self.update_measurements_pvs_status)
        self.pvs_connection_thread.display_progress_bar.connect(lambda x: self.check_pvs_progress_bar.setVisible(x))
        self.pvs_connection_thread.progress_bar_update.connect(lambda val: self.check_pvs_progress_bar.setValue(val))
        self.pvs_connection_thread.started.connect(self.pvs_connection_check_started)
        self.pvs_connection_thread.finished.connect(self.pvs_connection_check_finished)
        self.pvs_connection_thread.finished_check_before_add_config.connect(self.add_entry_pv_check_finished)
        QApplication.instance().aboutToQuit.connect(self.pvs_connection_thread.stop)  # graceful exit on app close
        # endregion

    # region Show & Close Events
    def showEvent(self, e: QShowEvent):
        self.update_fields()

    def closeEvent(self, e: QCloseEvent):
        self.pvs_connection_thread.stop()
        self.loading_msg.close()

    # endregion

    # region Widget refresh & updates
    def update_fields(self):
        self.obj_name_cb.clear()
        self.obj_name_cb.lineEdit().clear()
        self.obj_name_cb.addItem(None)
        self.obj_name_cb.addItems(DBUtils.get_all_object_names())

        self.obj_type_cb.clear()
        self.obj_type_cb.addItem(None)
        self.obj_type_cb.addItems(DBUtils.get_all_type_names())

        self.log_interval_sb.setValue(Settings.Manager.get_default_meas_update_interval())

        self.obj_comment.clear()

        self.clear_details()
        self.clear_pvs_connection_status()
        self.clear_measurement_type_labels()
        self.clear_measurement_pv_names()

        self.enable_or_disable_check_pvs_btn()

        self.existing_config_frame.hide()
        self.existing_config_load_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.message_lbl.clear()
        self.set_red_border(self.obj_name_frame, False)
        self.set_red_border(self.obj_type_frame, False)
        self.set_red_border(self.mea_pvs_frame, False)
    # endregion

    # region Accept, Reject, Save
    def on_accepted(self):
        """
        Check if the object name is given and measurements have at least one PV.
        Gets the object name from the LineEdit and fetches its ID from the DB.
        If ID is found, check if it already has an entry in the PV config. If it exists, show message box to confirm
        overwriting or cancelling.
        If ID is not found, enable the Type and Comment lines to be edited. An object can be created with the type
        and comment (optional) after confirming object creation.

        If auto-check PVs is enabled, run the PV connection test thread, and continue after the thread finished signal
        is emitted. If any PVs fail to connect, display warning, with the option or cancelling, or adding config anyway
        which will call the final add_entry method.
        If auto-check is not enabled, call add_entry directly.
        """
        self.update_data(update_meas_pvs=False)

        # Validate and display invalid input message + red highlight relevant frames if invalid
        if not self.object_name_and_measurement_pv_provided():
            return

        object_name = self.obj_name_cb.lineEdit().text()
        object_id = DBUtils.get_object_id(object_name)

        # If object with the given name was not found in the database, ask whether to create a new one
        if not object_id:
            type_name = self.obj_type_cb.currentText()
            if not type_name:
                self.set_message_colored_text(f'Object type is required.', 'red')
                self.set_red_border(self.obj_type_frame)
                return

            type_id = DBUtils.get_type_id(type_name=type_name)
            if not type_id:
                self.set_message_colored_text(f'Type "{type_name}" was not found.', 'red')
                self.set_red_border(self.obj_type_frame)
                return

            msg_box = QMessageBox.question(self, 'Create new object',
                                           f'Create new object "{object_name}" with type "{type_name}" '
                                           f'and save the PV configuration?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if msg_box != QMessageBox.Yes:
                return

            comment = self.obj_comment.text()

            try:
                DBUtils.add_object(object_name, type_id, comment)
            except DBUtilsObjectNameAlreadyExists:
                self.set_message_colored_text(f'Object "{object_name}" already exists in the database.', 'red')
                self.set_red_border(self.obj_name_frame)
                return

            # Update the ID with that of the newly created object
            object_id = DBUtils.get_object_id(object_name)

            # If the object is a Vessel, Cryostat or Gas Counter, create a Software Level Device and make relation
            class_id = DBUtils.get_class_id(type_id)
            # Class ID: Vessel = 2, Cryostat = 4, Gas Counter = 7. SLD Type ID: 18
            if class_id in [2, 4, 7]:
                # add SLD
                sld_name = f'SLD "{object_name}" (ID: {object_id})'
                sld_comment = f'Software Level Device for {type_name} "{object_name}" (ID: {object_id})'
                sld_type_id = 18
                DBUtils.add_object(name=sld_name, type_id=sld_type_id, comment=sld_comment)
                # make relation
                sld_id = DBUtils.get_object_id(object_name=sld_name)
                DBUtils.add_relation(or_object_id=object_id, or_object_id_assigned=sld_id)

        # Check if object already has a PV configuration (worth checking even for objects not in the DB before)
        existing_ids = Settings.Service.PVConfig.get_entry_object_ids()
        already_exists = False
        if object_id in existing_ids:  # if it does already have a config, ask if overwrite
            already_exists = True
            msg_box = OverwriteMessageBox(object_name, object_id)
            resp = msg_box.exec()
            if resp != QMessageBox.Ok:
                return

        # Test PV connections if auto-check is enabled, by starting the PV check thread. Once finished, it will emit
        # a signal to be picked by the main thread that will call the add_entry method.
        # If the auto-check is disabled, add entry directly.
        auto_pv_check_enabled = Settings.Manager.get_new_entry_auto_pv_check()
        if auto_pv_check_enabled:
            self.pv_check_obj_id = object_id                        # Store the object ID and whether it already has
            self.pv_check_obj_already_exists = already_exists       # a config. To be used after check thread finishes.
            self.start_measurement_pvs_check(on_add_config=True)
            self.loading_msg.show()
        else:
            self.add_entry(object_id=object_id, overwrite=already_exists)

    def add_entry_pv_check_finished(self):
        """
        Trigger once the PV connection check thread has finished. Check if there are any PVs that failed to connect,
        and if so, display warning ask if cancel entry addition or add anyway. If all PVs successfully connected or
        user decides to add anyway, call add_entry.
        """
        self.loading_msg.close()
        failed_connections = self.pvs_connection_thread.results['failed']
        if failed_connections:
            msg_box = QMessageBox.warning(self, 'PV Connection Failed',
                                          'Could not establish connection to one or more PVs.\n'
                                          'Add configuration anyway? (not recommended)',
                                          QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if msg_box == QMessageBox.Yes:
                self.add_entry(object_id=self.pv_check_obj_id, overwrite=self.pv_check_obj_already_exists)

    def add_entry(self, object_id: int, overwrite: bool):
        """
        Prepare the config data and add a new PV config entry or overwrite an existing one.

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
            self.set_message_colored_text('Configuration has been updated.', 'green')
        else:
            Settings.Service.PVConfig.add_entry(config_data)
            self.set_message_colored_text('New configuration has been added.', 'green')

        self.config_updated.emit()
        self.clear_pvs_connection_status()

    def object_name_and_measurement_pv_provided(self):
        """
        Check if object name and at least one measurement PV name is provided.
        If not, highlight relevant frames with a red border and display the error message.

        Returns:
            (bool): True if input is valid, False if not.
        """
        input_valid = True
        # if no object name
        if not self.obj_name_cb.lineEdit().text():
            self.set_message_colored_text('Object name is required.\n', 'red')
            self.set_red_border(self.obj_name_frame)
            input_valid = False

        measurements_have_pv = False
        for line_edit in self.mea_pv_names:
            if line_edit.text():
                measurements_have_pv = True
                break

        if not measurements_have_pv:
            self.set_message_colored_text(f'{self.message_lbl.text()}At least one measurement is required.\n', 'red')
            self.set_red_border(self.mea_pvs_frame)
            input_valid = False

        return input_valid

    def on_cancel(self):
        self.close()

    def on_delete(self):
        """
        Delete the PV configuration of the current object.
        """
        object_name = self.obj_name_cb.lineEdit().text()
        object_id = DBUtils.get_object_id(object_name)

        if not object_id:
            self.set_message_colored_text(f'Object ID for "{object_name}" was not found.', 'red')
            self.set_red_border(self.obj_name_frame)

        if object_id not in Settings.Service.PVConfig.get_entry_object_ids():
            self.set_message_colored_text(
                f'Object "{object_name}" with ID {object_id} does not have a PV configuration.', 'red'
            )
            self.set_red_border(self.obj_name_frame)

        msg_box = ConfigDeleteMessageBox(object_name, object_id)
        resp = msg_box.exec()

        if resp == QMessageBox.Ok:
            Settings.Service.PVConfig.delete_entry(object_id)
            self.config_updated.emit()
            self.delete_btn.setEnabled(False)

    # endregion

    # region Object & Config Data
    def toggle_details_frame(self):
        """ Show or Hide the details frame. """
        if self.obj_details_frame.isHidden():
            self.obj_details_frame.show()
        else:
            self.obj_details_frame.hide()

    def clear_details(self):
        """
        Clear the object details, and if the type and comment were last updated by selecting an existing object,
        clear them as well.
        """
        if self.type_and_comment_updated:
            self.obj_type_cb.setCurrentIndex(0)
            self.obj_comment.clear()
            self.type_and_comment_updated = False

        self.obj_detail_name.clear()
        self.obj_detail_id.clear()
        self.obj_detail_class.clear()
        self.obj_detail_func.clear()

        self.obj_detail_sdl_name.clear()
        self.obj_detail_sdl_id.clear()

        self.last_details_update_obj = None

    def update_data(self, update_meas_pvs: bool = True):
        """
        Update object details, show existing config frame if exists and load it if auto-load config is enabled.
        Disable and update type & comment if object is found in the DB, otherwise clear & enable editing
        for object creation.

        Args:
            update_meas_pvs (bool): Update measurement PVs if auto-load config is enabled. If False, don't update, even
                if auto-load is enabled in the settings.
        """
        current_object = self.obj_name_cb.currentText()
        # If object data already displayed, return
        if current_object == self.last_details_update_obj:
            return

        if not current_object:
            self.clear_details()
            self.obj_type_cb.setEnabled(True)
            self.obj_comment.setEnabled(True)
            return

        self.clear_details()
        self.message_lbl.clear()

        obj_id = DBUtils.get_object_id(current_object)  # search for object in DB
        if obj_id:
            self.obj_type_cb.setEnabled(False)
            self.obj_comment.setEnabled(False)
        else:
            self.obj_type_cb.setEnabled(True)
            self.obj_comment.setEnabled(True)

            return

        self.update_details(obj_id, current_object)

        if update_meas_pvs:
            if Settings.Manager.get_auto_load_existing_config():    # If existing config auto-load setting is enabled
                self.clear_measurement_pv_names()                   # clear the PV names before updating
            self.check_for_existing_config_pvs(obj_id)

    def update_details(self, obj_id: int, current_object: str):
        """ Fetches the object record data and updates the details widgets with it. """
        obj_record = DBUtils.get_object(obj_id)
        obj_class_record = DBUtils.get_object_class(object_id=obj_id)

        self.obj_comment.setText(obj_record[0][4])
        self.obj_type_cb.setCurrentText(DBUtils.get_object_type(object_id=obj_id, name_only=True))
        self.type_and_comment_updated = True

        self.obj_detail_name.setText(DBUtils.get_object_name(obj_id))
        self.obj_detail_id.setText(f'{obj_id}')
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

    def check_for_existing_config_pvs(self, obj_id: int):
        """ Check if a PV config with the given object already exists, and if it does, display config load frame. """
        obj_entry = Settings.Service.PVConfig.get_entry_with_id(obj_id)
        if not obj_entry:
            self.existing_config_frame.hide()
            self.existing_config_load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        self.existing_config_pvs = obj_entry[Settings.Service.PVConfig.MEAS]
        self.delete_btn.setEnabled(True)

        if self.existing_config_pvs:
            self.existing_config_frame.show()
            self.existing_config_load_btn.setEnabled(True)
            self.existing_config_load_btn.setText('Load')

            auto_load_setting = Settings.Manager.get_auto_load_existing_config()
            if auto_load_setting:                       # If existing config auto-load setting is enabled
                self.load_existing_config_pvs()         # update all PV names.

        else:
            self.existing_config_frame.hide()
            self.existing_config_load_btn.setEnabled(False)

    def load_existing_config_pvs(self):
        """ Update the measurement PV names with those from the existing config. """
        for index, pv_name_line_edit in enumerate(self.mea_pv_names):
            try:
                pv_name_line_edit.setText(self.existing_config_pvs[f'{index + 1}'])
            except KeyError:
                continue
        self.existing_config_load_btn.setText('Loaded')
        self.existing_config_load_btn.setEnabled(False)

    # endregion

    # region Measurement PVs & CA Connection Check
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

    def disable_widgets_if_pv_check_running(self, pvs_check_running: bool):
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
        """ Update the PVs status with the connection test results. """
        status_lbl = self.mea_status_labels[index]
        if connected:
            status_lbl.setText('OK')
            status_lbl.setStyleSheet('color: green;')
        else:
            status_lbl.setText('ERR')
            status_lbl.setStyleSheet('color: red;')

    def on_progress_bar_show_event(self):
        if self.existing_config_frame.isVisible():
            self.existing_config_frame_visible = True
            self.existing_config_frame.setVisible(False)

    def on_progress_bar_hide_event(self):
        if self.existing_config_frame_visible:
            self.existing_config_frame.setVisible(True)

    def on_mea_pv_text_change(self, mea_no: int):
        """
        Clears the measurement PV name status of the given QLineEdit index.
        Enables the check PVs button as long as there is one PV name in the measurement QLineEdits.
        Clears the message.
        Clears the red-highlight of the Mea. PVs frame.
        """
        self.mea_status_labels[mea_no].clear()
        self.enable_or_disable_check_pvs_btn()
        self.message_lbl.clear()
        self.set_red_border(self.mea_pvs_frame, False)

    def update_load_existing_config_btn(self):
        if self.existing_config_frame.isVisible():
            self.existing_config_load_btn.setText('Load')
            self.existing_config_load_btn.setEnabled(True)

    def enable_or_disable_check_pvs_btn(self):
        self.check_pvs_btn.setEnabled(False)
        for line_edit in self.mea_pv_names:
            if line_edit.text():
                self.check_pvs_btn.setEnabled(True)
                break

    def pvs_connection_check_started(self):
        self.disable_widgets_if_pv_check_running(pvs_check_running=True)
        self.clear_pvs_connection_status()
        self.ok_btn.setEnabled(False)
        self.log_interval_sb.setEnabled(False)
        self.set_message_colored_text('Checking measurement PVs ...', 'green')

    def pvs_connection_check_finished(self):
        self.disable_widgets_if_pv_check_running(pvs_check_running=False)
        self.ok_btn.setEnabled(True)
        self.log_interval_sb.setEnabled(True)

        results = self.pvs_connection_thread.results
        failed_pvs = len(results['failed'])
        if not failed_pvs:
            self.set_message_colored_text('PV connection test finished.\nAll PVs connected.', 'green')
        else:
            self.set_message_colored_text(f'PV connection test finished.\n{failed_pvs} PVs failed to connect.', 'red')

    # endregion

    # region Utilities & Other
    def edit_object_config(self, obj_name: str):
        """ Starts editing an object by loading its details and PV config. """
        self.obj_name_cb.lineEdit().setText(obj_name)
        self.update_data()
        self.load_existing_config_pvs()

    def set_message_colored_text(self, msg: str, color: str):
        self.message_lbl.setText(msg)
        self.message_lbl.setStyleSheet(f'color: {color};')

    @staticmethod
    def set_red_border(frame: QObject, highlight: bool = True):
        if highlight:
            frame.setStyleSheet(f'QObject#{frame.objectName()} {{border: 1px solid red;}}')
        else:
            frame.setStyleSheet(f'QObject#{frame.objectName()} {{}}')
    # endregion


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


class ProgressBarFilter(QObject):
    showEventSignal = pyqtSignal()
    hideEventSignal = pyqtSignal()

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Show:
            self.showEventSignal.emit()
        elif event.type() == QEvent.Hide:
            self.hideEventSignal.emit()

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
    def __init__(self, object_name: str, object_id: int):
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


class ConfigDeleteMessageBox(QMessageBox):
    def __init__(self, object_name: str, object_id: int):
        super().__init__()

        self.setWindowTitle('Delete configuration')
        self.setText(f'Deleting configuration for {object_name} (ID: {object_id}).\n'
                     f'Are you sure?')
        self.setIcon(QMessageBox.Warning)
        self.addButton(QMessageBox.Ok)
        ok_btn = self.button(QMessageBox.Ok)
        ok_btn.setText('Delete')
        self.addButton(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)
