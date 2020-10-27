"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from ca_wrapper import PvMonitors
from pv_functions import get_pv_names, get_pv_value
from user_config import UserConfig
import utilities
from pv_import import PvImport

if __name__ == '__main__':

    # Get the user configuration and the list of measurement PVs
    config = UserConfig()
    pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)
    print(pv_list)

    # Initialize the PV monitoring and set up the monitors for each measurement PV from the user config
    pv_monitors = PvMonitors(pv_list)

    # Initialize and set-up the PV import in charge of preparing the PV data, handling logging periods & tasks,
    # running content checks for the user config, and looping through each record every few seconds to check for
    # records scheduled to be updated with a new measurement.
    pv_import = PvImport(pv_monitors, config)
    pv_import.set_up()

    # Start the monitors and continuously store the PV data received on every update
    pv_monitors.start_monitors()

    # Start the PV import main loop to check each record
    pv_import.start()
