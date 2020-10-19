"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from ca_wrapper import PvMonitors
from pv_functions import get_pv_names
import utilities
from pv_import import PvImport

if __name__ == '__main__':

    pv_list = get_pv_names()
    # pv_list = get_config_pv_names(full_names=True)
    pv_monitors = PvMonitors(pv_list)
    pv_import = PvImport(pv_monitors)

    pv_import.set_up()

    pv_monitors.start_monitors()

    pv_import.start()
