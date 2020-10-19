"""
Various utility functions
"""
from constants import PvConfig


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
