import copy

from ca_wrapper import PvMonitors
from user_config import UserConfig
from utilities import get_blank_measurements_dict
from db_functions import add_measurement, setup_db_pv_import
import time
from datetime import datetime

LOOP_TIMER = 5.0    # The timer between each PV import loop


class PvImport:
    def __init__(self, pv_monitors: PvMonitors, user_config: UserConfig):
        self.pv_monitors = pv_monitors
        self.config = user_config
        self.tasks = {}

    def set_up(self):
        """
        Requirements and checks before importing PV data.
        """
        # Check if the user configuration is valid
        self.config.run_checks()

        # Create the PV IMPORT object within the database if it doesn't already exist
        setup_db_pv_import()

        # Initialize tasks
        for record in self.config.records:
            self.tasks[record] = 0

    def start(self):
        """
        Starts the PV data importing loop.
        """
        start_time = time.time()
        while True:
            time.sleep(LOOP_TIMER - ((time.time() - start_time) % LOOP_TIMER))

            pv_data = copy.deepcopy(self.pv_monitors.get_data())
            print(f"({datetime.now().strftime('%H:%M:%S')})", end=' ')
            print(len(pv_data), pv_data)

            for record in self.config.records:

                # Check record next logging time  in tasks, if not yet then go to next record
                if self.tasks[record] > time.time():
                    continue
                # If record is ready to be updated, set curr time + log period in minutes as next run, then proceed
                self.tasks[record] = time.time() + (60 * self.config.logging_periods[record])

                # Get the entry record's PVs, the initialize the blank measurement values dict (with None values)
                record_pvs = self.config.get_record_measurement_pvs(record, full_names=True)
                mea_values = get_blank_measurements_dict()

                # Iterate through the list of PVs, get the values from the PV monitor data dict, and add them to the
                # measurement values.
                for index, pv_name in enumerate(record_pvs):
                    # If the measurement doesn't have an assigned PV, go to the next one.
                    if not pv_name:
                        continue

                    # If the PV data is stale, then ignore it
                    if self.pv_monitors.pv_data_is_stale(pv_name, print_warning=True):
                        continue

                    # Add the PV value to the measurements. If the PV does not exist in the PV monitors data dict,
                    # then skip it. This could happen because of a monitor not receiving updates from the existing PV.
                    try:
                        pv_value = pv_data[pv_name]
                        mea_values[index + 1] = pv_value
                    except KeyError:
                        continue
                print(mea_values)

                # If none of the measurement PVs values were found in the PV monitors data dict,
                # skip to the next record.
                if all(value is None for value in mea_values.values()):
                    continue

                # Add a measurement with the values for the record/object
                add_measurement(record_name=record, mea_values=mea_values, mea_valid=True)
