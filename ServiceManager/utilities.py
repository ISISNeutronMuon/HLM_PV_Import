import ctypes
from lxml import etree
import xmltodict
from PyQt5.QtGui import QPalette, QColor


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


def get_config_entries(UserConfig):
    """
    Get all user configuration entries as a dictionary.

    Args:
        UserConfig (UserConfig): The Service UserConfig settings.
    Returns:
        (dict): The PV configurations dictionary.
    """
    config_path = UserConfig.get_path()
    with open(config_path, 'rb') as f:
        config = xmltodict.parse(f.read(), dict_constructor=dict)
        return_val = config[UserConfig.ROOT][UserConfig.ENTRY]
        return return_val

