"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from ca_wrapper import PvMonitors
from pv_functions import get_pv_names, get_pv_value
from user_config import UserConfig
import utilities
from pv_import import PvImport

if __name__ == '__main__':

    # pv_list = get_pv_names()
    config = UserConfig()
    pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)
    print(pv_list)
    pv_monitors = PvMonitors(pv_list)
    pv_import = PvImport(pv_monitors, config)

    pv_import.set_up()

    pv_monitors.start_monitors()

    pv_import.start()
