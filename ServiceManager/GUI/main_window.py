import os
from datetime import datetime
import win32serviceutil
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCloseEvent, QShowEvent, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QMessageBox, QPlainTextEdit, QWidget, QSpinBox, \
    QLineEdit, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QApplication, QFrame, QListWidget, QSizePolicy, \
    QToolButton
from PyQt5 import uic

from ServiceManager.logger import logger
from ServiceManager.settings import Settings
from ServiceManager.constants import main_window_ui, ASSETS_PATH
from ServiceManager.GUI.about import UIAbout
from ServiceManager.GUI.db_settings import UIDBSettings
from ServiceManager.GUI.general_settings import UIGeneralSettings
from ServiceManager.GUI.ca_settings import UICASettings
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.GUI.config_entry import UIConfigEntryDialog
from ServiceManager.utilities import is_admin, set_colored_text
from ServiceManager.GUI.main_window_threads import ServiceLogUpdaterThread, ServiceStatusCheckThread
from ServiceManager.db_utilities import DBUtils


class UIMainWindow(QMainWindow):
    def __init__(self):
        super(UIMainWindow, self).__init__()
        uic.loadUi(main_window_ui, self)

        # Update title if app running with admin privileges
        if is_admin():
            self.setWindowTitle(self.windowTitle() + ' (Administrator)')

        # region External windows
        self.about_w = None                     # "About" dialogue window
        self.db_settings_w = None               # "DB Settings" dialogue window
        self.general_settings_w = None          # "General Settings" dialogue window
        self.ca_settings_w = None               # "Channel Access" dialogue window
        self.service_dir_path_w = None          # "Service Directory" dialogue window
        self.config_entry_w = None              # Add/Edit Configuration Entry dialogue window
        # endregion

        # region Attributes
        self.table_expanded = False             # For toggling table expansion ("Expand Table"/"Service Info")
        self.expand_table_btn_text = {False: ['  Expand', 'expand.svg'], True: ['  Shrink', 'shrink.svg']}
        self.column_names = []                  # Config. table header names, for the Filters columns comboBox
        self.pv_config_data = None              # Store the PV configuration data to be displayed in the config. table
        # endregion

        # region Menu actions & signals
        self.about_action = self.findChild(QAction, 'actionAbout')
        self.about_action.triggered.connect(self.trigger_about)
        self.manager_log_action = self.findChild(QAction, 'actionManager_Error_Log')
        self.manager_log_action.triggered.connect(self.open_manager_log)
        self.manager_settings_action = self.findChild(QAction, 'actionManager_Settings')
        self.manager_settings_action.triggered.connect(self.open_manager_settings)
        self.manager_settings_dir_action = self.findChild(QAction, 'actionManager_Data_Dir')
        self.manager_settings_dir_action.triggered.connect(self.open_manager_settings_dir)
        self.show_service_log = self.findChild(QAction, 'actionDebug_log')
        self.show_service_log.triggered.connect(self.open_service_log)
        self.show_service_dir = self.findChild(QAction, 'actionService_directory')
        self.show_service_dir.triggered.connect(self.trigger_open_service_dir)
        self.show_service_settings = self.findChild(QAction, 'actionService_Settings')
        self.show_service_settings.triggered.connect(self.trigger_open_service_settings_file)
        self.db_settings_action = self.findChild(QAction, 'actionDB_Connection')
        self.db_settings_action.triggered.connect(self.trigger_db_settings)
        self.general_settings_action = self.findChild(QAction, 'actionGeneral')
        self.general_settings_action.triggered.connect(self.trigger_general_settings)
        self.ca_settings_action = self.findChild(QAction, 'actionChannel_Access')
        self.ca_settings_action.triggered.connect(self.trigger_ca_settings)
        self.service_directory_action = self.findChild(QAction, 'actionService_Directory')
        self.service_directory_action.triggered.connect(self.trigger_service_directory)
        self.open_pv_config_action = self.findChild(QAction, 'actionPV_Config')
        self.open_pv_config_action.triggered.connect(self.trigger_open_pv_config)
        # endregion

        # region Get widgets
        self.service_status_frame = self.findChild(QFrame, 'serviceStatusFrame')
        self.service_status_panel = self.findChild(QWidget, 'serviceDetails')
        self.service_status_title = self.service_status_panel.findChild(QLabel, 'statusMessage')
        self.service_details_name = self.service_status_panel.findChild(QLineEdit, 'nameText')
        self.service_details_status = self.service_status_panel.findChild(QLineEdit, 'statusText')
        self.service_details_pid = self.service_status_panel.findChild(QLineEdit, 'pidText')
        self.service_details_startup = self.service_status_panel.findChild(QLineEdit, 'startUpTypeText')
        self.service_details_description = self.service_status_panel.findChild(QLineEdit, 'descriptionText')
        self.service_details_username = self.service_status_panel.findChild(QLineEdit, 'usernameText')
        self.service_details_binpath = self.service_status_panel.findChild(QLineEdit, 'binPathText')
        self.btn_service_start = self.service_status_panel.findChild(QPushButton, 'serviceStart')
        self.btn_service_start.setIcon(QIcon(os.path.join(ASSETS_PATH, 'start.svg')))
        self.btn_service_start.setIconSize(QSize(15, 15))
        self.btn_service_start.setStyleSheet("QPushButton { text-align: left; }")
        self.btn_service_stop = self.service_status_panel.findChild(QPushButton, 'serviceStop')
        self.btn_service_stop.setIcon(QIcon(os.path.join(ASSETS_PATH, 'stop.svg')))
        self.btn_service_stop.setIconSize(QSize(15, 15))
        self.btn_service_stop.setStyleSheet("QPushButton { text-align: left; }")
        self.btn_service_restart = self.service_status_panel.findChild(QPushButton, 'serviceRestart')
        self.btn_service_restart.setIcon(QIcon(os.path.join(ASSETS_PATH, 'restart.svg')))
        self.btn_service_restart.setIconSize(QSize(15, 15))
        self.btn_service_restart.setStyleSheet("QPushButton { text-align: left; }")
        if not is_admin():
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)

        self.db_connection_status = self.findChild(QLabel, 'dbConnStatus')
        self.db_connection_refresh_btn = self.findChild(QToolButton, 'refreshDbConnButton')
        self.db_connection_refresh_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'refresh.svg')))
        self.db_connection_refresh_btn.setIconSize(QSize(15, 15))
        self.db_connection_last_checked = self.findChild(QLabel, 'dbLastCheckedLbl')

        self.h_line_one = self.findChild(QFrame, 'h_line_1')

        self.config_table = self.findChild(QTableWidget, 'configTable')
        self.expand_table_btn = self.findChild(QPushButton, 'expandTableButton')
        self.expand_table_btn.setIconSize(QSize(15, 15))
        self.expand_table_btn.setStyleSheet("QPushButton { text-align: left; }")
        self.refresh_btn = self.findChild(QPushButton, 'refreshButton')
        self.refresh_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'refresh_config.svg')))
        self.refresh_btn.setIconSize(QSize(15, 15))
        self.refresh_btn.setStyleSheet("QPushButton { text-align: left; }")
        self.show_filter_btn = self.findChild(QPushButton, 'filterButton')
        self.show_filter_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'filter.svg')))
        self.show_filter_btn.setIconSize(QSize(15, 15))
        self.show_filter_btn.setStyleSheet("QPushButton { text-align: left; }")
        self.new_config_btn = self.findChild(QPushButton, 'newButton')
        self.new_config_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'add.svg')))
        self.new_config_btn.setIconSize(QSize(15, 15))
        self.new_config_btn.setStyleSheet("QPushButton { text-align: left; }")
        self.edit_config_btn = self.findChild(QPushButton, 'editButton')
        self.edit_config_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'edit.svg')))
        self.edit_config_btn.setIconSize(QSize(15, 15))
        self.edit_config_btn.setStyleSheet("QPushButton { text-align: left; }")
        self.delete_config_btn = self.findChild(QPushButton, 'deleteButton')
        self.delete_config_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, 'delete.svg')))
        self.delete_config_btn.setIconSize(QSize(15, 15))
        self.delete_config_btn.setStyleSheet("QPushButton { text-align: left; }")

        # Save the table header names, to be used for the Filters columns combo box
        for index in range(self.config_table.columnCount()):
            self.column_names.append(self.config_table.horizontalHeaderItem(index).text())

        # Filter/Search Frame Setup
        self.filter_frame = self.findChild(QFrame, 'filterFrame')
        self.filter_frame.setVisible(False)
        self.filter_columns_cb = self.findChild(QComboBox, 'filterColumnCB')
        self.filter_columns_cb.insertItems(0, ['All columns', *self.column_names])
        self.filter_bar = self.findChild(QLineEdit, 'filterValueLE')
        self.apply_filter_btn = self.findChild(QPushButton, 'applyFilterBtn')
        self.clear_filter_btn = self.findChild(QPushButton, 'clearFilterBtn')

        self.h_line_two = self.findChild(QFrame, 'h_line_2')

        self.service_log_panel = self.findChild(QWidget, 'serviceLog')
        self.service_log_txt = self.service_log_panel.findChild(QPlainTextEdit, 'serviceLogText')
        self.service_log_file_open_btn = self.service_log_panel.findChild(QPushButton, 'openLogFileButton')
        self.service_log_scroll_down_btn = self.service_log_panel.findChild(QPushButton, 'logScrollDownButton')
        self.service_log_show_lines_spinbox = self.service_log_panel.findChild(QSpinBox, 'logLinesSpinBox')
        self.service_log_font_size = self.service_log_panel.findChild(QComboBox, 'fontSizeCB')
        # endregion

        # region Signals to Slots
        self.btn_service_start.clicked.connect(self.service_start_btn_clicked)
        self.btn_service_stop.clicked.connect(self.service_stop_btn_clicked)
        self.btn_service_restart.clicked.connect(self.service_restart_btn_clicked)

        self.db_connection_refresh_btn.clicked.connect(self.refresh_db_connection)

        self.config_table.itemSelectionChanged.connect(self.enable_or_disable_edit_and_delete_buttons)
        self.expand_table_btn.clicked.connect(self.expand_table_btn_clicked)
        self.refresh_btn.clicked.connect(self.refresh_config)
        self.show_filter_btn.clicked.connect(self.show_filter_btn_clicked)
        self.new_config_btn.clicked.connect(self.new_config_btn_clicked)
        self.edit_config_btn.clicked.connect(self.edit_config_btn_clicked)
        self.delete_config_btn.clicked.connect(self.delete_config_btn_clicked)
        # Table Filters
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.filter_bar.returnPressed.connect(self.apply_filters)
        self.filter_bar.returnPressed.connect(self.apply_filters)
        self.clear_filter_btn.clicked.connect(self.clear_filters)

        self.service_log_file_open_btn.clicked.connect(self.open_service_log)
        self.service_log_scroll_down_btn.clicked.connect(self.log_scroll_to_bottom)
        # Emit spinner valueChanged only on return key pressed, focus lost, and widget arrow keys clicked
        self.service_log_show_lines_spinbox.setKeyboardTracking(False)
        self.service_log_show_lines_spinbox.valueChanged.connect(self.update_log_displayed_lines_no)
        self.service_log_font_size.currentTextChanged.connect(self.update_log_font_size)
        # endregion

        # region Threads
        # region Service Status Thread
        # noinspection PyTypeChecker
        self.thread_service_status = ServiceStatusCheckThread()
        self.thread_service_status.update_status_title.connect(self.update_status_title)
        self.thread_service_status.update_status_style.connect(self.update_status_style)
        self.thread_service_status.update_service_details.connect(self.update_service_details)
        self.thread_service_status.update_service_control_btns.connect(self.update_service_control_btns)
        self.thread_service_status.start()
        # endregion

        # region Service Log Thread
        # noinspection PyTypeChecker
        self.thread_service_log = ServiceLogUpdaterThread(self.service_log_show_lines_spinbox.value())
        self.thread_service_log.log_fetched.connect(self.update_service_log)
        self.thread_service_log.file_not_found.connect(self.clear_service_log)
        self.thread_service_log.enable_or_disable_buttons.connect(self.update_service_log_btns)
        self.thread_service_log.start()
        # endregion

        # QThreads graceful exit on app close
        QApplication.instance().aboutToQuit.connect(self.thread_service_status.stop)
        QApplication.instance().aboutToQuit.connect(self.thread_service_log.stop)
        # endregion

    # region Show & Close Events
    def showEvent(self, event: QShowEvent):
        self.update_fields()

    def closeEvent(self, event: QCloseEvent):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'HLM PV Import', quit_msg, QMessageBox.Yes, QMessageBox.No)

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
        expand_table_btn_settings = self.expand_table_btn_text[self.table_expanded]  # text and icon depending on table
        self.expand_table_btn.setText(expand_table_btn_settings[0])
        self.expand_table_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, expand_table_btn_settings[1])))
        self.edit_config_btn.setEnabled(False)
        self.delete_config_btn.setEnabled(False)

        self.update_db_connection_status()

    def refresh_db_connection(self):
        if not DBUtils.is_connected():
            Settings.Service.connect_to_db()
        self.update_db_connection_status()

    def update_db_connection_status(self):
        if DBUtils.is_connected():
            set_colored_text(self.db_connection_status, 'connected', QColor('green'))

        else:
            set_colored_text(self.db_connection_status, 'not connected', QColor('red'))
        self.db_connection_last_checked.setText(f"Connection status last updated on: "
                                                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}")

    def update_service(self):
        self.thread_service_log.start()
        self.thread_service_log.update_log()

        self.thread_service_status.start()
        self.thread_service_status.update_status()
    # endregion

    # region Service control buttons slots
    def service_start_btn_clicked(self):
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.StartService(service_name)
        self.thread_service_status.update_status()

    def service_stop_btn_clicked(self):
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.StopService(service_name)
        self.thread_service_status.update_status()

    def service_restart_btn_clicked(self):
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.RestartService(service_name)
        self.thread_service_status.update_status()
    # endregion

    # region Action Slots
    def trigger_about(self):
        if self.about_w is None:
            self.about_w = UIAbout()
        self.about_w.show()
        self.about_w.activateWindow()

    @staticmethod
    def open_manager_log():
        log_file = Settings.Manager.get_log_path()
        os.startfile(log_file)

    @staticmethod
    def open_manager_settings():
        settings_file = Settings.Manager.get_manager_settings_path()
        os.startfile(settings_file)

    @staticmethod
    def open_manager_settings_dir():
        settings_dir = Settings.Manager.get_manager_settings_dir()
        os.startfile(settings_dir)

    @staticmethod
    def trigger_open_service_dir():
        service_dir_path = Settings.Manager.get_service_path()
        os.startfile(service_dir_path)

    @staticmethod
    def trigger_open_service_settings_file():
        settings_file = Settings.Service.settings_path
        os.startfile(settings_file)

    def trigger_db_settings(self):
        if self.db_settings_w is None:
            self.db_settings_w = UIDBSettings()
            self.db_settings_w.update_db_connection_status.connect(self.update_fields)
        self.db_settings_w.show()
        self.db_settings_w.activateWindow()

    def trigger_general_settings(self):
        if self.general_settings_w is None:
            self.general_settings_w = UIGeneralSettings()
        self.general_settings_w.show()
        self.general_settings_w.activateWindow()

    def trigger_ca_settings(self):
        if self.ca_settings_w is None:
            self.ca_settings_w = UICASettings()
        self.ca_settings_w.show()
        self.ca_settings_w.activateWindow()

    def trigger_service_directory(self):
        if self.service_dir_path_w is None:
            self.service_dir_path_w = UIServicePathDialog()
            self.service_dir_path_w.custom_signals.serviceUpdated.connect(self.update_service)
            self.service_dir_path_w.custom_signals.serviceUpdated.connect(self.update_fields)
        else:
            self.service_dir_path_w.update_fields()

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
            logger.info(e)
            self.pv_config_data = []
            return

    def expand_table_btn_clicked(self):
        """
        Toggle table expanded by hiding the service status & log frames, allowing the table to fill the remaining
        space.
         """
        # expanded is false -> set visible false (hide) -> expanded = true;
        # expanded is true -> set visible true (show) -> expanded = false;
        self.service_status_frame.setVisible(self.table_expanded)
        self.service_log_panel.setVisible(self.table_expanded)
        self.h_line_one.setVisible(self.table_expanded)
        self.h_line_two.setVisible(self.table_expanded)
        self.table_expanded = not self.table_expanded  # toggle bool
        expand_table_btn_settings = self.expand_table_btn_text[self.table_expanded]  # text and icon depending on table
        self.expand_table_btn.setText(expand_table_btn_settings[0])
        self.expand_table_btn.setIcon(QIcon(os.path.join(ASSETS_PATH, expand_table_btn_settings[1])))

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
            column_of_interest -= 1  # So indexes match (as filters columns comboBox has an extra "All Columns" on 0)
            for rowIndex in range(self.config_table.rowCount()):
                item = self.config_table.item(rowIndex, column_of_interest)
                if value_of_interest in item.text():
                    self.config_table.setRowHidden(rowIndex, False)
                else:
                    self.config_table.setRowHidden(rowIndex, True)

    def clear_filters(self):
        self.filter_columns_cb.setCurrentIndex(0)
        self.filter_bar.clear()
        self.refresh_config()

    def new_config_btn_clicked(self):
        """ Open the Config Entry dialog window. If database is not connected, display error message. """
        if not DBUtils.is_connected():
            QMessageBox.critical(self, 'Database connection required',
                                       'Database connection is required to edit the PV configuration.',
                                       QMessageBox.Ok)
            return

        if self.config_entry_w is None:
            self.config_entry_w = UIConfigEntryDialog()
            self.config_entry_w.config_updated.connect(self.refresh_config)
        self.config_entry_w.show()
        self.config_entry_w.activateWindow()

    def edit_config_btn_clicked(self):
        """ On Edit, open Config Entry dialog window as normal with object selected and PV config loaded. """
        if not DBUtils.is_connected():
            QMessageBox.critical(self, 'Database connection required',
                                       'Database connection is required to edit the PV configuration.',
                                       QMessageBox.Ok)
            return
        if self.config_entry_w is None:
            self.config_entry_w = UIConfigEntryDialog()
            self.config_entry_w.config_updated.connect(self.refresh_config)
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
            id_ = self.config_table.item(row_no, 0)
            obj_ids.append(id_.text())
            name_ = self.config_table.item(row_no, 1)
            obj_list.append(f'(ID: {id_.text()}) {name_.text()}')

        msg_box = DeleteConfigsMessageBox(obj_list=obj_list)
        resp = msg_box.exec()

        if resp == QMessageBox.Ok:
            for item in obj_ids:
                Settings.Service.PVConfig.delete_entry(object_id=int(item))

        self.refresh_config()

    def update_config_table(self):
        """ Update the config table contents with the stored entries' data. """
        self.config_table.setSortingEnabled(False)  # otherwise table will not be properly updated if columns are sorted
        self.config_table.setRowCount(0)            # it will delete the QTableWidgetItems automatically

        pv_config_data = self.pv_config_data        # Get the stored PV config data (from update_config_data)

        for entry in pv_config_data:
            object_id = entry[Settings.Service.PVConfig.OBJ]
            # store the entry data in a list, prepare to add to table as row
            entry_data = [
                object_id,
                DBUtils.get_object_name(object_id),
                DBUtils.get_object_type(object_id, name_only=True),
                DBUtils.get_object_sld(object_id, id_only=True),
                entry[Settings.Service.PVConfig.LOG_PERIOD],
                *[entry[Settings.Service.PVConfig.MEAS].get(x) for x in ['1', '2', '3', '4', '5']]
            ]

            self.config_table.insertRow(self.config_table.rowCount())

            # for each element of the entry data, add it to an item then add the item to the appropriate table cell
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
        if self.config_table.selectedItems():
            self.edit_config_btn.setEnabled(True)
            self.delete_config_btn.setEnabled(True)
        else:
            self.edit_config_btn.setEnabled(False)
            self.delete_config_btn.setEnabled(False)
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
        debug_file_path = Settings.Service.Logging.get_debug_log_path()
        if os.path.exists(debug_file_path):
            os.startfile(debug_file_path)
        else:
            QMessageBox.critical(self, 'Service Log File Not Found',
                                       'The service log file was not found.\n'
                                       f'"{debug_file_path}" does not exist.',
                                       QMessageBox.Ok)
            return

    def update_log_displayed_lines_no(self, value):
        self.thread_service_log.set_displayed_lines_no(value)

    def update_log_font_size(self, value):
        self.service_log_txt.setStyleSheet(f'font-size: {value}pt;')

    def update_service_log_btns(self, enabled: bool):
        self.service_log_file_open_btn.setEnabled(enabled)
        self.service_log_scroll_down_btn.setEnabled(enabled)
        self.service_log_show_lines_spinbox.setEnabled(enabled)
    # endregion

    # region Service Status
    def update_status_title(self, text: str):
        self.service_status_title.setText(text)

    def update_status_style(self, stylesheet: str):
        self.service_status_title.setStyleSheet(stylesheet)

    def update_service_details(self, service: dict):
        self.service_details_name.setText(service['name'])
        self.service_details_status.setText(service['status'])
        self.service_details_pid.setText(f"{service['pid']}")
        self.service_details_startup.setText(service['start_type'])
        self.service_details_description.setText(service['description'])
        self.service_details_username.setText(service['username'])
        self.service_details_binpath.setText(service['binpath'])

    def update_service_control_btns(self, service_status):
        if service_status == 'running':
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(True)
            self.btn_service_restart.setEnabled(True)
        elif service_status == 'stopped':
            self.btn_service_start.setEnabled(True)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)
        elif service_status is None or service_status == 'not found':
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)
        else:
            self.btn_service_start.setEnabled(True)
            self.btn_service_stop.setEnabled(True)
            self.btn_service_restart.setEnabled(True)
    # endregion
    # endregion


class DeleteConfigsMessageBox(QMessageBox):
    """ Message Box on deleting configuration entries. Display a list of entries to be deleted and confirm button. """
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

    def event(self, e):
        result = QMessageBox.event(self, e)
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
