"""
Various utility functions
"""
from HLM_PV_Import.settings import CA


def single_tuples_to_strings(tuple_list):
    """
    Given a list of tuples, convert all single-element tuples into a string of the first element. Tuples in the list
    with multiple elements will not be affected.

    Args:
        tuple_list (list): the list of tuples to convert
    Returns:
        (list) the list of strings made from the first element of the tuples

    """

    string_list = []
    for elem in tuple_list:
        if len(elem) == 1:
            string_list.append(elem[0])
        else:
            string_list.append(elem)
    return string_list


def pv_name_without_prefix_and_domain(name):
    """
    Given a PV name, remove the prefix and domain and return only the PV name.

    Args:
        name(str): the full PV name
    Returns:
        name(str): the PV name without prefix and domain
    """
    name = name.replace(f'{CA.PV_PREFIX}:', '').replace(f'{CA.PV_DOMAIN}:', '')
    return name


def get_full_pv_name(name):
    """
    Adds the prefix and domain to the PV if it doesn't have them.

    Args:
        name (str): The PV name.

    Returns:
        (str) The full PV name.
    """
    if not name:
        return None
    name = pv_name_without_prefix_and_domain(name)
    pv_prefix = CA.PV_PREFIX
    pv_domain = CA.PV_DOMAIN
    if pv_prefix:
        pv_prefix = f'{pv_prefix}:'
    if pv_domain:
        pv_domain = f'{pv_domain}:'
    name = f'{pv_prefix}{pv_domain}{name}'
    return name


def remove_raw_and_sim_pvs(pv_names):
    """
    Removes _RAW and SIM PVs from a PV name list.

    Args:
        pv_names (list): The list of PV names.

    Returns:
        new_names (list): The list without _RAW and SIM PV names.
    """
    new_names = []
    for name in pv_names:
        is_raw = True if name.split(':')[-1] == '_RAW' else False
        is_sim = True if pv_name_without_prefix_and_domain(name).split(':')[0] == 'SIM' else False
        if not is_raw and not is_sim:
            new_names.append(name)

    return new_names
