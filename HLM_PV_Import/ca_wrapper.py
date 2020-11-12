"""
Wrap caproto to give utilities methods for access in one place
"""
from caproto import CaprotoTimeoutError
from caproto.sync.client import read
from caproto.threading.client import Context
from HLM_PV_Import.logger import log_ca_error, log_stale_pv_warning
from HLM_PV_Import.constants import CA, PvImportConfig
import time

# Default timeout for reading a PV
TIMEOUT = CA.CONN_TIMEOUT
# time in s after which a PV's data is considered stale and will no longer be considered when adding a measurement
TIME_AFTER_STALE = PvImportConfig.STALE_AFTER


def get_connected_pvs(pv_list, timeout=TIMEOUT):
    """
    Returns a list of connected PVs from the given PV list.

    Args:
        pv_list (list): The full PV names list.
        timeout (int, optional): PV connection timeout.

    Returns:
        (list): The connected PVs.
    """
    connected_pvs = []

    ctx = Context()
    pvs = ctx.get_pvs(*pv_list, timeout=timeout)
    time.sleep(timeout)

    for pv in pvs:
        if pv.connected:
            connected_pvs.append(pv.name)

    return connected_pvs


def get_pv_value(name, timeout=TIMEOUT):
    """
    Get the current value of the PV.

    Args:
        name (str): The PV.
        timeout (int, optional): PV connection timeout.

    Returns:
        The PV value.

    Raises:
        CaprotoTimeoutError: If cannot connect to PV.
    """

    try:
        res = read(pv_name=name, timeout=timeout)
    except CaprotoTimeoutError as e:
        log_ca_error(pv_name=name, err=f'{e}', print_err=True)
        raise

    value = res.data[0]

    if isinstance(value, bytes):
        value = value.decode('utf-8')

    return value


class PvMonitors:
    """
    Monitor PV channels and continuously store updates data.
    """

    def __init__(self, pv_name_list: list):
        self.ctx = Context()
        self._pv_data = {}                               # full PV name and last update value
        self._pv_last_update = {}                        # full PV name and last update time
        self.pv_name_list = pv_name_list                 # list of PVs to monitor
        self.subscriptions = {}
        self._channel_data = []

    def get_data(self):
        return self._pv_data

    def _callback_f(self, sub, response):
        """
        Stash the PV Name/Value results in the data dictionary, and the Name/Last Update in another.

        Args:
            sub (caproto.threading.client.Subscription): The subscription, also containing the pertinent PV
                                                            and its name.
            response (caproto._commands.EventAddResponse): The full response from the server, which includes data
                                                            and any metadata.
        """
        print(f'Received response from {sub.pv.name}')
        value = response.data[0]

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        name = sub.pv.name
        self._pv_data[name] = value                     # store the PV name and data
        self._pv_last_update[name] = time.time()        # as well as the time of update

    def start_monitors(self):
        """
        Subscribe to channel updates of all PVs in the name list.
        """
        self._channel_data = self.ctx.get_pvs(*self.pv_name_list)
        for pv in self._channel_data:
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
        If no callback function was specified, use the default callback.

        Args:
            pv_name (str): The full PV name.
            callback_f (optional): The user callback function to add, Defaults to default callback.
        """
        sub = self.subscriptions[pv_name]['sub']

        if not callback_f:
            sub.add_callback(self._callback_f)
        else:
            sub.add_callback(callback_f)

    def pv_data_is_stale(self, pv_name, print_warning=False):
        """
        Checks whether a PVs data is stale or not, by looking at the time since its last update and the set length of
        time after which a PV is considered stale.

        Args:
            pv_name (str): The name of the PV.
            print_warning (boolean, optional): Print a warning message to console if PV is stale, Defaults to False.

        Returns:
            (boolean): True if data is stale, False if not.
        """
        last_update = self._pv_last_update[pv_name]
        current_time = time.time()
        time_since_last_update = current_time - last_update
        if time_since_last_update >= TIME_AFTER_STALE:
            log_stale_pv_warning(pv_name, time_since_last_update, print_err=print_warning)
            return True
        else:
            return False
