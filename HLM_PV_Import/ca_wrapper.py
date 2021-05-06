"""
Wrap caproto to give utilities methods for access in one place
"""
from caproto import CaprotoTimeoutError
from caproto.sync.client import read
from caproto.threading.client import Context
from HLM_PV_Import.logger import pv_logger, logger
from HLM_PV_Import.settings import CA
import time

# Default timeout for reading a PV
TIMEOUT = CA.CONN_TIMEOUT

# time in s after which PV data is considered stale and will no longer be considered when adding a measurement
STALE_AGE = CA.STALE_AFTER


def get_connected_pvs(pv_list, timeout=TIMEOUT):
    """
    Returns a list of connected PVs from the given PV list.

    Args:
        pv_list (list): The full PV names list.
        timeout (int, optional): PV connection timeout.

    Returns:
        (list): The connected PVs.
    """

    ctx = Context()
    pvs = ctx.get_pvs(*pv_list, timeout=timeout)
    time.sleep(timeout)

    return [pv.name for pv in pvs if pv.connected]


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
        logger.error(f"Unable to connect to PV '{name}': {e}")
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
        self._pv_data = {}  # full PV name and last update value
        self._pv_last_update = {}  # full PV name and last update time
        self.pv_name_list = pv_name_list  # list of PVs to monitor
        self.subscriptions = {}
        self._channel_data = []

    def get_pv_data(self, pv_name):
        return self._pv_data[pv_name]

    def _callback_f(self, sub, response):
        """
        Stash the PV Name/Value results in the data dictionary, and the Name/Last Update in another.

        Args:
            sub (caproto.threading.client.Subscription): The subscription, also containing the pertinent PV
                                                            and its name.
            response (caproto._commands.EventAddResponse): The full response from the server, which includes data
                                                            and any metadata.
        """
        value = response.data[0]

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        name = sub.pv.name
        self._pv_data[name] = value  # store the PV name and data
        self._pv_last_update[name] = time.time()  # as well as the time of update

    def start_monitors(self):
        """
        Subscribe to channel updates of all PVs in the name list.
        """
        self._channel_data = self.ctx.get_pvs(*self.pv_name_list)
        for pv in self._channel_data:
            sub = pv.subscribe()
            sub.add_callback(self._callback_f)
            self.subscriptions[pv.name] = sub

    def pv_data_is_stale(self, pv_name):
        """
        Checks whether a PVs data is stale or not, by looking at the time since its last update and the set length of
        time after which a PV is considered stale.

        Args:
            pv_name (str): The name of the PV.

        Returns:
            (boolean): True if data is stale, False if not.
        """
        last_update = self._pv_last_update[pv_name]
        current_time = time.time()
        time_since_last_update = current_time - last_update
        if time_since_last_update >= STALE_AGE:
            pv_logger.warning(f"Stale PV: '{pv_name}' has not received updates for "
                              f"{'{:.1f}'.format(time_since_last_update)} seconds.")
            return True
        return False
