import ctypes
from PyQt5.QtGui import QPalette, QColor
from ServiceManager.logger import logger
from caproto import CaprotoTimeoutError
from caproto.sync.client import read


def get_pv_value(name: str, timeout: int = 1):
    """
    Get the current value of the PV.

    Args:
        name (str): The PV.
        timeout (int, optional): PV connection timeout in seconds, Defaults to 1.

    Returns:
        (str): The PV value.

    Raises:
        CaprotoTimeoutError: If establishing the connection to the PV timed out.
    """

    try:
        res = read(pv_name=name, timeout=timeout)
    except CaprotoTimeoutError as e:
        logger.info(e)
        raise

    value = res.data[0]

    if isinstance(value, bytes):
        value = value.decode('utf-8')

    return value


def is_admin():
    # noinspection PyBroadException
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logger.warning(e)
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
