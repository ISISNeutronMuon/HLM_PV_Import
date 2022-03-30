from PyQt5.QtCore import QObject, QEvent, QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QFont, QMovie, QShowEvent, QCloseEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QMessageBox

from service_manager.constants import loading_animation
from service_manager.logger import manager_logger
from service_manager.utilities import test_pv_connection


class ObjectNameCBFilter(QObject):
    """ Focus events filter for the object name comboBox. """
    focusOut = pyqtSignal()

    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QEvent.FocusOut:
            # Custom actions
            self.focusOut.emit()
        return False  # return False so that the widget will also handle the event


class CheckPVsThread(QThread):
    """ Thread to run the PV connection test. """

    # Signals
    mea_status_update = pyqtSignal(int, bool)
    progress_bar_update = pyqtSignal(int)
    display_progress_bar = pyqtSignal(bool)
    finished_check = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.finished.connect(self._on_finish)
        self.pv_names = None
        self._running = None
        self.results = None

        # If the PV connection test is started from the Save/Add Config button (auto-check before
        # entry add/edit). This is used when the check is started automatically by the Add
        # Configuration/Save button, and automatic PV check is enabled in general settings.
        self._add_entry = False

    def __del__(self):
        self.wait()

    def stop(self):
        self._running = False
        self.exit()

    def _on_finish(self):
        # clear_progress_bar
        self.progress_bar_update.emit(0)
        self.display_progress_bar.emit(False)

        self.finished_check.emit(self._add_entry)

    def set_pv_names(self, pv_names: list):
        self.pv_names = pv_names

    def add_entry_after_check(self, add_entry: bool):
        self._add_entry = add_entry

    def run(self):
        self._running = True
        manager_logger.info(f'Checking connection of measurement PVs: {self.pv_names}')
        connected = []
        failed = []
        self.display_progress_bar.emit(True)
        for index, pv_name in enumerate(self.pv_names):
            if pv_name:
                pv_connected = test_pv_connection(name=pv_name, timeout=2)
                if not self._running:
                    manager_logger.info('Stopped PV connection check.')
                    break
                self.mea_status_update.emit(index, pv_connected)
                if pv_connected:
                    connected.append(pv_name)
                else:
                    failed.append(pv_name)

            self.progress_bar_update.emit(index + 1)

        if self._running:
            manager_logger.info(
                f'PV connection check finished. Connected: {connected}. Failed: {failed}')

        self.results = {'connected': connected, 'failed': failed}


class LoadingPopupWindow(QWidget):
    """ Loading splash screen to display during PV connection auto-check. """

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
    """ Message box displayed on Save/Add Config when the object already has an existing config
    entry. """

    def __init__(self, object_name: str, object_id: int):
        super().__init__()

        self.setWindowTitle('Configuration already exists')
        self.setText(
            f'{object_name} (ID: {object_id}) already has a PV configuration.\n'                  
            f'Overwrite existing configuration?')
        self.setIcon(QMessageBox.Warning)
        self.addButton(QMessageBox.Ok)
        ok_btn = self.button(QMessageBox.Ok)
        ok_btn.setText('Overwrite')
        self.addButton(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)


class ConfigDeleteMessageBox(QMessageBox):
    """ Confirmation message box to display on object config entry deletion within the Config
    Entry dialog window. """

    def __init__(self, object_name: str, object_id: int):
        super().__init__()

        self.setWindowTitle('Delete configuration')
        self.setText(
            f'Deleting configuration for {object_name} (ID: {object_id}).\n'                     
            f'Are you sure?')
        self.setIcon(QMessageBox.Warning)
        self.addButton(QMessageBox.Ok)
        ok_btn = self.button(QMessageBox.Ok)
        ok_btn.setText('Delete')
        self.addButton(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)
