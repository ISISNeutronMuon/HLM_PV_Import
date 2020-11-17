import os
import win32serviceutil
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QMessageBox, QPlainTextEdit, QWidget, QSpinBox, \
    QLineEdit, QLabel
from PyQt5 import uic

from ServiceManager.logger import logger
from ServiceManager.settings import Settings
from ServiceManager.GUI.about import UIAbout
from ServiceManager.GUI.db_settings import UIDBSettings
from ServiceManager.GUI.general_settings import UIGeneralSettings
from ServiceManager.GUI.ca_settings import UICASettings
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.utilities import is_admin
from ServiceManager.GUI.main_window_utils import ServiceLogUpdaterThread, ServiceStatusCheckThread


class UIMainWindow(QMainWindow):
    def __init__(self):
        super(UIMainWindow, self).__init__()

        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts', 'MainWindow.ui')
        uic.loadUi(ui_file_path, self)

        # Update title if app running with admin privileges
        if is_admin():
            self.setWindowTitle(self.windowTitle() + ' (Administrator)')

        # region External windows
        self.about_w = None
        self.db_settings_w = None
        self.general_settings_w = None
        self.ca_settings_w = None
        self.service_dir_path_w = None
        # endregion

        # region Initialize attributes
        Settings.Service.Info.get_name()
        Settings.Service.Logging.get_debug_log_path()
        Settings.Manager.get_service_path()

        self.service_name = None
        self.service_debug_f = None
        self.service_path = None
        # endregion

        # region Menu actions
        self.about_action = self.findChild(QAction, 'actionAbout')
        self.about_action.triggered.connect(self.trigger_about)
        self.show_manager_error_log = self.findChild(QAction, 'actionManager_Error_Log')
        self.show_manager_error_log.triggered.connect(self.trigger_show_manager_error_log)
        self.show_service_debug_log = self.findChild(QAction, 'actionDebug_log')
        self.show_service_debug_log.triggered.connect(self.trigger_open_debug_log)
        self.show_service_dir = self.findChild(QAction, 'actionService_directory')
        self.show_service_dir.triggered.connect(self.trigger_open_service_dir)
        self.db_settings_action = self.findChild(QAction, 'actionDB_Connection')
        self.db_settings_action.triggered.connect(self.trigger_db_settings)
        self.general_settings_action = self.findChild(QAction, 'actionGeneral')
        self.general_settings_action.triggered.connect(self.trigger_general_settings)
        self.ca_settings_action = self.findChild(QAction, 'actionChannel_Access')
        self.ca_settings_action.triggered.connect(self.trigger_ca_settings)
        self.service_directory_action = self.findChild(QAction, 'actionService_Directory')
        self.service_directory_action.triggered.connect(self.trigger_service_directory)
        # endregion

        # region Get widgets
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
        self.btn_service_stop = self.service_status_panel.findChild(QPushButton, 'serviceStop')
        self.btn_service_restart = self.service_status_panel.findChild(QPushButton, 'serviceRestart')
        
        self.service_log_panel = self.findChild(QWidget, 'serviceLog')
        self.service_log_txt = self.service_log_panel.findChild(QPlainTextEdit, 'serviceLogText')
        self.service_log_file_open_btn = self.service_log_panel.findChild(QPushButton, 'openLogFileButton')
        self.service_log_scroll_down_btn = self.service_log_panel.findChild(QPushButton, 'logScrollDownButton')
        self.service_log_show_lines_spinbox = self.service_log_panel.findChild(QSpinBox, 'logLinesSpinBox')

        self.refresh_btn = self.findChild(QPushButton, 'refreshButton')
        # endregion

        # region Connect signals to slots
        self.btn_service_start.clicked.connect(self.service_start_btn_clicked)
        self.btn_service_stop.clicked.connect(self.service_stop_btn_clicked)
        self.btn_service_restart.clicked.connect(self.service_restart_btn_clicked)

        self.service_log_file_open_btn.clicked.connect(self.trigger_open_debug_log)
        self.service_log_scroll_down_btn.clicked.connect(self.log_scroll_down)
        # Emit spinner valueChanged only on return key pressed, focus lost, and arrow key pressed
        self.service_log_show_lines_spinbox.setKeyboardTracking(False)
        self.service_log_show_lines_spinbox.valueChanged.connect(self.update_log_displayed_lines_no)

        self.refresh_btn.clicked.connect(self.refresh_main_window)
        # endregion

        # region Service Status Thread
        # noinspection PyTypeChecker
        self.thread_service_status = ServiceStatusCheckThread(self.service_status_panel)
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

        # region Set buttons
        self.btn_service_start.setEnabled(False)
        self.btn_service_stop.setEnabled(False)
        self.btn_service_restart.setEnabled(False)
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

    # region Other buttons
    def log_scroll_down(self):
        self.service_log_txt.verticalScrollBar(). \
            setValue(self.service_log_txt.verticalScrollBar().maximum())
    # endregion

    # region Action Slots
    def trigger_about(self):
        if self.about_w is None:
            self.about_w = UIAbout()
        self.about_w.show()
        self.about_w.activateWindow()

    @staticmethod
    def trigger_show_manager_error_log():
        error_log_file = Settings.Manager.get_error_log_path()
        os.startfile(error_log_file)

    @staticmethod
    def trigger_open_debug_log():
        debug_file_path = Settings.Service.Logging.get_debug_log_path()
        os.startfile(debug_file_path)

    @staticmethod
    def trigger_open_service_dir():
        service_dir_path = Settings.Manager.get_service_path()
        os.startfile(service_dir_path)

    def trigger_db_settings(self):
        if self.db_settings_w is None:
            self.db_settings_w = UIDBSettings()
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
        else:
            self.service_dir_path_w.update_fields()

        self.service_dir_path_w.exec_()
    # endregion

    # region Events
    def closeEvent(self, event: QCloseEvent):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'HLM PV Import',
                                           quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    # endregion

    def refresh_main_window(self):
        pass

    def update_service(self):
        self.thread_service_log.start()
        self.thread_service_log.update_log()

        self.thread_service_status.start()
        self.thread_service_status.update_status()

    # region Threads

    # region Service Log
    def update_service_log(self, text):
        old_v_scrollbar_value = self.service_log_txt.verticalScrollBar().value()
        old_h_scrollbar_value = self.service_log_txt.horizontalScrollBar().value()

        self.service_log_txt.setPlainText(text)

        self.service_log_txt.verticalScrollBar().setValue(old_v_scrollbar_value)
        self.service_log_txt.horizontalScrollBar().setValue(old_h_scrollbar_value)

    def clear_service_log(self):
        self.service_log_txt.clear()

    def update_log_displayed_lines_no(self, value):
        self.thread_service_log.set_displayed_lines_no(value)

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
        elif service_status is None:
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)
        else:
            self.btn_service_start.setEnabled(True)
            self.btn_service_stop.setEnabled(True)
            self.btn_service_restart.setEnabled(True)
    # endregion

    # endregion
