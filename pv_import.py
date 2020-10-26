import copy

from ca_wrapper import PvMonitors
from user_config import UserConfig
from utilities import pv_name_without_prefix_and_domain, get_blank_measurements_dict
from db_functions import add_measurement, create_pv_import_class_and_function_if_not_exist, \
    create_pv_import_object_and_type_if_not_exist, get_object_id
import time
from datetime import datetime

# The timer between each PV import loop
LOOP_TIMER = 5.0


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

        # Make sure the PV IMPORT object class and function exist
        create_pv_import_class_and_function_if_not_exist()
        create_pv_import_object_and_type_if_not_exist()

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
                    # If measurement number 'index + 1' doesn't have an assigned PV, skip it.
                    if not pv_name:
                        continue
                    # Add the PV value to the measurements. If the PV does not exist in the PV monitors data dict,
                    # then skip it.
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
                add_measurement(record_name=record, mea_values=mea_values, mea_valid=1)
