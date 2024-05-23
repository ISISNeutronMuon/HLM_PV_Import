import configparser
import ctypes
import os

from PyQt5.QtCore import QObject, QSize
from PyQt5.QtGui import QPalette, QColor, QCloseEvent, QIcon
from PyQt5.QtWidgets import QMessageBox, QPushButton

from service_manager.constants import ASSETS_PATH
from service_manager.logger import manager_logger
from caproto.sync.client import read

from shared.const import DBClassIDs


def test_pv_connection(name: str, timeout: int = 1):
    """
    Tests whether CA can connect to a PV and get its value.

    Args:
        name (str): The PV.
        timeout (int, optional): PV connection timeout in seconds, Defaults to 1.

    Returns:
        (boolean): True if connected, False otherwise.
    """

    try:
        read(pv_name=name, timeout=timeout)
        return True
    except Exception as e:
        manager_logger.error(e)
        return False


def is_admin():
    # noinspection PyBroadException
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        manager_logger.error(e)
        return False


def make_bold(widget, bold):
    """
    Takes a QtWidget object and sets it font to bold/normal.

    Args:
        widget (QtWidget): The widget.
        bold (bool): True for Bold, False for Normal.
    """
    font = widget.font()
    font.setBold(bold)
    widget.setFont(font)


def set_colored_text(label, text, color):
    """
    Set the given color and text to a QWidget.

    Args:
        label (QObject): The QLabel.
        text (str): The text.
        color (QColor): The QColor.
    """
    pal = label.palette()
    pal.setColor(QPalette.WindowText, color)
    label.setPalette(pal)
    label.setText(text)


def set_red_border(frame: QObject, highlight: bool = True):
    frame.setStyleSheet(
        f"QObject#{frame.objectName()} {{{'border: 1px solid red;' if highlight else ''}}}")


def setup_settings_file(path: str, template: dict, parser: configparser.ConfigParser):
    """
    Creates the settings file and its directory, if it doesn't exist, and writes the given config
    template with blank values to it.

    Args:
        path (str): The full path to the file.
        template (dict): The template containing sections (keys, str) and their options (values,
        list of str).
        parser (ConfigParser): The ConfigParser object.
    """
    # Create file and directory if not exists and write config template to it with blank values
    settings_dir = os.path.dirname(path)
    if not os.path.exists(
            settings_dir):  # If settings directory does not exist either, create it too
        os.makedirs(settings_dir)

    for section, options in template.items():
        parser.add_section(section)
        for option_key, option_val in options.items():
            parser[f'{section}'][f'{option_key}'] = option_val
    with open(path, 'w') as settings_file:
        parser.write(settings_file)


def apply_unsaved_changes_dialog(event: QCloseEvent, apply_settings_func, settings_changed):
    if settings_changed:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Any changes will be lost.\nApply settings?")
        msg.setWindowTitle('Unsaved changes')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        reply = msg.exec_()

        if reply == QMessageBox.Cancel:
            event.ignore()
        else:
            if reply == QMessageBox.Yes:
                apply_settings_func()
            event.accept()


def setup_button(button: QPushButton, icon_name: str = None):
    if icon_name:
        button.setIcon(QIcon(os.path.join(ASSETS_PATH, icon_name)))
    button.setIconSize(QSize(15, 15))
    button.setStyleSheet("QPushButton { text-align: left; }")


def generate_module_name(object_name: str, object_id: int, object_class: int):
    if object_class in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT]:
        return f'SLD "{object_name}" (ID: {object_id})'
    elif object_class == DBClassIDs.GAS_COUNTER:
        return f'GCM "{object_name}" (ID: {object_id})'
