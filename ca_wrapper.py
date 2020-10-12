"""
Wrap caproto to give utilities methods for access in one place
"""
import caproto
from caproto.sync.client import read
from ca_logger import log_ca_error

TIMEOUT = 3  # Default timeout for PV get


def get_pv_value(name, timeout=TIMEOUT):
    """
    Get the current value of the PV.

    Args:
        name (str): The PV.
        timeout (optional): How long to wait for the PV to connect etc.

    Returns:
        The PV value.

    Raises:
        UnableToConnectToPVException: If cannot connect to PV.
    """

    res = get_chan(name, timeout)
    value = res.data[0]

    if isinstance(value, bytes):
        value = value.decode('utf-8')

    return value


def get_chan(name, timeout):
    """
    Gets a channel based on a channel name.

    Args:
        name (str): the name of the channel to get
        timeout (int): timeout to set on channel

    Returns:
        ReadNotifyResponse caproto object containing channel data and more.
    """
    try:
        res = read(pv_name=name, timeout=timeout)
    except caproto.sync.client.CaprotoTimeoutError as e:
        log_ca_error(pv_name=name, err=f'{e}', print_err=True)
        raise
    return res
