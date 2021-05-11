from peewee import DoesNotExist
from functools import wraps
from shared.db_models import *
from shared.const import DBTypeIDs


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