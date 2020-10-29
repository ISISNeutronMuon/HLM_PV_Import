"""
Various utility functions
"""
from constants import PvConfig
from collections import Counter


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


def get_types_list(values):
    """
    Given a list of values, returns a list of their types, one entry per type.
    """
    types = set()
    for value in values:
        types.add(type(value))
    return types


def pv_name_without_prefix_and_domain(name):
    """
    Given a PV name, remove the prefix and domain and return only the PV name.

    Args:
        name(str): the full PV name
    Returns:
        name(str): the PV name without prefix and domain
    """
    name = name.replace(f'{PvConfig.PV_PREFIX}:', '').replace(f'{PvConfig.PV_DOMAIN}:', '')
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
    name = f'{PvConfig.PV_PREFIX}:{PvConfig.PV_DOMAIN}:{name}'
    return name


def list_add_blank_values(list_, size):
    """
    Adds None values to a list until the desired size is reached.

    Args:
        list_ (list): The list.
        size (int): The desired length/size of the list.

    """
    if size < len(list_):
        raise ValueError("Desired size cannot be lower than current size.")
    blank_values = [None] * (size - len(list_))
    list_.extend(blank_values)
    return list_


def get_blank_measurements_dict():
    """
    Returns a blank (None values) measurements dict.
    """
    dict_ = {
        1: None,
        2: None,
        3: None,
        4: None,
        5: None
    }
    return dict_


def meas_values_dict_valid(dict_):
    """
    Checks whether the given measurements values dictionary is valid (5 keys named from 1 to 5).

    Args:
        dict_ (dict): The measurements/mea_values dictionary.

    Returns:
        (boolean): True if valid, else False
    """
    keys = list(dict_.keys())
    expected_keys = [1, 2, 3, 4, 5]
    return Counter(keys) == Counter(expected_keys)


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
