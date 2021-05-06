"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from HLM_PV_Import.ca_wrapper import PvMonitors
from HLM_PV_Import.user_config import UserConfig
from HLM_PV_Import.pv_import import PvImport
from HLM_PV_Import.settings import CA
from HLM_PV_Import.logger import logger
import os
import sys

this = sys.modules[__name__]

this.pv_import = None


def main():
    # Setup the channel access address list in order to connect to PVs
    os.environ['EPICS_CA_ADDR_LIST'] = CA.EPICS_CA_ADDR_LIST

    # Get the user configuration and the list of measurement PVs
    config = UserConfig()
    pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)
    logger.info(f'PVs to monitor: {pv_list}')

    # Initialize the PV monitoring and set up the monitors for each measurement PV from the user config
    pv_monitors = PvMonitors(pv_list)

    # Initialize and set-up the PV import in charge of preparing the PV data, handling logging periods & tasks,
    # running content checks for the user config, and looping through each record every few seconds to check for
    # records scheduled to be updated with a new measurement.
    this.pv_import = PvImport(pv_monitors, config)
    this.pv_import.set_up()

    # Start the monitors and continuously store the PV data received on every update
    pv_monitors.start_monitors()

    # Start the PV import main loop to check each record
    this.pv_import.start()


if __name__ == '__main__':
    main()
