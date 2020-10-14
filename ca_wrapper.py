"""
Wrap caproto to give utilities methods for access in one place
"""
import caproto
from caproto.sync.client import read
from err_logger import log_ca_error
from caproto.threading.client import Context

TIMEOUT = 3  # Default timeout for reading a PV


class PvMonitoring:
    """
    Class for monitoring PV channels and storing their data in a dict.
    """

    def __init__(self, pv_name_list):
        self.ctx = Context()
        self._pv_data = {}
        self.pv_name_list = pv_name_list

    def get_data(self):
        return self._pv_data

    def _callback_f(self, sub, response):
        """
        Stash the PV Name/Value results in a dictionary.

        Args:
            sub (caproto.threading.client.Subscription): The subscription, also containing the pertinent PV
                                                            and its name.
            response (caproto._commands.EventAddResponse): The full response from the server, which includes data
                                                            and any metadata.
        """
        # print('Received response from', sub.pv.name)
        value = response.data[0]

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        name = sub.pv.name
        self._pv_data[name] = value

    def start_monitors(self):
        """
        Subscribe to channel updates of all PVs in the name list.
        """
        channel_data = self.ctx.get_pvs(*self.pv_name_list)

        for pv in channel_data:
            pv.subscribe().add_callback(self._callback_f)


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
