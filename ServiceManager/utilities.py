import ctypes
import json
from PyQt5.QtGui import QPalette, QColor
from ServiceManager.settings import Settings
from ServiceManager.logger import logger


def is_admin():
    # noinspection PyBroadException
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
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


def single_tuples_to_strings(tuple_list):
    """
    Given a list of tuples, convert all single-element tuples into a string of the first element. Tuples in the list
    with multiple elements will not be affected.

    Args:
        tuple_list (list): the list of tuples to convert
    Returns:
        (list) the list of strings made from the first element of the tuples

    """

    string_list = []
    for elem in tuple_list:
        if len(elem) == 1:
            string_list.append(elem[0])
        else:
            string_list.append(elem)
    return string_list


def get_config_entries():
    """
    Get all user configuration entries as a dictionary.

    Returns:
        (dict): The PV configurations dictionary.
    """
    config_file = Settings.Service.PVConfig.get_path()
    with open(config_file) as f:
        data = json.load(f)
        data = data[Settings.Service.PVConfig.ROOT]

        if not data:
            logger.info('PV configuration file is empty.')
        return data


def add_config_entry(new_entry: dict):
    """
    Add a new record config entry to PV Config.

    Args:
        new_entry  (dict): The record config.
    """
    config_file = Settings.Service.PVConfig.get_path()
    data = get_config_entries()
    print(data)
