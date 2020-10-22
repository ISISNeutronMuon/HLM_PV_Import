import copy

from ca_wrapper import PvMonitors
from user_config import UserConfig
from utilities import pv_name_without_prefix_and_domain, get_blank_measurements_dict
from db_functions import add_measurement, create_pv_import_class_and_function_if_not_exist, \
    create_pv_import_object_and_type_if_not_exist
import time
from datetime import datetime


class PvImport:
    def __init__(self, pv_monitors: PvMonitors, config: UserConfig):
        self.pv_monitors = pv_monitors
        self.tasks = {}
        self.config = config

    def set_up(self):
        """
        Requirements and checks before importing PV data.
        """
        # Check if the user configuration is valid
        self.config.run_checks()

        # Make sure the PV IMPORT object class and function exist
        create_pv_import_class_and_function_if_not_exist()
        create_pv_import_object_and_type_if_not_exist()

    def start(self):
        """
        Starts the PV data importing loop.
        """
        start_time = time.time()
        while True:
            pv_data = copy.deepcopy(self.pv_monitors.get_data())
            print(f"({datetime.now().strftime('%H:%M:%S')})", end=' ')
            print(len(pv_data), pv_data)

            for record in self.config.records:
                measurement_pvs = self.config.get_record_measurement_pvs(record, full_names=True)
                mea_values = get_blank_measurements_dict()

                for index, pv_name in enumerate(measurement_pvs):
                    try:
                        pv_value = pv_data[pv_name]
                    except KeyError:
                        continue
                    mea_values[index + 1] = pv_value

                # If all measurement values are None/empty, skip to the next record.
                if all(value is None for value in mea_values.values()):
                    continue

                print(mea_values)

            # for pv_name, pv_value in pv_names_and_values.items():
            #     pv_short_name = pv_name_without_prefix_and_domain(pv_name)
            #     print(self.config.get_pv_config(pv_short_name))
            # try:
            #     pv_config = self.pv_configs[pv_short_name]
            # except KeyError:
            #     # If PV name was not found in the config file, cancel future updates
            #     # and remove it from the PV Data dict.
            #     self.pv_monitors.remove_pv(pv_name)
            #     continue
            #
            # object_id = pv_config['record_id']
            # mea_values = [pv_value]

            # add_measurement(object_id=object_id, mea_values=mea_values, mea_valid=1)

            time.sleep(5.0 - ((time.time() - start_time) % 5.0))
