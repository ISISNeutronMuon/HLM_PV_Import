from PyQt5.QtCore import QTimer, QThread, QEventLoop
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QLabel, QListWidget, QMessageBox,\
    QPlainTextEdit
from PyQt5 import uic
import os
import time
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
        self.button = self.findChild(QPushButton, 'pushButton')
        self.button.clicked.connect(self.pushButtonPressed)
        self.pv_list = self.findChild(QListWidget, 'listWidget')

        self.service_log_txt = self.findChild(QPlainTextEdit, 'serviceLogText')
        # endregion

        # region Service Status Thread
        # todo: service status
        # self.service_status_thread = ServiceStatusCheckThread()
        # self.service_status_thread.start()

        # region Service Log Thread
        self.log_updater_thread = ServiceLogUpdaterThread(self.service_log_txt)
        self.log_updater_thread.start()
        # endregion

    def pushButtonPressed(self):
        print('printButtonPressed')
        self.pv_list.addItem('wow')


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
                text = file.read()
                self.log_widget.setPlainText(text)
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
        self.timer.start(1*1000)
        loop = QEventLoop()
        loop.exec_()


class ServiceStatusCheckThread(QThread):
    def update_status(self):
        pass

    def __init__(self, widget, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.widget = widget
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.timer.timeout.connect(self.update_status)

    def run(self):
        self.timer.start(1*1000)
        loop = QEventLoop()
        loop.exec_()

