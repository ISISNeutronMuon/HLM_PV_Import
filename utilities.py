"""
Various utility functions
"""
import json
from err_logger import log_pv_config_error
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


def get_pv_config(pv_name, attr_key=None):
    """
    Get the configuration of given PV.

    If no attribute key was specified, get dictionary of all PV config attributes.

    Args:
        pv_name (str): Name of the PV
        attr_key (str, optional): PV configuration attribute key, Defaults to None.

    Returns:
        (string/dict): The PV config attribute value, or a dictionary of all attributes if key was not specified.
    """
    return_val = None
    with open(PvConfig.PATH) as json_file:
        data = json.load(json_file)

        try:
            if attr_key:
                return_val = data[PvConfig.ROOT][f'{pv_name}'][f'{attr_key}']
            else:
                return_val = data[PvConfig.ROOT][f'{pv_name}']
        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PvConfig.NAME, print_err=True)

        return return_val


def get_all_pv_configs():
    """
    Get all PV configurations in a dict.

    Returns:
        (dict): The PV configurations dictionary.
    """
    return_val = None
    with open(PvConfig.PATH) as json_file:
        data = json.load(json_file)

        try:
            return_val = data[PvConfig.ROOT]
        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PvConfig.NAME, print_err=True)

    return return_val


def get_config_pv_names(full_names=False):
    """
    Get a list of all configurations PV names.

    Args:
        full_names (boolean, optional): Get the PV name with domain and prefix, Defaults to False.

    Returns:
        (list): The list of PV names in the configuration file.
    """
    return_val = None
    with open(PvConfig.PATH) as json_file:
        data = json.load(json_file)

        try:
            return_val = data[PvConfig.ROOT]  # get dictionary
            return_val = [*return_val]  # unpack dict into list literal

            if full_names:
                for index, pv_name in enumerate(return_val):
                    return_val[index] = get_full_pv_name(pv_name)

        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PvConfig.NAME, print_err=True)

    return return_val


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
