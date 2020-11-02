from HLM_PV_Import.db_functions import get_pv_records
from HLM_PV_Import.ca_wrapper import get_pv_value
from HLM_PV_Import import utilities


def get_pv_names(short_names=False):
    """
    Gets the list of names for the PVs currently in the IOC.

    Args:
        short_names (boolean, optional): Display PV names without prefix and domain, Defaults to False.
    Returns:
        The list of PV names.
    """
    records = get_pv_records('pvname')

    if short_names:
        for index, name in enumerate(records):
            records[index] = utilities.pv_name_without_prefix_and_domain(name)

    return records


def get_pv_values():
    """
    Gets the list of values for the PVs currently in the IOC.

    Returns:
        The list of PV values.
    """
    values = []
    records = get_pv_records('pvname')

    for pv in records:
        val = get_pv_value(pv)
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
    records = get_pv_records('pvname')

    for name in records:
        value = get_pv_value(name)

        if short_names:
            pv_dict[utilities.pv_name_without_prefix_and_domain(name)] = value
        else:
            pv_dict[name] = value

    return pv_dict
