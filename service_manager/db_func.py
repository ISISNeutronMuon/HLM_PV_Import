from peewee import DoesNotExist
from datetime import datetime

from service_manager.utilities import generate_module_name
from shared.const import DBTypeIDs, DBClassIDs
from shared.utils import need_connection
from shared.db_models import *
from service_manager.logger import manager_logger as logger


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
        (GamObject/None): The object with the given ID, None if not found.

    """
    return GamObject.get_or_none(GamObject.ob_id == object_id)


@need_connection
def get_object_id(object_name):
    """
    Get the ID of the object with the given name.

    Returns:
        (int/None): The object ID, None if object with given name not found.
    """
    obj = GamObject.get_or_none(GamObject.ob_name == object_name)
    return obj.ob_id if obj else None


@need_connection
def get_max_object_id():
    """
    Get the ID highest ID.

    Returns:
        (int): The highest object ID in the database or zero if there isn't any present.
    """
    query = GamObject.select(GamObject.ob_id).order_by(GamObject.ob_id)
    if not query:
        return 0
    else:
        return query[-1].ob_id


@need_connection
def get_object_name(object_id):
    """
    Gets the name of the object with the given ID.

    Args:
        object_id (int): The object ID.

    Returns:
        (str/None): The object name, None if object with given ID not found.
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
def get_all_display_names():
    """
    Get a list of all display group names.

    Returns:
        (list): The display group names.
    """
    query = GamDisplaygroup.select(GamDisplaygroup.dg_name)
    return [x.dg_name for x in query if x]


@need_connection
def get_type_id(type_name: str):
    """
    Get the ID of the object type with the given name.

    Args:
        type_name (str): The object type name.

    Returns:
        type_id (int/None): The object type ID, None if not found.
    """
    obj_type = GamObjecttype.get_or_none(GamObjecttype.ot_name == type_name)
    return obj_type.ot_id if obj_type else None


@need_connection
def get_display_group_id(display_group: str):
    """
    Get the ID of the object type with the given name.

    Args:
        display_group (str): The display group name.

    Returns:
        type_id (int/None): The object type ID, None if not found.
    """
    group = GamDisplaygroup.get_or_none(GamDisplaygroup.dg_name == display_group)
    return group.dg_id if group else None


@need_connection
def get_object_type(object_id: int):
    """
    Returns the type name of the object with the specified ID.

    Args:
        object_id (int): The object ID.

    Returns:
        (str/None): The object type name, None if not found.
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
        (str/None): The object class name, None if not found.
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
        (int/None): The object class ID, None if not found.
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
        (str/None): The object function name, None if not found.
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
        (list/None): The measurement types, None if class was not found.
    """
    try:
        obj_class = GamObjectclass.get(GamObjectclass.oc_id == object_class_id)
        return [obj_class.oc_measuretype1, obj_class.oc_measuretype2, obj_class.oc_measuretype3,
                obj_class.oc_measuretype4, obj_class.oc_measuretype5]
    except DoesNotExist:
        return None


@need_connection
def get_object_display_group(object_id: int):
    """
    Get the name of the object's display group if it has one.

    Args:
        object_id (int): The object ID.

    Returns:
        (str/None): The object's display group, None if not found.
    """
    obj = GamObject.get_or_none(GamObject.ob_id == object_id)
    try:
        display_id = obj.ob_displaygroup
        return display_id.dg_name
    except (DoesNotExist, AttributeError):
        return


@need_connection
def create_module_if_required(object_id: int, object_name: str, type_name: str, class_id: int):
    module_id = None
    module_name = generate_module_name(object_name, object_id, class_id)
    if class_id in [DBClassIDs.VESSEL, DBClassIDs.CRYOSTAT]:
        module_id = add_object(name=module_name, type_id=DBTypeIDs.SLD,
                               comment=f'Software Level Device for {type_name} "{object_name}" (ID: {object_id})')
    elif class_id == DBClassIDs.GAS_COUNTER:
        module_id = add_object(name=module_name, type_id=DBTypeIDs.GCM,
                               comment=f'Gas Counter Module for {type_name} "{object_name}" (ID: {object_id})')
    if module_id is not None:
        add_relation(or_object_id=object_id, or_object_id_assigned=module_id)


@need_connection
def add_object(name: str, type_id: int, display_group_id: int = None, comment: str = None):
    """
    Create a new object with the given name, type and comment.

    Args:
        name (str): The name of the object.
        type_id (int): The type ID of the object.
        display_group_id (int): The ID of the display group this object is part of.
        comment (str): Object comment.

    Returns:
        (int): ID of the added object.

    Raises:
        DBObjectNameAlreadyExists: If an object with the given name already exists in the database.
    """
    if get_object_id(object_name=name) is not None:
        raise DBObjectNameAlreadyExists(f'Could not create object - '
                                        f'Object with name "{name}" already exists in the database.')

    record_id = GamObject.insert(ob_name=name, ob_objecttype=type_id, ob_displaygroup=display_group_id,
                                 ob_comment=comment).execute()

    logger.info(f'Created object no. {record_id} ("{name}") of type {type_id}.')

    return record_id


@need_connection
def add_relation(or_object_id: int, or_object_id_assigned: int):
    """
    Creates a relation between two objects. Note: Dates must be in '%Y-%m-%d %H:%M:%S' format.

    Args:
        or_object_id (int): The object ID (the object itself).
        or_object_id_assigned (int): The assigned object ID (e.g. the SLD/ILM Module etc.).
    """
    record_id = GamObjectrelation.insert(
        or_primary=0,
        or_object=or_object_id,
        or_object_id_assigned=or_object_id_assigned,
        or_date_assignment=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        or_date_removal=None,
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
