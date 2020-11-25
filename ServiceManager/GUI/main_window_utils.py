import os
import time
import psutil
from collections import deque, defaultdict
from PyQt5.QtCore import QTimer, QThread, QEventLoop, pyqtSignal
from ServiceManager.logger import logger
from ServiceManager.settings import Settings
from ServiceManager.utilities import is_admin


class ServiceLogUpdaterThread(QThread):

    # Custom signals
    log_fetched = pyqtSignal(str)
    file_not_found = pyqtSignal()
    enable_or_disable_buttons = pyqtSignal(bool)

    def update_log(self):
        debug_log_path = Settings.Service.Logging.get_debug_log_path()
        try:
            last_modified = os.path.getmtime(debug_log_path)
        except FileNotFoundError as e:
            # todo: test what happens on debug file rotate
            logger.info(e)
            self.enable_or_disable_buttons.emit(False)
            self.file_not_found.emit()
            self.last_widget_update = 0
            self.stop()
            return
        # if log file was modified since last log widget update, update widget text
        if last_modified > self.last_widget_update:
            with open(debug_log_path) as file:
                text = ''.join(deque(file, self.displayed_lines_no))
                self.log_fetched.emit(text)
                self.last_widget_update = time.time()

    def __init__(self, display_lines_no, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.finished.connect(self.timer.stop)  # When thread is finished, stop timer
        self.timer.timeout.connect(self.update_log)
        self.last_widget_update = 0
        self.displayed_lines_no = display_lines_no

    def set_displayed_lines_no(self, lines_no):
        self.displayed_lines_no = lines_no
        if self.isRunning():
            self.last_widget_update = 0
            self.update_log()

    def run(self):
        self.enable_or_disable_buttons.emit(True)
        self.update_log()
        self.timer.start(1 * 1000)
        loop = QEventLoop()
        loop.exec_()

    def stop(self):
        self.exit()


class ServiceStatusCheckThread(QThread):

    # Custom signals
    update_status_title = pyqtSignal(str)
    update_status_style = pyqtSignal(str)
    update_service_details = pyqtSignal(dict)
    update_service_control_btns = pyqtSignal(str)

    def update_status(self):
        # Get service details
        service_name = Settings.Service.Info.get_name()
        try:
            service = psutil.win_service_get(service_name)
        except psutil.NoSuchProcess as e:
            logger.info(e)
            self.update_status_title.emit(f"Service {service_name} not found")
            stylesheet = f"background-color: {self.status_color[None]}; padding: 20px;"
            self.update_status_style.emit(stylesheet)
            self.update_service_details.emit(self.none_dict)
            self.stop()
            return

        service_info = service.as_dict()
        status = service_info['status']
        status_msg = f"{service_info['display_name']} is {status.upper()}"
        self.update_status_title.emit(status_msg)

        stylesheet = f"background-color: {self.status_color[status]}; padding: 20px;"
        self.update_status_style.emit(stylesheet)

        self.update_service_details.emit(service_info)

        if is_admin():
            self.update_service_control_btns.emit(status)

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.moveToThread(self)
        self.finished.connect(self.timer.stop)  # When thread is finished, stop timer
        self.timer.timeout.connect(self.update_status)

        # region Styles
        self.status_color = defaultdict(lambda: '#ffff00')  # electric yellow
        self.status_color['running'] = '#90ee90'  # medium light shade of green
        self.status_color['stopped'] = '#add8e6'  # light shade of cyan
        # endregion

        self.none_dict = defaultdict(lambda: None)

    def run(self):
        self.update_status()
        self.timer.start(5 * 1000)
        loop = QEventLoop()
        loop.exec_()

    def stop(self):
        self.exit()
