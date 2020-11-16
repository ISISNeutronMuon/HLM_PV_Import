import os
import time
import psutil
import win32serviceutil
from collections import deque, defaultdict
from PyQt5.QtCore import QTimer, QThread, QEventLoop, QCoreApplication
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QLabel, QListWidget, QMessageBox, \
    QPlainTextEdit, QWidget, QLineEdit, QApplication, QSpinBox
from PyQt5 import uic
from ServiceManager.settings import Settings
from ServiceManager.GUI.about import UIAbout
from ServiceManager.GUI.db_settings import UIDBSettings
from ServiceManager.GUI.general_settings import UIGeneralSettings
from ServiceManager.GUI.ca_settings import UICASettings
from ServiceManager.GUI.service_path_dlg import UIServicePathDialog
from ServiceManager.utilities import is_admin


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
        self.service_dir_w = None
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
        self.btn_service_start = self.service_status_panel.findChild(QPushButton, 'serviceStart')
        self.btn_service_stop = self.service_status_panel.findChild(QPushButton, 'serviceStop')
        self.btn_service_restart = self.service_status_panel.findChild(QPushButton, 'serviceRestart')
        self.service_log = self.findChild(QWidget, 'serviceLog')
        self.service_log_txt = self.service_log.findChild(QPlainTextEdit, 'serviceLogText')
        self.service_log_file_open_btn = self.service_log.findChild(QPushButton, 'openLogFileButton')
        self.service_log_scroll_down_btn = self.service_log.findChild(QPushButton, 'logScrollDownButton')
        self.service_log_show_lines_spinbox = self.service_log.findChild(QSpinBox, 'logLinesSpinBox')
        # endregion

        # region Connect signals to slots
        self.btn_service_start.clicked.connect(self.service_start_btn_clicked)
        self.btn_service_stop.clicked.connect(self.service_stop_btn_clicked)
        self.btn_service_restart.clicked.connect(self.service_restart_btn_clicked)

        self.service_log_file_open_btn.clicked.connect(self.trigger_open_debug_log)
        self.service_log_scroll_down_btn.clicked.connect(self.log_scroll_down)
        # endregion

        # region Service Status Thread
        # noinspection PyTypeChecker
        self.service_status_thread = ServiceStatusCheckThread(self.service_status_panel)
        self.service_status_thread.start()
        # endregion

        # region Service Log Thread
        # noinspection PyTypeChecker
        self.log_updater_thread = ServiceLogUpdaterThread(self.service_log)
        self.log_updater_thread.start()
        # endregion

        # region Admin mode only buttons
        if not is_admin():
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)
        # endregion

    # region Service control buttons slots
    @staticmethod
    def service_start_btn_clicked():
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.StartService(service_name)

    @staticmethod
    def service_stop_btn_clicked():
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.StopService(service_name)

    @staticmethod
    def service_restart_btn_clicked():
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.RestartService(service_name)
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
        if self.service_dir_w is None:
            self.service_dir_w = UIServicePathDialog()
        self.service_dir_w.show()
        self.service_dir_w.activateWindow()
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


class ServiceLogUpdaterThread(QThread):
    def update_log(self):
        debug_log_path = Settings.Service.Logging.get_debug_log_path()
        last_modified = os.path.getmtime(debug_log_path)
        # if log file was modified since last log widget update, update widget text
        if last_modified > self.last_widget_update:
            with open(debug_log_path) as file:
                show_lines_number = self.service_log_show_lines.value()
                text = ''.join(deque(file, show_lines_number))
                old_v_scrollbar_value = self.service_log.verticalScrollBar().value()
                old_h_scrollbar_value = self.service_log.horizontalScrollBar().value()
                self.service_log.setPlainText(text)
                self.service_log.verticalScrollBar().setValue(old_v_scrollbar_value)
                self.service_log.horizontalScrollBar().setValue(old_h_scrollbar_value)
                self.last_widget_update = time.time()

    def __init__(self, log_widget: QWidget, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.log_widget = log_widget
        self.service_log = self.log_widget.findChild(QPlainTextEdit, 'serviceLogText')
        self.service_log_show_lines = self.log_widget.findChild(QSpinBox, 'logLinesSpinBox')

        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.timer.timeout.connect(self.update_log)
        self.last_widget_update = 0

    def run(self):
        self.update_log()
        self.timer.start(1*1000)
        loop = QEventLoop()
        loop.exec_()


class ServiceStatusCheckThread(QThread):
    def update_status(self):
        # Get service details
        service_name = Settings.Service.Info.get_name()
        service = psutil.win_service_get(service_name)
        service = service.as_dict()

        main_msg = f"{service['display_name']} is {service['status'].upper()}"
        self.main_status_msg.setText(main_msg)
        self.update_status_title_style(service['status'])

        self.update_service_details(service)

        if is_admin():
            self.update_service_control_buttons(service['status'])

    def __init__(self, widget: QWidget, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.timer.timeout.connect(self.update_status)

        # region Get widget components
        self.widget = widget
        self.main_status_msg = self.widget.findChild(QLabel, 'statusMessage')
        self.name_msg = self.widget.findChild(QLineEdit, 'nameText')
        self.status_small_msg = self.widget.findChild(QLineEdit, 'statusText')
        self.pid_msg = self.widget.findChild(QLineEdit, 'pidText')
        self.startup_type_msg = self.widget.findChild(QLineEdit, 'startUpTypeText')
        self.description_msg = self.widget.findChild(QLineEdit, 'descriptionText')
        self.username_msg = self.widget.findChild(QLineEdit, 'usernameText')
        self.binpath_msg = self.widget.findChild(QLineEdit, 'binPathText')
        self.btn_service_start = self.widget.findChild(QPushButton, 'serviceStart')
        self.btn_service_stop = self.widget.findChild(QPushButton, 'serviceStop')
        self.btn_service_restart = self.widget.findChild(QPushButton, 'serviceRestart')
        # endregion

        # region Styles
        self.status_color = defaultdict(lambda: '#ffff00')  # electric yellow
        self.status_color['running'] = '#90ee90'  # medium light shade of green
        self.status_color['stopped'] = '#add8e6'  # light shade of cyan
        # endregion

    def run(self):
        self.update_status()
        self.timer.start(5*1000)
        loop = QEventLoop()
        loop.exec_()

    def update_service_control_buttons(self, service_status):
        if service_status == 'running':
            self.btn_service_start.setEnabled(False)
            self.btn_service_stop.setEnabled(True)
            self.btn_service_restart.setEnabled(True)
        elif service_status == 'stopped':
            self.btn_service_start.setEnabled(True)
            self.btn_service_stop.setEnabled(False)
            self.btn_service_restart.setEnabled(False)
        else:
            self.btn_service_start.setEnabled(True)
            self.btn_service_stop.setEnabled(True)
            self.btn_service_restart.setEnabled(True)

    def update_status_title_style(self, status):
        style = f'background-color: {self.status_color[status]};' \
                f'padding: 20px;'
        self.main_status_msg.setStyleSheet(style)

    def update_service_details(self, service):
        self.name_msg.setText(service['name'])
        self.status_small_msg.setText(service['status'])
        self.pid_msg.setText(f"{service['pid']}")
        self.startup_type_msg.setText(service['start_type'])
        self.description_msg.setText(service['description'])
        self.username_msg.setText(service['username'])
        self.binpath_msg.setText(service['binpath'])
