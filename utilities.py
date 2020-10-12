"""
Various utility functions
"""
import os
import json
import sys
from ca_logger import log_pv_config_error

PV_CONFIG = 'pv_config.json'
PV_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), PV_CONFIG)
PV_CONFIG_DICT = 'pvs'

PV_PREFIX = 'TE:NDW2123'
PV_DOMAIN = 'HA:HLM'


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
    with open(PV_CONFIG_PATH) as json_file:
        data = json.load(json_file)

        try:
            if attr_key:
                return_val = data[PV_CONFIG_DICT][f'{pv_name}'][f'{attr_key}']
            else:
                return_val = data[PV_CONFIG_DICT][f'{pv_name}']
        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PV_CONFIG, print_err=True)

        return return_val


def get_all_pv_configs():
    """
    Get all PV configurations in a dict.

    Returns:
        (dict): The PV configurations dictionary.
    """
    return_val = None
    with open(PV_CONFIG_PATH) as json_file:
        data = json.load(json_file)

        try:
            return_val = data[PV_CONFIG_DICT]
        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PV_CONFIG, print_err=True)

    return return_val


def get_config_pv_names():
    """
    Get a list of all configurations PV names.

    Returns:
        (list): The list of PV names in the configuration file.
    """
    return_val = None
    with open(PV_CONFIG_PATH) as json_file:
        data = json.load(json_file)

        try:
            return_val = data[PV_CONFIG_DICT]  # get dictionary
            return_val = [*return_val]  # unpack dict into list literal
        except KeyError as e:
            log_pv_config_error(pv_name=f'{e}', config_file=PV_CONFIG, print_err=True)

    return return_val


def get_full_pv_name(name):
    """
    Adds the prefix and domain to the PV if it doesn't have them.

    Args:
        name (str): The PV name.

    Returns:
        (str) The full PV name.
    """
    name = name.replace(f'{PV_PREFIX}:', '')
    name = name.replace(f'{PV_DOMAIN}:', '')
    name = f'{PV_PREFIX}:{PV_DOMAIN}:{name}'
    return name
