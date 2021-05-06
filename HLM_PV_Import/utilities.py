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

    return name.replace(CA.PV_PREFIX, '').replace(CA.PV_DOMAIN, '')


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
    
    return f'{CA.PV_PREFIX}{CA.PV_DOMAIN}{name}'
