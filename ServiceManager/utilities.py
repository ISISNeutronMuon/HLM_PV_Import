import configparser
import ctypes
import os

from PyQt5.QtGui import QPalette, QColor
from ServiceManager.logger import manager_logger
from caproto.sync.client import read


def test_pv_connection(name: str, timeout: int = 1):
    """
    Tests whether CA can connect to a PV and get its value.

    Args:
        name (str): The PV.
        timeout (int, optional): PV connection timeout in seconds, Defaults to 1.

    Returns:
        (boolean): True if connected, False otherwise.

    Raises:
        CaprotoTimeoutError: If establishing the connection to the PV timed out.
    """

    try:
        read(pv_name=name, timeout=timeout)
    except Exception as e:
        manager_logger.error(e)
        return False

    return True


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


def setup_settings_file(path: str, template: dict, parser: configparser.ConfigParser):
    """
    Creates the settings file and its directory, if it doesn't exist, and writes the given config template with
    blank values to it.

    Args:
        path (str): The full path to the file.
        template (dict): The template containing sections (keys, str) and their options (values, list of str).
        parser (ConfigParser): The ConfigParser object.
    """
    # Create file and directory if not exists and write config template to it with blank values
    settings_dir = os.path.dirname(path)
    if not os.path.exists(settings_dir):  # If settings directory does not exist either, create it too
        os.makedirs(settings_dir)

    for section, options in template.items():
        parser.add_section(section)
        for option_key, option_val in options.items():
            parser[f'{section}'][f'{option_key}'] = option_val
    with open(path, 'w') as settings_file:
        parser.write(settings_file)
