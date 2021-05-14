import sys
import time
from datetime import datetime
from functools import wraps

from shared.db_models import *
from shared.utils import get_sld_id
from HLM_PV_Import.logger import logger, db_logger, log_exception

RECONNECT_ATTEMPTS_MAX = 1000
RECONNECT_WAIT = 5  # base wait time between attempts in seconds
RECONNECT_MAX_WAIT_TIME = 14400  # maximum wait time between attempts, in sec


def increase_reconnect_wait_time(current_wait):  # increasing wait time in s between attempts for each failed attempt
    return current_wait*2 if current_wait*2 < RECONNECT_MAX_WAIT_TIME else RECONNECT_MAX_WAIT_TIME


def db_connect():
    try:
        database.connect(reuse_if_open=True)
        logger.info('Database connection successful.')
    except Exception as e:
        logger.error(e)
        log_exception(*sys.exc_info())


def check_db_connection(attempt: int = 1, wait_until_reconnect: int = RECONNECT_WAIT):
    """
    Check if DB is connected, and if not re-attempt to establish a connection.
    With each attempt, the interval between attempts will increase.
    """
    if database.is_connection_usable():
        return True
    elif attempt > RECONNECT_ATTEMPTS_MAX:
        conn_aborted = 'Connection to the database was lost and could not be re-established.'
        logger.error(conn_aborted)
        raise Exception(conn_aborted)
    else:
        logger.error(f'Connection to the database could not be established, re-attempting to connect in '
                     f'{wait_until_reconnect}s. (Attempt: {attempt})')
        time.sleep(wait_until_reconnect)
        time_until_next_reconnect = increase_reconnect_wait_time(current_wait=wait_until_reconnect)
        db_connect()
        check_db_connection(attempt=attempt + 1, wait_until_reconnect=time_until_next_reconnect)


def check_connection(func):
    """
    Decorator to check that the DB is connected before function is called.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        check_db_connection()
        return func(*args, **kwargs)

    return wrapper


@check_connection
def get_object(object_id):
    """
    Gets the record of the object with the given ID.

    Returns:
        (GamObject): The object with the given ID.

    """
    return GamObject.get_or_none(GamObject.ob_id == object_id)


@check_connection
def add_measurement(object_id, mea_values: dict):
    """
    Adds a measurement to the database. If the object currently has a Software Level Device, the measurement object will
    be the SLD. Otherwise, the measurement will be added to the object itself.

    Args:
        object_id (int): Record/Object id of the object the measurement is for.
        mea_values (dict): A dict of the measurement values, max 5, in measurement_number(str)/pv_value pairs.
        mea_valid (boolean, optional): Whether the measurement is valid, Defaults to True.
    """
    obj = GamObject.get(GamObject.ob_id == object_id)
    type_name = obj.ob_objecttype.ot_name
    class_name = obj.ob_objecttype.ot_objectclass.oc_name

    # Check if object has a Software Level Device
    sld_id = get_sld_id(object_id=obj.ob_id)
    if sld_id is not None:
        mea_comment = f'SLD for {object_id} "{obj.ob_name}" ({type_name} - {class_name}) via HLM PV IMPORT'
        object_id = sld_id  # Add measurements to the SLD instead of directly to the object
    else:
        mea_comment = f'"{obj.ob_name}" ({type_name} - {class_name}) via HLM PV IMPORT'

    mea_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    record_id = GamMeasurement.insert(
        mea_object=object_id,
        mea_date=mea_date,
        mea_date2=mea_date,
        mea_comment=mea_comment,
        mea_value1=mea_values['1'],
        mea_value2=mea_values['2'],
        mea_value3=mea_values['3'],
        mea_value4=mea_values['4'],
        mea_value5=mea_values['5'],
        mea_valid=1,
        mea_bookingcode=0  # 0 = measurement is not from the balance program (HZB)
    ).execute()

    logger.info(f'Added measurement {record_id} for {obj.ob_name} ({object_id}) with values: {dict(mea_values)}')
    # noinspection PyProtectedMember
    db_logger.info(f"Added record no. {record_id} to {GamMeasurement._meta.table_name}")
