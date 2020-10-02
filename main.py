"""
Helium Level Monitoring Project - HeRecovery Database PV Import

Environment variables to set: EPICS_CA_ADDR_LIST, DB_IOC_USER, DB_IOC_PASS
"""

import caproto
from caproto.sync.client import read as ca_read

import ca_wrapper
import pv_functions
import utilities


PV_PREFIX = 'TE:NDW2123'
PV_DOMAIN = 'HA:HLM'

pv_name = f'{PV_PREFIX}:{PV_DOMAIN}:MCP1:BANK4:DLS_HE_STORAGE'


if __name__ == '__main__':

    print(ca_wrapper.get_pv_value(pv_name))
    print(pv_functions.get_pv_names())
    print(pv_functions.get_pv_values())
    print(pv_functions.get_pv_names_and_values())
