"""
Various utility functions
"""


def single_elem_tuples_to_strings(tuple_list):
    """
    Given a list of bytearray tuples, convert it into a list of strings of the first tuple element.

    args:
        tuples (list): the list of bytearray tuples to convert
    returns:
        (list) the list of strings made from the first element of the tuples
    """
    string_list = []
    for elem in tuple_list:
        string_list.append(elem[0])
    return string_list


def get_types_list(values):
    """
    Given a list of values, returns a list of their types, one entry per type.
    """
    types = set()
    for value in values:
        types.add(type(value))
    return types
