"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from HLM_PV_Import.ca_wrapper import PvMonitors
from HLM_PV_Import.user_config import UserConfig
from HLM_PV_Import.pv_import import PvImport
from HLM_PV_Import.settings import CA, HEDB
from HLM_PV_Import.logger import logger
from shared.db_models import initialize_database
from HLM_PV_Import.db_func import db_connect, check_db_connection
import os
import sys

this = sys.modules[__name__]

this.pv_import = None


def main():
    # Setup the channel access address list in order to connect to PVs
    os.environ['EPICS_CA_ADDR_LIST'] = CA.EPICS_CA_ADDR_LIST

    # Initialize and establish the database connection
    initialize_database(name=HEDB.NAME, user=HEDB.USER, password=HEDB.PASS, host=HEDB.HOST)
    db_connect()
    check_db_connection()

    # Get the user configuration and the list of measurement PVs
    config = UserConfig()
    pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)
    logger.info(f'PVs to monitor: {pv_list}')

    # Initialize the PV monitoring and set up the monitors for each measurement PV from the user config
    pv_monitors = PvMonitors(pv_list)

    # Initialize and set-up the PV import in charge of preparing the PV data, handling logging periods & tasks,
    # running content checks for the user config, and looping through each record every few seconds to check for
    # records scheduled to be updated with a new measurement.
    pv_import = PvImport(pv_monitors, config)

    # Start the monitors and continuously store the PV data received on every update
    pv_monitors.start_monitors()

    # Start the PV Import main loop
    pv_import.start()


if __name__ == '__main__':
    main()
