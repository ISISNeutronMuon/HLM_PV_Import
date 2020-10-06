import db_functions
import ca_wrapper as ca_wrapper
import utilities
from object_classes import PVRecord

PV_PREFIX = 'TE:NDW2123'
PV_DOMAIN = 'HA:HLM'


def get_pv_names(short_names=False):
    """
    Gets the list of names for the PVs currently in the IOC.

    Args:
        short_names (boolean, optional): Display PV names without prefix and domain, Defaults to False.
    Returns:
        The list of PV names.
    """
    records = db_functions.get_pv_records('pvname')

    if short_names:
        for index, name in enumerate(records):
            records[index] = utilities.pv_name_without_domain(name, PV_DOMAIN)

    return records


def get_pv_values():
    """
    Gets the list of values for the PVs currently in the IOC.

    Returns:
        The list of PV values.
    """
    values = []
    records = db_functions.get_pv_records('pvname')

    for pv in records:
        val = ca_wrapper.get_pv_value(pv)
        values.append(val)
    return values


def get_pv_names_and_values(short_names=False):
    """
    Gets the dictionary of names:values for the PVs currently in the IOC.

    Args:
        short_names (boolean, optional): Display PV names without prefix and domain, Defaults to False.
    Returns:
        The dict of PV names and values.
    """
    pv_dict = {}
    records = db_functions.get_pv_records('pvname')

    for name in records:
        value = ca_wrapper.get_pv_value(name)

        if short_names:
            pv_dict[utilities.pv_name_without_domain(name, PV_DOMAIN)] = value
        else:
            pv_dict[name] = value

    return pv_dict


def get_pv_objects():
    """
    Gets a list of :class:`PVRecord` objects containing the value and record data for each PV currently in the IOC.

    Returns:
        The list of PV objects.
    """
    obj_list = []
    records = db_functions.get_pv_records()

    for pv in records:
        # 0: pvname, 1: record_type, 2: record_desc, 3: iocname
        obj = PVRecord(
            pv[0],                                             # pvname
            ca_wrapper.get_pv_value(pv[0]),                    # value
            pv[1],                                             # record_type
            pv[2],                                             # record_desc
            pv[3]                                              # iocname
        )
        obj_list.append(obj)

    return obj_list
