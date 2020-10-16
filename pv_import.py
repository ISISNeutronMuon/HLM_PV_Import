import copy

from utilities import get_all_pv_configs, pv_name_without_prefix_and_domain
from db_functions import add_measurement, create_pv_import_class_and_function_if_not_exist, \
    create_pv_import_object_and_type_if_not_exist
import time
from datetime import datetime


class PvImport:
    def __init__(self, pv_monitors):
        self.pv_monitors = pv_monitors
        self.tasks = {}
        self.pv_configs = get_all_pv_configs()

    @staticmethod
    def set_up():
        """
        Requirements and checks for importing.
        """
        # Make sure the PV IMPORT object class and function exist
        create_pv_import_class_and_function_if_not_exist()
        create_pv_import_object_and_type_if_not_exist()

    def start(self):
        start_time = time.time()
        while True:
            print(f"({datetime.now().strftime('%H:%M:%S')})", end=' ')
            print(len(self.pv_monitors.get_data()), self.pv_monitors.get_data())

            pvs = copy.deepcopy(self.pv_monitors.get_data())
            for pv_name, pv_value in pvs.items():
                #######################
                pv_short_name = pv_name_without_prefix_and_domain(pv_name)
                try:
                    pv_config = self.pv_configs[pv_short_name]
                except KeyError:
                    # If PV name was not found in the config file, cancel future updates
                    # and remove it from the PV Data dict.
                    self.pv_monitors.remove_pv(pv_name)
                    continue

                object_id = pv_config['record_id']
                mea_values = [pv_value]

                add_measurement(object_id=object_id, mea_values=mea_values, mea_valid=1)
                #######################

            time.sleep(5.0 - ((time.time() - start_time) % 5.0))

    @staticmethod
    def get_tasks_from_config():
        """
        Gets a dictionary of the PV/Logging Period for each entry in the config file.

        Returns:
            (dict): A PV/Logging Period dictionary.
        """
        tasks = {}
        configs = get_all_pv_configs()
        for pv, config in configs.items():
            tasks[f'{pv}'] = config['logging']

        return tasks
