from peewee import DoesNotExist
from datetime import datetime

from shared.const import DBTypeIDs, DBClassIDs
from shared.utils import get_sld_id, need_connection
from shared.db_models import *
from ServiceManager.logger import manager_logger as logger


def db_connect():
    try:
        database.connect(reuse_if_open=True)
        logger.info('Database connection successful.')
    except Exception as e:
        raise DBConnectionError(f'Could not establish database connection: {e}')


def db_connected():
    return database.is_connection_usable()


@need_connection
def get_object(object_id):
    """
    Gets the record of the object with the given ID.

    Returns:
        (GamObject): The object with the given ID.

    """
    return GamObject.get_or_none(GamObject.ob_id == object_id)


@need_connection
def get_object_id(object_name):
    """
    Get the ID of the object with the given name.

    Returns:
        (int): The object ID.
    """
    obj = GamObject.get_or_none(GamObject.ob_name == object_name)
    return obj.ob_id if obj else None


@need_connection
def get_object_name(object_id):
    """
    Gets the name of the object with the given ID.

    Args:
        object_id (int): The object ID.

    Returns:
        (str): The object name.
    """
    obj = GamObject.get_or_none(GamObject.ob_id == object_id)
    return obj.ob_name if obj else None


@need_connection
def get_all_object_names():
    """
    Get a list of all object names.

    Returns:
        (list): The object names.
    """
    query = GamObject.select(GamObject.ob_name)
    return [x.ob_name for x in query if x]


@need_connection
def get_all_type_names():
    """
    Get a list of all object type names.

    Returns:
        (list): The object type names.
    """
    query = GamObjecttype.select(GamObjecttype.ot_name)
    return [x.ot_name for x in query if x]


@need_connection
def get_type_id(type_name: str):
    """
    Get the ID of the object type with the given name.

    Args:
        type_name (str): The object type name.

    Returns:
        type_id (int): The object type ID.
    """
    obj_type = GamObjecttype.get_or_none(GamObjecttype.ot_name == type_name)
    return obj_type.ot_id if obj_type else None


@need_connection
def get_object_type(object_id: int):
    """
    Returns the type name of the object with the specified ID.

    Args:
        object_id (int): The object ID.

    Returns:
        (str): The object type name.
    """
    obj = GamObject.get_or_none(GamObject.ob_id == object_id)
    return obj.ob_objecttype.ot_name if obj else None


@need_connection
def get_object_class(object_id: int):
    """
    Returns the class name of the object with the specified ID.

    Args:
        object_id (int): The object ID.

    Returns:
        (str): The object class name.
    """
    obj = GamObject.get_or_none(GamObject.ob_id == object_id)
    return obj.ob_objecttype.ot_objectclass.oc_name if obj else None


@need_connection
def get_class_id(type_id: int):
    """
    Returns the object class ID of the object type with the specified ID.

    Args:
        type_id (int): The object type ID.

    Returns:
        (int): The object class ID.
    """
    obj_type = GamObjecttype.get_or_none(GamObjecttype.ot_id == type_id)
    return obj_type.ot_objectclass.oc_id if obj_type else None


@need_connection
def get_object_function(object_id: int):
    """
    Returns the object function name of the object with the specified ID.

    Args:
        object_id (int): The DB ID of the object.

    Returns:
        (str): The object function name.
    """
    obj = GamObject.get_or_none(GamObject.ob_id == object_id)
    return obj.ob_objecttype.ot_objectclass.oc_function.of_name if obj else None


@need_connection
def get_measurement_types(object_class_id: int):
    """
    Returns the measurement types of the class with the specified ID.

    Args:
        object_class_id (int): The class ID.

    Returns:
        (dict): The measurement types as a dict (Mea. No. / Type).
    """
    try:
        obj_class = GamObjectclass.get(GamObjectclass.oc_id == object_class_id)
        mea_types = [obj_class.oc_measuretype1, obj_class.oc_measuretype2, obj_class.oc_measuretype3,
                     obj_class.oc_measuretype4, obj_class.oc_measuretype5]

        return {i + 1: x for i, x in enumerate(mea_types)}
    except DoesNotExist:
        return None


@need_connection
def get_object_sld(object_id: int):
    """
    Get the name of the object's SLD (Software Level Device) if it has one.

    Args:
        object_id (int): The object ID.

    Returns:
        (str): The object's SLD namem.
    """
    sld_id = get_sld_id(object_id)
    sld = GamObject.get_or_none(GamObject.ob_id == sld_id)
    return sld.ob_name if sld else None


@need_connection
def create_sld_if_required(object_id: int, object_name: str, type_name: str, class_id: int):
    if class_id in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT, DBClassIDs.GAS_COUNTER]:
        sld_id = add_object(name=f'SLD "{object_name}" (ID: {object_id})', type_id=DBTypeIDs.SLD,
                            comment=f'Software Level Device for {type_name} "{object_name}" (ID: {object_id})')
        add_relation(or_object_id=object_id, or_object_id_assigned=sld_id)


@need_connection
def add_object(name: str, type_id: int, comment: str = None):
    """
    Create a new object with the given name, type and comment.

    Args:
        name (str): The name of the object.
        type_id (int): The type ID of the object.
        comment (str): Object comment.

    Returns:
        (int): ID of the added object.

    Raises:
        DBObjectNameAlreadyExists: If an object with the given name already exists in the database.
    """
    if get_object_id(object_name=name) is not None:
        raise DBObjectNameAlreadyExists(f'Could not create object - '
                                        f'Object with name "{name}" already exists in the database.')

    record_id = GamObject.insert(ob_name=name, ob_objecttype=type_id, ob_comment=comment).execute()

    logger.info(f'Created object no. {record_id} ("{name}") of type {type_id}.')

    return record_id


@need_connection
def add_relation(or_object_id: int, or_object_id_assigned: int,
                 start_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), removal_date=None):
    """
    Creates a relation between two objects. Note: Dates must be in '%Y-%m-%d %H:%M:%S' format.

    Args:
        or_object_id (int): The object ID (the object itself).
        or_object_id_assigned (int): The assigned object ID (e.g. the SLD/ILM Module etc.).
        start_date (str, optional): The starting date of the relation, Defaults to current time.
        removal_date (str, optional): The removal date of the relation, Defaults to None.
    """
    record_id = GamObjectrelation.insert(
        or_primary=0,
        or_object=or_object_id,
        or_object_id_assigned=or_object_id_assigned,
        or_date_assignment=start_date,
        or_date_removal=removal_date,
        or_outflow=None,
        or_bookingrequest=None
    ).execute()

    logger.info(f'Added relation {record_id} for objects {or_object_id} - {or_object_id_assigned}.')


class DBObjectNameAlreadyExists(Exception):
    def __init__(self, err_msg):
        logger.error(err_msg)
        super(DBObjectNameAlreadyExists, self).__init__(err_msg)


class DBConnectionError(Exception):
    def __init__(self, err_msg):
        logger.error(err_msg)
        super(DBConnectionError, self).__init__(err_msg)
