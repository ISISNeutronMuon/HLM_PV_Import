"""
Various utility functions
"""
from HLM_PV_Import.settings import CA


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
