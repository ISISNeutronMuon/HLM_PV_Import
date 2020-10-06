"""
Various utility functions
"""


def single_tuples_to_strings(tuple_list):
    """
    Given a list of tuples, convert all single-element tuples into a string of the first element. Tuples in the list
    with multiple elements will not be affected.

    Args:
        tuple_list (list): the list of bytearray tuples to convert
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


def pv_name_without_domain(name, domain):
    """
    Given a PV name, remove the prefix and domain and return only the PV name.

    Args:
        name(str): the full PV name
        domain(str): the domain name
    Returns:
        name(str): the PV name without prefix and domain
    """
    name = name.split(domain + ':', 1)
    name = name[len(name) - 1]  # get the last element of the list
    return name
