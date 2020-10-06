"""
Helium Level Monitoring Project - HeRecovery Database PV Import
"""

import ca_wrapper
import pv_functions


PV_PREFIX = 'TE:NDW2123'
PV_DOMAIN = 'HA:HLM'

pv_name = f'{PV_PREFIX}:{PV_DOMAIN}:MCP1:BANK4:DLS_HE_STORAGE'
pvtwo = f'{PV_PREFIX}:{PV_DOMAIN}:GC:ZOOM_SANS2D_AND_POLREF.DESC'

if __name__ == '__main__':
    print(ca_wrapper.get_pv_value(pvtwo))
    # print(utilities.pv_name_without_domain(pv_name, pv_functions.PV_DOMAIN))
    # print(pv_functions.get_pv_names(short_names=True))
    # print(pv_functions.get_pv_names_and_values(short_names=True))
    print(pv_functions.get_pv_objects())
    asd = pv_functions.get_pv_objects()
    for pv in asd:
        print(pv.name + ' ' + pv.desc)
