"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

from hlm_pv_import.ca_wrapper import PvMonitors
from hlm_pv_import.user_config import UserConfig
from hlm_pv_import.pv_import import PvImport
from hlm_pv_import.settings import CA, HEDB
from hlm_pv_import.logger import logger
from hlm_pv_import.db_func import db_connect, check_db_connection
from hlm_pv_import.external_pvs import MercuryPVs
from shared.db_models import initialize_database
import os
import sys

this = sys.modules[__name__]

this.pv_import = None


def main():
    # Setup the channel access address list in order to connect to PVs
    os.environ['EPICS_CA_ADDR_LIST'] = CA.EPICS_CA_ADDR_LIST

    # External PVs
    external_pvs_configs = [MercuryPVs()]
    external_pvs_list = [y for x in external_pvs_configs for y in x.get_full_pv_list()]

    # Initialize and establish the database connection
    initialize_database(name=HEDB.NAME, user=HEDB.USER, password=HEDB.PASS, host=HEDB.HOST)
    db_connect()
    check_db_connection()

    # Get the user configuration and the list of measurement PVs
    config = UserConfig()
    pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)
    logger.info(f'He Recovery PLC PVs to monitor: {pv_list}')

    # Add external PVs to monitoring list
    logger.info(f'Non-PLC PVs to monitor: {external_pvs_list}')
    pv_list.extend(external_pvs_list)

    # Set up monitoring and fetching of the PV data
    pv_monitors = PvMonitors(pv_list)

    # Initialize and set-up the PV import in charge of preparing the PV data, handling logging periods & tasks,
    # running content checks for the user config, and looping through each record every few seconds to check for
    # records scheduled to be updated with a new measurement.
    this.pv_import = PvImport(pv_monitors, config, external_pvs_configs)

    # Start the monitors and continuously store the PV data received on every update
    pv_monitors.start_monitors()

    # Start the PV Import main loop
    this.pv_import.start()


if __name__ == '__main__':
    main()
