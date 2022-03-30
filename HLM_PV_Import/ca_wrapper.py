"""
Wrap caproto to give utilities methods for access in one place
"""
import json
import time

from caproto.threading.client import Context
from caproto.sync.client import read
from caproto import CaprotoError

from hlm_pv_import.logger import pv_logger, logger
from hlm_pv_import.settings import CA
from hlm_pv_import.utils import dehex_and_decompress, ints_to_string

# Default timeout for reading a PV
TIMEOUT = CA.CONN_TIMEOUT

# time in s after which PV data is considered stale and will no longer be considered when adding a measurement
STALE_AGE = CA.STALE_AFTER

# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"


def get_instrument_list():
    """
    Retrieve the instrument list.

    Returns:
       (list): instruments with their host names
    """
    err_msg = "Error getting instrument list:"

    try:
        bytes_data = read(INST_LIST_PV).data
        raw = ints_to_string([int(x) for x in bytes_data])
    except CaprotoError as e:
        logger.error(f"{err_msg} {e}")
        return []

    try:
        full_inst_list_string = dehex_and_decompress(raw)
        full_inst_list = json.loads(full_inst_list_string)
    except Exception as e:
        logger.error(f"{err_msg} {e}")
        return []

    return full_inst_list


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
        time_since_last_update = self.get_time_since_last_update(pv_name)
        if time_since_last_update >= STALE_AGE:
            pv_logger.warning(f"Stale PV: '{pv_name}' has not received updates for "
                              f"{'{:.1f}'.format(time_since_last_update)} seconds.")
            return True
        return False

    def get_time_since_last_update(self, pv_name):
        """
        Returns how much time in seconds has passed since the given PV's last update.

        Args:
            pv_name (str): The PV name

        Returns:
            (int): Time in seconds since last update
        """
        return time.time() - self._pv_last_update[pv_name]
