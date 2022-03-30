import os
from datetime import datetime

import psutil
import win32serviceutil
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent, QShowEvent, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QApplication, QListWidget, \
    QSizePolicy
from PyQt5 import uic

from service_manager.logger import manager_logger
from service_manager.settings import Settings
from service_manager.constants import main_window_ui, ASSETS_PATH, MANAGER_SETTINGS_DIR, \
    MANAGER_SETTINGS_FILE, MANAGER_LOGS_FILE
from service_manager.gui.about import UIAbout
from service_manager.gui.db_settings import UIDBSettings
from service_manager.gui.general_settings import UIGeneralSettings
from service_manager.gui.ca_settings import UICASettings
from service_manager.gui.service_path_dlg import UIServicePathDialog
from service_manager.gui.config_entry import UIConfigEntryDialog
from service_manager.utilities import is_admin, set_colored_text, setup_button
from service_manager.gui.main_window_threads import ServiceLogUpdaterThread, \
    ServiceStatusCheckThread
from service_manager.db_func import db_connected, get_object_name, get_object_type
from shared.const import SERVICE_NAME
from shared.utils import get_object_module

EXPAND_CONFIG_TABLE_BTN = {False: ['  Expand', 'expand.svg'], True: ['  Shrink', 'shrink.svg']}


class ConfigTableIndex:
    ID = 0
    NAME = 1


class UIMainWindow(QMainWindow):
    def __init__(self):
        super(UIMainWindow, self).__init__()
        uic.loadUi(main_window_ui, self)

        # Update title if app running with admin privileges
        if is_admin():
            self.setWindowTitle(self.windowTitle() + ' (Administrator)')

        # region External windows
        self.about_w = UIAbout()  # "About" dialogue window
        self.db_settings_w = UIDBSettings()  # "DB Settings" dialogue window
        self.general_settings_w = UIGeneralSettings()  # "General Settings" dialogue window
        self.ca_settings_w = UICASettings()  # "Channel Access" dialogue window
        self.service_dir_path_w = UIServicePathDialog()  # "Service Directory" dialogue window
        self.config_entry_w = UIConfigEntryDialog()  # Add/Edit Configuration Entry dialogue window
        # endregion

        # region External windows setup
        self.db_settings_w.update_db_connection_status.connect(self.update_fields)
        self.service_dir_path_w.service_updated.connect(self.update_service)
        self.service_dir_path_w.service_updated.connect(self.update_fields)
        self.config_entry_w.config_updated.connect(self.refresh_config)
        # endregion

        # region Attributes
        self.table_expanded = False  # For toggling table expansion ("Expand Table"/"Service Info")
        self.pv_config_data = []  # Store the PV configuration data to be displayed in the
        # config. table
        self.expand_table_btn_text = EXPAND_CONFIG_TABLE_BTN
        # endregion

        # region Menu actions & signals
        self.about_action.triggered.connect(lambda _: self.trigger_window(self.about_w))
        self.manager_log_action.triggered.connect(lambda _: os.startfile(MANAGER_LOGS_FILE))
        self.manager_settings_action.triggered.connect(
            lambda _: os.startfile(MANAGER_SETTINGS_FILE))
        self.manager_settings_dir_action.triggered.connect(
            lambda _: os.startfile(MANAGER_SETTINGS_DIR))
        self.show_service_log.triggered.connect(self.open_service_log)
        self.show_service_dir.triggered.connect(self.trigger_open_service_dir)
        self.show_service_settings.triggered.connect(
            lambda _: os.startfile(Settings.Service.settings_path))
        self.db_settings_action.triggered.connect(lambda _: self.trigger_window(self.db_settings_w))
        self.general_settings_action.triggered.connect(
            lambda _: self.trigger_window(self.general_settings_w))
        self.ca_settings_action.triggered.connect(lambda _: self.trigger_window(self.ca_settings_w))
        self.service_directory_action.triggered.connect(self.trigger_service_directory)
        self.open_pv_config_action.triggered.connect(self.trigger_open_pv_config)
        # endregion

        # region Setup widgets
        btn_conf = [
            (self.btn_service_start, 'start.svg'),
            (self.btn_service_stop, 'stop.svg'),
            (self.btn_service_restart, 'restart.svg'),
            (self.db_connection_refresh_btn, 'refresh.svg'),
            (self.expand_table_btn, None),
            (self.refresh_btn, 'refresh_config.svg'),
            (self.show_filter_btn, 'filter.svg'),
            (self.new_config_btn, 'add.svg'),
            (self.edit_config_btn, 'edit.svg'),
            (self.delete_config_btn, 'delete.svg')
        ]
        for btn in btn_conf:
            setup_button(btn[0], btn[1])

        if not is_admin():
            for btn in [self.btn_service_start, self.btn_service_stop, self.btn_service_restart]:
                btn.setEnabled(False)
                btn.setToolTip(
                    btn.toolTip() + '\nRun the manager as administrator to start/stop/restart the '
                                    'service.')

        # Filter/Search Frame Setup
        self.filter_frame.setVisible(False)

        # Save the table header names, to be used for the Filters columns combo box
        column_names = [self.config_table.horizontalHeaderItem(index).text()
                        for index in range(self.config_table.columnCount())]
        self.filter_columns_cb.insertItems(0, ['All columns', *column_names])
        # endregion

        # region Signals to Slots
        self.btn_service_start.clicked.connect(
            lambda _: self.call_on_service(win32serviceutil.StartService))
        self.btn_service_stop.clicked.connect(
            lambda _: self.call_on_service(win32serviceutil.StopService))
        self.btn_service_restart.clicked.connect(
            lambda _: self.call_on_service(win32serviceutil.RestartService))

        self.db_connection_refresh_btn.clicked.connect(self.refresh_db_connection)

        self.config_table.itemSelectionChanged.connect(
            self.enable_or_disable_edit_and_delete_buttons)
        self.expand_table_btn.clicked.connect(self.expand_table_btn_clicked)
        self.refresh_btn.clicked.connect(self.refresh_config)
        self.show_filter_btn.clicked.connect(self.show_filter_btn_clicked)
        self.new_config_btn.clicked.connect(self.new_config_btn_clicked)
        self.edit_config_btn.clicked.connect(self.edit_config_btn_clicked)
        self.delete_config_btn.clicked.connect(self.delete_config_btn_clicked)
        # Table Filters
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.filter_bar.returnPressed.connect(self.apply_filters)
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        # endregion

        # region Threads
        # region Service Status Thread
        # noinspection PyTypeChecker
        self.thread_service_status = ServiceStatusCheckThread()
        self.thread_service_status.update_status_title.connect(self.service_status_title.setText)
        self.thread_service_status.update_status_style.connect(
            self.service_status_title.setStyleSheet)
        self.thread_service_status.update_service_details.connect(self.update_service_details)
        self.thread_service_status.update_service_control_btns.connect(
            self.update_service_control_btns)
        self.thread_service_status.start()
        # endregion

        # region Service Log Thread
        # noinspection PyTypeChecker
        self.thread_service_log = ServiceLogUpdaterThread(
            self.service_log_show_lines_spinbox.value())
        self.thread_service_log.log_fetched.connect(self.update_service_log)
        self.thread_service_log.file_not_found.connect(self.clear_service_log)
        self.thread_service_log.enable_or_disable_buttons.connect(self.update_service_log_btns)
        self.thread_service_log.start()
        # endregion

        # QThreads graceful exit on app close
        QApplication.instance().aboutToQuit.connect(self.thread_service_status.stop)
        QApplication.instance().aboutToQuit.connect(self.thread_service_log.stop)
        # endregion

        # region Service Log Widgets
        self.service_log_file_open_btn.clicked.connect(self.open_service_log)
        self.service_log_scroll_down_btn.clicked.connect(self.log_scroll_to_bottom)

        # Emit spinner valueChanged only on return key pressed, focus lost, and widget arrow keys
        # clicked
        self.service_log_show_lines_spinbox.setKeyboardTracking(False)

        self.service_log_font_size.currentTextChanged.connect(self.update_log_font_size)
        self.service_log_show_lines_spinbox.valueChanged.connect(
            self.thread_service_log.set_displayed_lines_no)
        # endregion

    # region Show & Close Events
    def showEvent(self, event: QShowEvent):
        self.update_fields()

    def closeEvent(self, event: QCloseEvent):
        quit_msg = "Close the application?"
        reply = QMessageBox.question(self, 'HLM PV Import', quit_msg, QMessageBox.Yes,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()

    # endregion

    # region Update Fields & Update Service
    def update_fields(self):
        self.update_config_data()
        self.update_config_table()
        expand_table_btn_settings = self.expand_table_btn_text[
            self.table_expanded]  # text and icon depending on table
        self.expand_table_btn.setText(expand_table_btn_settings[0])
        self.expand_table_btn.setIcon(
            QIcon(os.path.join(ASSETS_PATH, expand_table_btn_settings[1])))
        self.edit_config_btn.setEnabled(False)
        self.delete_config_btn.setEnabled(False)

        self.update_db_connection_status()

    def refresh_db_connection(self):
        manager_logger.info("Refreshing database connection...")
        Settings.Service.connect_to_db()
        self.update_db_connection_status()

    def update_db_connection_status(self):
        if db_connected():
            set_colored_text(self.db_connection_status, 'connected', QColor('green'))

        else:
            set_colored_text(self.db_connection_status, 'not connected', QColor('red'))
        self.db_connection_last_checked.setText(
            f"Connection status last updated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}")

    def update_service(self):
        self.thread_service_log.start()
        self.thread_service_log.update_log()

        self.thread_service_status.start()
        self.thread_service_status.update_status()

    # endregion

    # region Service control buttons slots
    def call_on_service(self, func):
        func(SERVICE_NAME)
        self.thread_service_status.update_status()

    # endregion

    # region Action Slots
    @staticmethod
    def trigger_open_service_dir():
        service_dir_path = Settings.Manager.service_path
        os.startfile(service_dir_path)

    @staticmethod
    def trigger_window(window):
        window.show()
        window.activateWindow()

    def trigger_service_directory(self):
        self.service_dir_path_w.exec_()

    @staticmethod
    def trigger_open_pv_config():
        path = Settings.Service.PVConfig.get_path()
        os.startfile(path)

    # endregion

    # region PV Configuration Table
    def update_config_data(self):
        """ Get the PV configuration entries (list of dicts) and store the data in an attribute. """
        try:
            self.pv_config_data = Settings.Service.PVConfig.get_entries()
        except FileNotFoundError as e:
            manager_logger.error(e)
            self.pv_config_data = []
            return

    def expand_table_btn_clicked(self):
        """
        Toggle table expanded by hiding the service status & log frames, allowing the table to
        fill the remaining
        space.
         """
        # expanded is false -> set visible false (hide) -> expanded = true;
        # expanded is true -> set visible true (show) -> expanded = false;
        self.service_status_frame.setVisible(self.table_expanded)
        self.service_log_panel.setVisible(self.table_expanded)
        self.h_line_one.setVisible(self.table_expanded)
        self.h_line_two.setVisible(self.table_expanded)
        self.table_expanded = not self.table_expanded  # toggle bool
        expand_table_btn_settings = self.expand_table_btn_text[
            self.table_expanded]  # text and icon depending on table
        self.expand_table_btn.setText(expand_table_btn_settings[0])
        self.expand_table_btn.setIcon(
            QIcon(os.path.join(ASSETS_PATH, expand_table_btn_settings[1])))

    def refresh_config(self):
        """ Re-fetch PV config data, update table contents. """
        self.update_config_data()
        self.update_config_table()

    def show_filter_btn_clicked(self):
        """ Show or Hide the Filters bar. """
        toggle = not self.filter_frame.isVisible()
        self.filter_frame.setVisible(toggle)

    def apply_filters(self):
        """
        Apply filters and display only the matches in the config table.
        column_of_interest = 0 -> index 0 for the filters columns comboBox (All Columns).
         """
        column_of_interest = self.filter_columns_cb.currentIndex()
        value_of_interest = self.filter_bar.text()

        if column_of_interest == 0:
            results = self.config_table.findItems(value_of_interest, Qt.MatchContains)
            rows = set(item.row() for item in results)
            for index in range(self.config_table.rowCount()):
                show_or_hide = index not in rows
                self.config_table.setRowHidden(index, show_or_hide)
        else:
            column_of_interest -= 1  # So indexes match (as filters columns comboBox has an extra
            # "All Columns" on 0)
            for rowIndex in range(self.config_table.rowCount()):
                item = self.config_table.item(rowIndex, column_of_interest)
                contains_search = value_of_interest in item.text()
                self.config_table.setRowHidden(rowIndex, not contains_search)

    def clear_filters(self):
        self.filter_columns_cb.setCurrentIndex(0)
        self.filter_bar.clear()
        self.refresh_config()

    def new_config_btn_clicked(self):
        """ Open the Config Entry dialog window. If database is not connected, display error
        message. """
        if not db_connected():
            QMessageBox.critical(self, 'Database connection required',
                                 'Database connection is required to edit the PV configuration.',
                                 QMessageBox.Ok)
            return

        self.config_entry_w.show()
        self.config_entry_w.activateWindow()

    def edit_config_btn_clicked(self):
        """ On Edit, open Config Entry dialog window as normal with object selected and PV config
        loaded. """
        if not db_connected():
            QMessageBox.critical(self, 'Database connection required',
                                 'Database connection is required to edit the PV configuration.',
                                 QMessageBox.Ok)
            return
        self.config_entry_w.show()

        selected_row_items = self.config_table.selectedItems()
        if selected_row_items:
            selected_object_name = selected_row_items[1].text()
            self.config_entry_w.edit_object_config(obj_name=selected_object_name)

        self.config_entry_w.activateWindow()

    def delete_config_btn_clicked(self):
        """
        Display message box with list of selected PV config entries, with Delete & Cancel options.
        On Delete, the entries will be deleted from the PV config, and table will be refreshed.
        """
        selected = self.config_table.selectedIndexes()
        cols_count = self.config_table.columnCount()
        selected_rows = set()
        for index in selected[1::cols_count]:
            selected_rows.add(index.row())

        if not selected_rows:
            return

        obj_ids = []  # ids of objects whose config is to be removed
        obj_list = []
        for row_no in selected_rows:
            id_ = self.config_table.item(row_no, ConfigTableIndex.ID)
            obj_ids.append(id_.text())
            name_ = self.config_table.item(row_no, ConfigTableIndex.NAME)
            obj_list.append(f'(ID: {id_.text()}) {name_.text()}')

        msg_box = DeleteConfigsMessageBox(obj_list=obj_list)
        resp = msg_box.exec()

        if resp == QMessageBox.Ok:
            for item in obj_ids:
                Settings.Service.PVConfig.delete_entry(object_id=int(item))

        self.refresh_config()

    def update_config_table(self):
        """ Update the config table contents with the stored entries' data. """
        self.config_table.setSortingEnabled(
            False)  # otherwise table will not be properly updated if columns are sorted
        self.config_table.setRowCount(0)  # it will delete the QTableWidgetItems automatically

        pv_config_data = self.pv_config_data  # Get the stored PV config data (from
        # update_config_data)

        for entry in pv_config_data:
            object_id = entry[Settings.Service.PVConfig.OBJ]

            # store the entry data in a list, prepare to add to table as row
            entry_data = [
                object_id,
                get_object_name(object_id),
                get_object_type(object_id),
                get_object_module(object_id),
                entry[Settings.Service.PVConfig.LOG_PERIOD],
                *[entry[Settings.Service.PVConfig.MEAS].get(x) for x in ['1', '2', '3', '4', '5']]
            ]

            self.config_table.insertRow(self.config_table.rowCount())

            # for each element of the entry data, add it to an item then add the item to the
            # appropriate table cell
            for index, elem in enumerate(entry_data):
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setData(Qt.DisplayRole, elem)
                item.setToolTip(f'{elem}')
                self.config_table.setItem(self.config_table.rowCount() - 1, index, item)

        self.config_table.setSortingEnabled(True)
        self.config_table.resizeColumnsToContents()

    def enable_or_disable_edit_and_delete_buttons(self):
        """ If config table has row selection, enable buttons. """
        items_selected = bool(self.config_table.selectedItems())
        self.edit_config_btn.setEnabled(items_selected)
        self.delete_config_btn.setEnabled(items_selected)

    # endregion

    # region Threads
    # region Service Log
    def update_service_log(self, text):
        """ Update the service log text field while maintaining scroll position. """
        old_v_scrollbar_value = self.service_log_txt.verticalScrollBar().value()
        old_h_scrollbar_value = self.service_log_txt.horizontalScrollBar().value()

        self.service_log_txt.setPlainText(text)

        self.service_log_txt.verticalScrollBar().setValue(old_v_scrollbar_value)
        self.service_log_txt.horizontalScrollBar().setValue(old_h_scrollbar_value)

    def clear_service_log(self):
        self.service_log_txt.clear()

    def log_scroll_to_bottom(self):
        self.service_log_txt.verticalScrollBar(). \
            setValue(self.service_log_txt.verticalScrollBar().maximum())

    def open_service_log(self):
        log_path = Settings.Service.Logging.log_path
        if os.path.exists(log_path):
            os.startfile(log_path)
        else:
            QMessageBox.critical(self, 'Service Log File Not Found',
                                 'The service log file was not found.\n'
                                 f'"{log_path}" does not exist.',
                                 QMessageBox.Ok)
            return

    def update_log_font_size(self, value):
        self.service_log_txt.setStyleSheet(f'font-size: {value}pt;')

    def update_service_log_btns(self, enabled: bool):
        self.service_log_file_open_btn.setEnabled(enabled)
        self.service_log_scroll_down_btn.setEnabled(enabled)
        self.service_log_show_lines_spinbox.setEnabled(enabled)

    # endregion

    # region Service Status
    def update_service_details(self, service: dict):
        self.service_details_name.setText(service['name'])
        self.service_details_status.setText(service['status'])
        self.service_details_pid.setText(f"{service['pid']}")
        self.service_details_startup.setText(service['start_type'])
        self.service_details_description.setText(service['description'])
        self.service_details_username.setText(service['username'])
        self.service_details_binpath.setText(service['binpath'])

    def update_service_control_btns(self, service_status):
        stopped = service_status == psutil.STATUS_STOPPED
        running = service_status == psutil.STATUS_RUNNING
        self.btn_service_start.setEnabled(stopped)
        self.btn_service_stop.setEnabled(running)
        self.btn_service_restart.setEnabled(running)
    # endregion
    # endregion


class DeleteConfigsMessageBox(QMessageBox):
    """ Message Box on deleting configuration entries. Display a list of entries to be deleted
    and confirm button. """

    def __init__(self, obj_list: list):
        super().__init__()

        self.setWindowTitle('Delete configuration')
        self.setText(f'Deleting the following configuration entries.\n'
                     f'Are you sure?\n\n\n')
        self.setIcon(QMessageBox.Warning)

        self.list_ = QListWidget(self)
        self.list_.move(30, 70)
        self.list_.resize(450, 120)
        self.list_.addItems(obj_list)

        self.addButton(QMessageBox.Ok)
        ok_btn = self.button(QMessageBox.Ok)
        ok_btn.setText('Delete')
        self.addButton(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)

    # QMessageBox "resists" resizing, and the widget will always get hard-resized to the width of
    # the
    # main text attribute, and informativeText will always get word-wrapped to that width whether
    # you want it to or not.
    # To set the size manually, subclass QMessageBox and reimplement the resize event handler to
    # override the layout.
    def resizeEvent(self, e):
        result = QMessageBox.resizeEvent(self, e)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.resize(500, 250)

        return result
