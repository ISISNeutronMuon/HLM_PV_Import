from peewee import DoesNotExist
from functools import wraps
from shared.db_models import *
from shared.const import DBTypeIDs, DBClassIDs


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
def get_object_module(object_id: int, object_class: int = None):
    if object_class is None:
        obj = GamObject.get_or_none(GamObject.ob_id == object_id)
        if obj is None:
            return None
        object_class = obj.ob_objecttype.ot_objectclass.oc_name
    if object_class in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT]:
        return _get_module_object(object_id, DBTypeIDs.SLD)
    elif object_class == DBClassIDs.GAS_COUNTER:
        return _get_module_object(object_id, DBTypeIDs.GCM)
    else:
        return None


@need_connection
def _get_module_object(object_id: int, module_type: int):
    """
    Get the module with the given type of the object with the given ID.

    Args:
        object_id (int): The object ID whose relations to check.
        module_type (int): The type of the module to find in relations.

    Returns:
        (GamObject): The module object.
    """
    try:
        gcm_relation = (GamObjectrelation
                        .select(GamObjectrelation.or_object_id_assigned)
                        .join(GamObject, on=GamObjectrelation.or_object_id_assigned == GamObject.ob_id)
                        .where(GamObjectrelation.or_object == object_id, GamObjectrelation.or_date_removal.is_null(),
                               GamObject.ob_objecttype == module_type)
                        .order_by(GamObjectrelation.or_id.desc())
                        .get())
        return gcm_relation.or_object_id_assigned
    except DoesNotExist:
        return None
