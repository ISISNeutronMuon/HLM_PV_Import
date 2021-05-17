from peewee import DoesNotExist
from functools import wraps
from shared.db_models import *
from shared.const import DBTypeIDs


def _end_with_colon(string):
    return string if string.endswith(':') else f'{string}:'


def get_short_pv_name(pv_name, prefix, domain):
    return pv_name.replace(_end_with_colon(prefix), '').replace(_end_with_colon(domain), '')


def get_full_pv_name(pv_name, prefix, domain):
    """
    Adds the prefix and domain to the PV name.

    Args:
        pv_name (str): The PV name.
        prefix (str): The PV prefix.
        domain (str): The PV domain.
    Returns:
        (str) The full PV name, with its prefix and domain.
    """
    pv_name = get_short_pv_name(pv_name, prefix, domain)
    return f'{_end_with_colon(prefix)}{_end_with_colon(domain)}{pv_name}' if pv_name else None


def need_connection(func):
    """
    Call function only if DB connection is usable.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs) if database.is_connection_usable() else None

    return wrapper


@need_connection
def get_sld_id(object_id: int):
    """
    Get the ID of the object's SLD (Software Level Device) if it has one.

    Args:
        object_id (int): The object ID.

    Returns:
        (int): The SLD object ID.
    """
    try:
        sld_relation = (GamObjectrelation
                        .select(GamObjectrelation.or_object_id_assigned)
                        .join(GamObject, on=GamObjectrelation.or_object_id_assigned == GamObject.ob_id)
                        .where(GamObjectrelation.or_object == object_id, GamObjectrelation.or_date_removal.is_null(),
                               GamObject.ob_objecttype == DBTypeIDs.SLD)
                        .order_by(GamObjectrelation.or_id.desc())
                        .get())
        return sld_relation.or_object_id_assigned.ob_id
    except DoesNotExist:
        return None
