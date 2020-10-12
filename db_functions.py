"""
Contains functions for working with the IOC and HeRecovery database.
Environment variables: DB_IOC_USER, DB_IOC_PASS, DB_HE_USER, DB_HE_PASS
"""
import os
import mysql.connector
from object_classes import *
import utilities
from datetime import datetime
from ca_wrapper import get_pv_value
from ca_logger import log_db_error

# the IOC DB containing the list of PVs
IOC_HOST = "localhost"
IOC_DB = "iocdb"
IOC_USER = os.environ.get('DB_IOC_USER')
IOC_PASS = os.environ.get('DB_IOC_PASS')

# the HLM GAM DB
HE_HOST = "localhost"
HE_DB = "helium"
HE_USER = os.environ.get('DB_HE_USER')
HE_PASS = os.environ.get('DB_HE_PASS')

HLM_PV_IMPORT = 'HLM PV IMPORT'


def get_pv_records(*args):
    """
    Get the list of PVs containing the Helium Recovery PLC data.

    args:
        *args (str): The columns to get from the table row.

    returns:
        The list of PV records.

    notes:
        Columns/PV Attributes: ['pvname', 'record_type', 'record_desc', 'iocname'].

        If arguments are not provided, all columns (PV attributes) will be selected.

        Invalid arguments (not a valid column) will be ignored.
    """
    valid_columns = ['pvname', 'record_type', 'record_desc', 'iocname']
    columns = []
    for arg in args:
        if arg in valid_columns and arg not in columns:
            columns.append(arg)
    columns = ','.join(columns)

    if not columns:  # if columns is empty
        columns = '*'

    filters = "WHERE pvname LIKE '%HLM%'"
    records = _select_query(table='pvs', columns=columns, filters=filters, db=IOC_DB)

    return records


def add_vessel(vessel: EpicsVessel):
    """
    Create a new vessel record of given vessel type.

    Args:
        vessel (EpicsVessel): The vessel object

    """

    vessel_dict = {
        'OB_OBJECTTYPE_ID': vessel.type_id,
        'OB_NAME': vessel.name,
        'OB_COMMENT': vessel.comment,
        'OB_POSINFORMATION': vessel.pos_info,
        'OB_ACTIVE': vessel.active,
        'OB_MINVALUE': vessel.min_val,
        'OB_MAXVALUE': vessel.max_val,
        'OB_CRITVALUE': vessel.crit_val,
        'OB_TARE': vessel.tare,
        'OB_SPAN1': vessel.span,
        'OB_ZERO1': vessel.zero,
        'OB_ENABLED2': vessel.params_valid,
        'OB_ENABLED3': vessel.display_reversed,
        'OB_SHORTINTERVAL': vessel.interval_short,
        'OB_LONGINTERVAL': vessel.interval_long,
        'OB_QUENCHTIME': vessel.quench_time,
        'OB_QUENCHCURRENT': vessel.quench_current,
        'OB_WAITTIME': vessel.wait_time,
        'OB_MEASCURRENT': vessel.measurement_current,
        'OB_ADCLOOP': vessel.adc_loop,
        'OB_FILLTIMEOUT': vessel.fill_timeout,
        'OB_INSTALLED': vessel.installed_date,
        'OB_SERNO': vessel.serial_no
    }

    table = 'gam_object'

    _insert_query(table, values=vessel_dict)


def add_measurement(pv_name, mea_valid=1):
    """
    Adds a measurement to the database.

    Args:
        pv_name (str): Name of the PV to insert the data from.
        mea_valid (int, optional): If the measurement is valid, Defaults to 1 (true).
    """
    pv_config = utilities.get_pv_config(pv_name)
    object_id = pv_config['record_id']
    object_name = _select_query(
        table='gam_object',
        columns='OB_NAME',
        filters=f'WHERE OB_ID LIKE {object_id}'
    )

    mea_obj_type = _get_object_type(object_id)
    mea_obj_class = _get_object_class(object_id)
    mea_comment = f'{mea_obj_type} ({mea_obj_class} "{object_name} via {HLM_PV_IMPORT}")'

    full_pv_name = utilities.get_full_pv_name(pv_name)
    pv_value, mea_date = get_pv_value(full_pv_name), datetime.now()

    measurement_dict = {
        'MEA_OBJECT_ID': object_id,
        'MEA_DATE': mea_date,
        'MEA_DATE2': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        # 'MEA_STATUS': ,
        'MEA_COMMENT': mea_comment,
        'MEA_VALUE1': pv_value,
        # 'MEA_VALUE2': ,
        # 'MEA_VALUE3': ,
        # 'MEA_VALUE4': ,
        # 'MEA_VALUE5': ,
        'MEA_VALID': mea_valid,
        'MEA_BOOKINGCODE': 0,  # 0 = measurement is not from the balance program
    }
    table = 'gam_measurement'
    print(measurement_dict)
    return 0
    _insert_query(table, values=measurement_dict)


def _get_object_type(object_id, name_only=False):
    """
    Returns the type DB record of the given object.

    Args:
        object_id (int): The DB ID of the object.
        name_only (boolean, optional): Get only the type name, Defaults to False.

    Returns:
        (str/dict): The type name/record of the object.
    """

    type_id = _select_query(table='gam_object',
                            columns='OB_OBJECTTYPE_ID',
                            filters=f'WHERE OB_ID LIKE {object_id}')

    if isinstance(type_id, list):
        type_id = type_id[0]

    columns = 'OT_NAME' if name_only else '*'
    record = _select_query(table='gam_objecttype',
                           columns=columns,
                           filters=f'WHERE OT_ID LIKE {type_id}')

    return record


def _get_object_class(object_id, name_only=False):
    """
    Returns the class DB record of the given object.

    Args:
        object_id (int): The DB ID of the object.
        name_only (boolean, optional): Get only the class name, Defaults to False.

    Returns:
        (str/dict): The class name/record of the object.
    """
    type_record = _get_object_type(object_id)
    class_id = type_record[0][1]
    columns = 'OT_NAME' if name_only else '*'
    record = _select_query(table='gam_objecttype',
                           columns=columns,
                           filters=f'WHERE OT_ID LIKE {class_id}')
    return record


def _get_table_columns(table, names_only=False):
    """
    Gets the list of table columns from the specified table within the helium database.

    Args:
        table (str): The table name
        names_only (boolean): Return only the column names, Defaults to False.

    Returns:
        (list): A list of columns
    """

    try:
        connection = mysql.connector.connect(host=HE_HOST,
                                             database=HE_DB,
                                             user=HE_USER,
                                             password=HE_PASS)
        if connection.is_connected():
            cursor = connection.cursor()

            query = f"SHOW COLUMNS FROM {table}"

            cursor.execute(query)
            records = cursor.fetchall()

            if names_only:
                names_list = []
                for elem in records:
                    names_list.append(elem[0])
                records = names_list

            return records

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def _select_query(table, columns='*', filters=None, db=HE_DB):
    """
    Returns the list of records from the given table.

    Args:
        table (str): The table to look in.
        columns (str, optional): The columns to be fetched, Defaults to '*' (all).
        filters (str, optional): Conditions, e.g. 'WHERE type LIKE "cat"', Defaults to None
        db (str, optional): The database to look in, Defaults to the Helium DB.

    Returns:
        (list): The list of records.
    """
    try:
        if db == IOC_DB:
            connection = mysql.connector.connect(host=IOC_HOST,
                                                 database=IOC_DB,
                                                 user=IOC_USER,
                                                 password=IOC_PASS)
        elif db == HE_DB:
            connection = mysql.connector.connect(host=HE_HOST,
                                                 database=HE_DB,
                                                 user=HE_USER,
                                                 password=HE_PASS)
        else:
            raise ValueError(f'Invalid DB "{db}".')

        if connection.is_connected():
            cursor = connection.cursor()

            query = f"SELECT {columns} FROM {table}"
            if filters:
                query += f' {filters}'

            cursor.execute(query)
            records = cursor.fetchall()

            # If records are made of single-element tuples, convert to strings
            if len(records[0]) == 1:
                records = utilities.single_tuples_to_strings(records)

            return records

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def _insert_query(table, values):
    """
    Adds the given values into the specified columns of the table.

    Args:
        table (str): The table to insert into.
        values (dict): The values to be inserted, in a Column/Value dictionary.
    """
    try:
        connection = mysql.connector.connect(host=HE_HOST,
                                             database=HE_DB,
                                             user=HE_USER,
                                             password=HE_PASS)
        if connection.is_connected():
            cursor = connection.cursor()

            placeholders = ', '.join(['%s'] * len(values))
            columns = ', '.join(values.keys())

            query = "INSERT INTO %s ( %s ) VALUES ( %s )" % (table, columns, placeholders)

            cursor.execute(query, values)

            connection.commit()

            record_no = cursor.lastrowid

            print(f"Added record no. {record_no} to {table}")

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


