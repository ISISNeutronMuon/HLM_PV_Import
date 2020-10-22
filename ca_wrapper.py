"""
Wrap caproto to give utilities methods for access in one place
"""
from caproto import CaprotoTimeoutError
from caproto.sync.client import read
from caproto.threading.client import Context
from err_logger import log_ca_error

TIMEOUT = 3  # Default timeout for reading a PV


class PvMonitors:
    """
    Class for monitoring PV channels and storing their data in a dict.
    """

    def __init__(self, pv_name_list: list):
        self.ctx = Context()
        self._pv_data = {}
        self.pv_name_list = pv_name_list
        self.subscriptions = {}

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
        print('Received response from', sub.pv.name)
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
            sub = pv.subscribe()
            token = sub.add_callback(self._callback_f)
            self.subscriptions[pv.name] = {'token': token, 'sub': sub}

    def remove_pv(self, pv_name):
        """
        Clears the callback and removes the PV from the PV Data dict.
        """
        self.clear_callbacks(pv_name)
        self._pv_data.pop(pv_name, None)

    def clear_callbacks(self, pv_name):
        """
        Cancel future updates by clearing all callbacks on the subscription of the specified PV.

        Args:
            pv_name (str): The full PV name.
        """
        sub = self.subscriptions[pv_name]['sub']
        sub.clear()

    def add_callback(self, pv_name, callback_f=None):
        """
        Initiate updates by adding a user callback to the subscription of the specified PV.
        If only the PV name is given, add the default callback.

        Args:
            pv_name (str): The full PV name.
            callback_f (optional): The user callback function to add, Defaults to None (Default func).
        """
        sub = self.subscriptions[pv_name]['sub']

        if not callback_f:
            sub.add_callback(self._callback_f)
        else:
            sub.add_callback(callback_f)


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
    except CaprotoTimeoutError as e:
        log_ca_error(pv_name=name, err=f'{e}', print_err=True)
        raise
    return res
