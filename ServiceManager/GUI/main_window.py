import os
import time
import psutil
from collections import deque, defaultdict
from PyQt5.QtCore import QTimer, QThread, QEventLoop
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QLabel, QListWidget, QMessageBox, \
    QPlainTextEdit, QWidget, QLineEdit
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
        self.open_debug_log = self.findChild(QAction, 'actionDebug_log')
        self.open_debug_log.triggered.connect(self.trigger_open_debug_log)
        self.open_service_dir = self.findChild(QAction, 'actionService_directory')
        self.open_service_dir.triggered.connect(self.trigger_open_service_dir)
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
        self.service_details = self.findChild(QWidget, 'serviceDetails')
        self.service_log_txt = self.findChild(QPlainTextEdit, 'serviceLogText')
        # endregion

        # region Service Status Thread
        # noinspection PyTypeChecker
        self.service_status_thread = ServiceStatusCheckThread(self.service_details)
        self.service_status_thread.start()
        # endregion

        # region Service Log Thread
        self.log_updater_thread = ServiceLogUpdaterThread(self.service_log_txt)
        self.log_updater_thread.start()
        # endregion

    # region Action Slots
    def trigger_about(self):
        if self.about_w is None:
            self.about_w = UIAbout()
        self.about_w.show()
        self.about_w.activateWindow()

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
        last_modified = os.path.getmtime(self.debug_log_path)
        # if log file was modified since last log widget update, update widget text
        if last_modified > self.last_widget_update:
            with open(self.debug_log_path) as file:
                text = ''.join(deque(file, 15))
                self.log_widget.setPlainText(text)
                self.log_widget.verticalScrollBar().\
                    setValue(self.log_widget.verticalScrollBar().maximum())
                self.last_widget_update = time.time()

    def __init__(self, log_widget, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.log_widget = log_widget
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.timer.timeout.connect(self.update_log)
        self.last_widget_update = 0
        self.debug_log_path = Settings.Service.Logging.get_debug_log_path()

    def run(self):
        self.update_log()
        self.timer.start(1*1000)
        loop = QEventLoop()
        loop.exec_()


class ServiceStatusCheckThread(QThread):
    def update_status(self):
        # Get service details
        service = psutil.win_service_get(self.service_name)
        service = service.as_dict()

        main_msg = f"{service['display_name']} is {service['status'].upper()}"
        self.main_status_msg.setText(main_msg)
        self.style_status_msg(service['status'])

        self.set_details(service)

    def __init__(self, widget: QWidget, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.timer.timeout.connect(self.update_status)
        self.service_name = Settings.Service.Info.get_name()

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

    def style_status_msg(self, status):
        style = f'background-color: {self.status_color[status]}'
        self.main_status_msg.setStyleSheet(style)

    def set_details(self, service):
        self.name_msg.setText(service['name'])
        self.status_small_msg.setText(service['status'])
        self.pid_msg.setText(service['pid'])
        self.startup_type_msg.setText(service['start_type'])
        self.description_msg.setText(service['description'])
        self.username_msg.setText(service['username'])
        self.binpath_msg.setText(service['binpath'])
