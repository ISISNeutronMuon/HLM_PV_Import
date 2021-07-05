from PyQt5.QtWidgets import QDialog, QApplication, QLineEdit
from PyQt5 import uic

from ServiceManager.constants import config_entry_ui
from ServiceManager.settings import Settings
from ServiceManager.utilities import set_red_border
from ServiceManager.db_func import *
from ServiceManager.GUI.config_entry_utils import *


class UIConfigEntryDialog(QDialog):
    config_updated = pyqtSignal()

    def __init__(self):
        super(UIConfigEntryDialog, self).__init__()
        uic.loadUi(uifile=config_entry_ui, baseinstance=self)  # Load the UI file and its widgets

        # region Attributes
        self.last_details_update_obj = None  # Name of object whose details were last updated and displayed
        self.loading_msg = LoadingPopupWindow()  # Loading splash screen when testing PV connection
        self.pv_check_obj_id = None  # For PV auto-check. Save object ID and whether it already exists
        self.pv_check_obj_already_exists = None  # before starting the connection test thread.
        self.existing_config_pvs = {}  # Store existing object config measurement PVs when 'Load' clicked
        self.type_and_comment_updated = False  # If the object type and comment were updated by an existing object

        # Default text of the Check PVs button ("Loading ...")
        self.check_pvs_btn_default_text = self.check_pvs_btn.text()
        # endregion

        # region Widget Setup - things that can't be done in QtDesigner
        self.obj_name_cb.lineEdit().setPlaceholderText('Enter new object name or select existing')

        self.mea_widgets = [
            (self.mea_pv_name_1, self.mea_type_lbl_1, self.mea_status_lbl_1),
            (self.mea_pv_name_2, self.mea_type_lbl_2, self.mea_status_lbl_2),
            (self.mea_pv_name_3, self.mea_type_lbl_3, self.mea_status_lbl_3),
            (self.mea_pv_name_4, self.mea_type_lbl_4, self.mea_status_lbl_4),
            (self.mea_pv_name_5, self.mea_type_lbl_5, self.mea_status_lbl_5),
        ]

        self.existing_config_frame.hide()
        self.existing_config_load_btn.setEnabled(False)
        self.check_pvs_progress_bar.hide()
        # endregion

        # region Signals & Slots
        self.obj_details_frame.showEvent = lambda x: self.obj_details_btn.setText('Hide details')
        self.obj_details_frame.hideEvent = lambda x: self.obj_details_btn.setText('Show details')

        self.obj_name_cb.currentIndexChanged.connect(self.load_object_data)
        self.obj_name_cb.lineEdit().returnPressed.connect(self.load_object_data)
        self.obj_name_cb.lineEdit().textChanged.connect(lambda: set_red_border(self.obj_name_frame, False))
        self.obj_name_cb.lineEdit().textChanged.connect(self.check_for_existing_config_pvs)
        self.obj_name_cb.lineEdit().textChanged.connect(self.load_object_data)
        self.object_name_filter = ObjectNameCBFilter()  # instantiate event filter with custom signals
        self.object_name_filter.focusOut.connect(self.load_object_data)  # connect filter custom signal to slot
        self.obj_name_cb.installEventFilter(self.object_name_filter)  # install filter to widget

        self.obj_type_cb.currentTextChanged.connect(self.message_lbl.clear)
        self.obj_type_cb.currentTextChanged.connect(lambda: set_red_border(self.obj_type_frame, False))
        self.obj_type_cb.currentTextChanged.connect(self.update_measurement_types)

        self.obj_details_btn.clicked.connect(self.toggle_details_frame)

        # Connect signals for each measurement PV name line edit
        for mea in self.mea_widgets:
            # Need to bind mea for each function created (x=mea), otherwise only last mea will be affected
            mea[0].textChanged.connect(lambda _, x=mea: self.on_mea_pv_text_change(x))
            # If any PV name has been changed, if the load existing config frame is visible, enable the load button
            # and update its text. (Disabled, 'Loaded' --> Enabled, 'Load')
            mea[0].textEdited.connect(self.update_load_existing_config_btn)

        self.existing_config_load_btn.clicked.connect(self.load_existing_config_pvs)

        self.check_pvs_progress_bar.showEvent = self.on_progress_bar_show_event
        self.check_pvs_progress_bar.hideEvent = self.on_progress_bar_hide_event

        self.check_pvs_btn.clicked.connect(self.start_measurement_pvs_check)

        self.ok_btn.clicked.connect(self.on_accepted)
        self.cancel_btn.clicked.connect(self.close)
        self.delete_btn.clicked.connect(self.on_delete)
        # endregion

        # region Thread - PV Connection Check
        self.pvs_connection_thread = CheckPVsThread()
        self.pvs_connection_thread.mea_status_update.connect(self.update_measurements_pvs_status)
        self.pvs_connection_thread.display_progress_bar.connect(lambda x: self.check_pvs_progress_bar.setVisible(x))
        self.pvs_connection_thread.progress_bar_update.connect(lambda val: self.check_pvs_progress_bar.setValue(val))
        self.pvs_connection_thread.started.connect(self.pvs_connection_check_started)
        self.pvs_connection_thread.finished_check.connect(lambda x: self.pvs_connection_check_finished(x))
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
    def add_items_to_cb(self):
        self.obj_name_cb.clear()
        self.obj_name_cb.lineEdit().clear()
        self.obj_name_cb.addItem(None)
        try:
            self.obj_name_cb.addItems(get_all_object_names())
        except TypeError:
            pass

        self.obj_type_cb.clear()
        self.obj_type_cb.addItem(None)
        try:
            self.obj_type_cb.addItems(get_all_type_names())
        except TypeError:
            pass

    def update_fields(self):
        self.add_items_to_cb()
        self.log_interval_sb.setValue(Settings.Manager.default_update_interval)
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
        set_red_border(self.obj_name_frame, False)
        set_red_border(self.obj_type_frame, False)
        set_red_border(self.mea_pvs_frame, False)

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
        # Validate and display invalid input message + red highlight relevant frames if invalid
        if not self.validate():
            return

        object_name = self.obj_name_cb.lineEdit().text()
        object_id = get_object_id(object_name)

        # If object with the given name was not found in the database, ask whether to create a new one
        if not object_id:
            type_name = self.obj_type_cb.currentText()
            type_id = get_type_id(type_name=type_name)

            msg_box = QMessageBox.question(self, 'Create new object',
                                           f'Create new object "{object_name}" with type "{type_name}" '
                                           f'and save the PV configuration?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if msg_box != QMessageBox.Yes:
                return

            try:
                object_id = add_object(object_name, type_id, self.obj_comment.text())
                create_sld_if_required(object_id=object_id, object_name=object_name,
                                       type_name=type_name, class_id=get_class_id(type_id))
            except DBObjectNameAlreadyExists:
                self.set_message_colored_text(f'Object "{object_name}" already exists in the database.', 'red')
                set_red_border(self.obj_name_frame)
                return
            except Exception as e:
                manager_logger.error(f'Exception occurred when adding new object to DB, aborting PV Config entry '
                                     f'creation: {e}')
                return

        # Check if object already has a PV configuration (worth checking even for objects not in the DB)
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
        auto_pv_check_enabled = Settings.Manager.auto_pv_check
        if auto_pv_check_enabled:
            self.pv_check_obj_id = object_id  # Store the object ID and whether it already has
            self.pv_check_obj_already_exists = already_exists  # a config. To be used after check thread finishes.
            self.start_measurement_pvs_check(add_entry_after_check=True)
            self.loading_msg.show()
        else:
            self.add_entry(object_id=object_id, overwrite=already_exists)

    def add_entry(self, object_id: int, overwrite: bool):
        """
        Prepare the config data and add a new PV config entry or overwrite an existing one.

        Args:
            object_id (int): The object ID.
            overwrite (bool): If object already has config, overwrite entry. If False, append as normal.
        """
        log_period = self.log_interval_sb.value()
        mea_pv_names = [mea[0].text() for mea in self.mea_widgets]
        measurement_pvs = {}
        for index, pv_name in enumerate(mea_pv_names):
            measurement_pvs[f'{index + 1}'] = Settings.Service.CA.get_short_pv_name(pv_name) if pv_name else None

        config_data = {
            Settings.Service.PVConfig.OBJ: object_id,
            Settings.Service.PVConfig.LOG_PERIOD: log_period,
            Settings.Service.PVConfig.MEAS: measurement_pvs
        }

        if overwrite:
            Settings.Service.PVConfig.add_entry(config_data, overwrite=True)
            self.check_for_existing_config_pvs(object_id)
            self.set_message_colored_text('Configuration has been updated.', 'green')
        else:
            Settings.Service.PVConfig.add_entry(config_data)
            self.update_fields()
            self.set_message_colored_text('New configuration has been added.', 'green')

        self.config_updated.emit()
        self.clear_pvs_connection_status()

    def validate(self):
        """
        Check if object name, type, and at least one measurement PV name is provided.
        If not, highlight relevant frames with a red border and display the error message.

        Returns:
            (bool): True if input is valid, False if not.
        """

        def _set_invalid(msg: str, frame: QFrame):
            self.set_message_colored_text(f'{self.message_lbl.text()}{msg}\n', 'red')
            set_red_border(frame)
            return False

        input_valid = True
        object_name_max_length = 50
        self.message_lbl.clear()

        # check object type
        type_name = self.obj_type_cb.currentText()
        if not type_name:
            input_valid = _set_invalid('Object type is required.', self.obj_type_frame)
        else:
            type_id = get_type_id(type_name=type_name)
            if not type_id:
                input_valid = _set_invalid(f'Type "{type_name}" was not found.', self.obj_type_frame)
            else:
                class_id = get_class_id(type_id=type_id)
                if class_id in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT, DBClassIDs.GAS_COUNTER]:
                    # if object will have an SLD, lower max name length to make space for the SLD object name formatting
                    object_name_max_length -= len(generate_sld_name(object_name="", object_id=get_max_object_id() + 1))

        # check object name
        if not self.obj_name_cb.lineEdit().text():
            input_valid = _set_invalid('Object name is required.', self.obj_name_frame)
        else:
            if len(self.obj_name_cb.lineEdit().text()) > object_name_max_length:
                input_valid = _set_invalid('Object name is too long. Max length for this object is: {}'
                                           .format(object_name_max_length), self.obj_name_frame)

        # check measurement pv names
        if not any(mea[0].text() for mea in self.mea_widgets):
            input_valid = _set_invalid('At least one measurement is required.', self.mea_pvs_frame)

        return input_valid

    def on_delete(self):
        """
        Delete the PV configuration of the current object.
        """
        object_name = self.obj_name_cb.lineEdit().text()
        object_id = get_object_id(object_name)

        if not object_id:
            self.set_message_colored_text(f'Object ID for "{object_name}" was not found.', 'red')
            set_red_border(self.obj_name_frame)

        if object_id not in Settings.Service.PVConfig.get_entry_object_ids():
            self.set_message_colored_text(
                f'Object "{object_name}" with ID {object_id} does not have a PV configuration.', 'red'
            )
            set_red_border(self.obj_name_frame)

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
        self.obj_details_frame.setVisible(not self.obj_details_frame.isVisible())

    def clear_details(self):
        """
        Clear the object details, and if the type and comment were last updated by selecting an existing object,
        clear them as well.
        """
        if self.type_and_comment_updated:
            self.obj_type_cb.setCurrentIndex(0)
            self.obj_comment.clear()
            self.type_and_comment_updated = False

        for line_edit in self.obj_details_frame.findChildren(QLineEdit):
            line_edit.clear()

        self.last_details_update_obj = None

    def load_object_data(self, update_meas_pvs: bool = True):
        """
        Update object details, show existing config frame if exists and load it if auto-load config is enabled.
        Disable and update type & comment if object is found in the DB, otherwise clear & enable editing
        for object creation.

        Args:
            update_meas_pvs (bool): Update measurement PVs if auto-load config is enabled. If False, don't update, even
                if auto-load is enabled in the settings.
        """
        current_object_name = self.obj_name_cb.currentText()
        # If object data already displayed, return
        if current_object_name == self.last_details_update_obj:
            return

        self.clear_details()
        self.message_lbl.clear()

        obj_id = get_object_id(current_object_name) if current_object_name else False
        self.obj_type_cb.setEnabled(not obj_id)
        self.obj_comment.setEnabled(not obj_id)
        if not obj_id:
            return

        # Don't update details for objects with duplicate names
        if not isinstance(obj_id, list):
            self.update_details(obj_id, current_object_name)

        if update_meas_pvs:
            if Settings.Manager.auto_load_existing_config:  # If existing config auto-load setting is enabled
                self.clear_measurement_pv_names()  # clear the PV names before updating
            self.check_for_existing_config_pvs(obj_id)

    def update_details(self, obj_id: int, current_object: str):
        """ Fetches the object record data and updates the details widgets with it. """
        obj_record = get_object(obj_id)
        obj_class_name = get_object_class(object_id=obj_id)
        type_name = get_object_type(object_id=obj_id)

        self.obj_comment.setText(obj_record.ob_comment if obj_record else None)
        self.obj_type_cb.setCurrentText(type_name)
        self.type_and_comment_updated = True

        self.obj_detail_name.setText(get_object_name(obj_id))
        self.obj_detail_id.setText(f'{obj_id}')
        self.obj_detail_class.setText(obj_class_name)
        self.obj_detail_func.setText(get_object_function(object_id=obj_id))

        self.obj_detail_sld_name.setText(get_object_sld(obj_id))
        self.obj_detail_sld_id.setText(f'{get_sld_id(obj_id)}')

        self.last_details_update_obj = current_object

    def check_for_existing_config_pvs(self, obj_id: int):
        """ Check if a PV config with the given object already exists, and if it does, display config load frame. """
        obj_entry = Settings.Service.PVConfig.get_entry_with_id(obj_id)
        if not obj_entry:
            self.existing_config_frame.hide()
            self.existing_config_load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.existing_config_pvs = {}
            return

        self.existing_config_pvs = obj_entry[Settings.Service.PVConfig.MEAS]
        self.delete_btn.setEnabled(True)

        self.existing_config_frame.show()
        self.existing_config_load_btn.setEnabled(True)
        self.existing_config_load_btn.setText('Load')

        if Settings.Manager.auto_load_existing_config:  # If existing config auto-load setting is enabled
            self.load_existing_config_pvs()  # update all PV names.

    def load_existing_config_pvs(self):
        """ Update the measurement PV names with those from the existing config. """
        for index, mea in enumerate(self.mea_widgets):
            try:
                mea[0].setText(self.existing_config_pvs[f'{index + 1}'])
            except KeyError:
                continue
        self.existing_config_load_btn.setText('Loaded')
        self.existing_config_load_btn.setEnabled(False)

    # endregion

    # region Measurement PVs & CA Connection Check
    def clear_pvs_connection_status(self, mea_status_lbl=None):
        if mea_status_lbl:
            mea_status_lbl.clear()
            mea_status_lbl.setStyleSheet('')
        else:
            for mea in self.mea_widgets:
                mea[2].clear()
                mea[2].setStyleSheet('')

    def clear_measurement_type_labels(self):
        for mea in self.mea_widgets:
            mea[1].clear()

    def clear_measurement_pv_names(self):
        for mea in self.mea_widgets:
            mea[0].clear()

    def update_measurement_types(self):
        type_name = self.obj_type_cb.currentText()
        if not type_name:
            self.clear_measurement_type_labels()
            return

        type_id = get_type_id(type_name=type_name)
        if not type_id:
            manager_logger.warning(f'Type ID for {type_name} was not found.')

        class_id = get_class_id(type_id=type_id)

        sld = False
        # If class is Vessel, Cryostat or Gas Counter, display types for HLModule (class of Soft. Level Device)
        if class_id in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT, DBClassIDs.GAS_COUNTER]:
            sld = True
            class_id = DBClassIDs.HE_LVL_MODULE

        mea_types = get_measurement_types(object_class_id=class_id)
        for i, mea in enumerate(self.mea_widgets):
            mea[1].setText(f'SLD: {mea_types[i]}' if sld else mea_types[i])

    def toggle_widgets_based_on_pv_check_running(self, pvs_check_running: bool):
        self.check_pvs_btn.setText('Checking connections ...' if pvs_check_running
                                   else self.check_pvs_btn_default_text)
        self.check_pvs_btn.setEnabled(not pvs_check_running)
        for mea in self.mea_widgets:
            mea[0].setEnabled(not pvs_check_running)
        self.obj_name_cb.setEnabled(not pvs_check_running)
        self.ok_btn.setEnabled(not pvs_check_running)
        self.log_interval_sb.setEnabled(not pvs_check_running)

    def start_measurement_pvs_check(self, add_entry_after_check: bool = False):
        """
        Check all line edits. If no text, skip. If text, take PV name (should accept both FULL and PARTIAL names).
        Starts the PV connection check thread.
        For each PV, thread tries to connect and get value. If success, change label and set green,
        if timeout set red etc.
        While loading, change label text or add loading animation

        Args:
            add_entry_after_check (bool): Whether to to add the PV configuration on finish or not.
                This is used when the check is started automatically by the Add Configuration button
                if automatic PV check is enabled in general settings.
        """
        names = []
        for mea in self.mea_widgets:
            name = mea[0].text()
            if name:
                full_name = Settings.Service.CA.get_full_pv_name(name)
                names.append(full_name)
            else:
                names.append(None)
        self.pvs_connection_thread.add_entry_after_check(add_entry=add_entry_after_check)
        self.pvs_connection_thread.set_pv_names(pv_names=names)
        self.pvs_connection_thread.start()

    def update_measurements_pvs_status(self, index: int, connected: bool):
        """ Update the PVs status with the connection test results. """
        status_lbl = self.mea_widgets[index][2]
        status_lbl.setText('OK' if connected else 'ERR')
        status_lbl.setStyleSheet('color: green;' if connected else 'color: red;')

    def on_progress_bar_show_event(self, _event):
        if self.existing_config_frame.isVisible():
            self.existing_config_frame.hide()

    def on_progress_bar_hide_event(self, _event):
        if not self.existing_config_frame.isVisible() and self.existing_config_pvs:
            self.existing_config_frame.show()

    def on_mea_pv_text_change(self, mea: tuple):
        """
        Clears the measurement PV name status of the given QLineEdit index.
        Enables the check PVs button as long as there is one PV name in the measurement QLineEdits.
        Clears the message.
        Clears the red-highlight of the Mea. PVs frame.
        """
        self.clear_pvs_connection_status(mea_status_lbl=mea[2])
        self.enable_or_disable_check_pvs_btn()
        self.message_lbl.clear()
        set_red_border(self.mea_pvs_frame, False)

    def update_load_existing_config_btn(self):
        if self.existing_config_frame.isVisible():
            self.existing_config_load_btn.setText('Load')
            self.existing_config_load_btn.setEnabled(True)

    def enable_or_disable_check_pvs_btn(self):
        any_pv_name_set = any(mea[0].text() for mea in self.mea_widgets)
        self.check_pvs_btn.setEnabled(any_pv_name_set)

    def pvs_connection_check_started(self):
        self.toggle_widgets_based_on_pv_check_running(pvs_check_running=True)
        self.clear_pvs_connection_status()
        self.set_message_colored_text('Checking measurement PVs ...', 'rgb(255, 85, 0)')

    def pvs_connection_check_finished(self, add_entry=False):
        self.toggle_widgets_based_on_pv_check_running(pvs_check_running=False)

        results = self.pvs_connection_thread.results
        failed_pvs = len(results['failed'])
        if failed_pvs:
            self.set_message_colored_text(f'PV connection test finished.\n{failed_pvs} PVs failed to connect.', 'red')
        else:
            self.set_message_colored_text('PV connection test finished.\nAll PVs connected.', 'green')

        if add_entry:
            # Trigger once the PV connection check thread has finished.
            # Check if there are any PVs that failed to connect, and if so, display warning to ask if cancel or add.
            # If all PVs successfully connected or user decides to add anyway, call add_entry.
            self.loading_msg.close()
            if self.pvs_connection_thread.results['failed']:
                msg_box = QMessageBox.warning(self, 'PV Connection Failed',
                                              'Could not establish connection to one or more PVs.\n'
                                              'Add configuration anyway?',
                                              QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if msg_box != QMessageBox.Yes:
                    return
            self.add_entry(object_id=self.pv_check_obj_id, overwrite=self.pv_check_obj_already_exists)

    # endregion

    # region Utilities & Other
    def edit_object_config(self, obj_name: str):
        """ Starts editing an object by loading its details and PV config. """
        self.obj_name_cb.lineEdit().setText(obj_name)
        self.load_object_data()
        self.load_existing_config_pvs()

    def set_message_colored_text(self, msg: str, color: str):
        self.message_lbl.setText(msg)
        self.message_lbl.setStyleSheet(f'color: {color};')
    # endregion
