"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

import ca_wrapper
import pv_functions
import utilities
import db_functions
import pv_import
import time


PV_PREFIX = 'TE:NDW2123'
PV_DOMAIN = 'HA:HLM'

pv_name = f'{PV_PREFIX}:{PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

if __name__ == '__main__':
    # print(pv_functions.get_pv_names(short_names=True))
    # print(utilities.get_pv_config('MOTHER_DEWAR:HE_LEVEL'))
    # print(utilities.get_all_pv_configs())
    # print(utilities.get_config_pv_names())
    # print(utilities.get_config_pv_names(full_names=True))
    # db_functions.add_measurement('MOTHER_DEWAR:HE_LEVEL')
    # print(pv_import.get_tasks_from_config())
    # print(pv_functions.get_pv_names_and_values(short_names=True))

    pv_list = pv_functions.get_pv_names()
    # pv_list = utilities.get_config_pv_names(full_names=True)

    pvs = ca_wrapper.PvMonitoring(pv_list)
    pvs.start_monitors()

    start_time = time.time()
    while True:
        print('tick')
        print(len(pvs.get_data()), pvs.get_data())
        time.sleep(5.0 - ((time.time() - start_time) % 5.0))
