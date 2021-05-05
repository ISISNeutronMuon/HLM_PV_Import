"""
Contains functions for working with the HeRecovery database.
"""
import sys
import time

import mysql.connector
from datetime import datetime
from HLM_PV_Import.logger import log_db_error, DBLogger
from HLM_PV_Import.settings import HEDB, Tables

# setup the database events logger
db_logger = DBLogger()
db_logger.make_log()

# Explicit access to module level variables by accessing them explicitly on the module
this = sys.modules[__name__]

this.connection = None
this.reconnect_wait_time = HEDB.RECONNECT_WAIT


# Establish the database connection
def make_db_connection():
    try:
        this.connection = mysql.connector.connect(host=HEDB.HOST, database=HEDB.NAME,
                                                  user=HEDB.USER, password=HEDB.PASS)
    except Exception as e:
        sys.stderr.write(f'{e}\n')
        this.connection = None


make_db_connection()


def db_is_connected(attempt: int = 1):
    """
    Check if DB is connected, and if not attempt to re-establish it.
    """
    if attempt > HEDB.RECONNECT_ATTEMPTS_MAX:
        raise Exception('Connection to the database was lost and could not be re-established.')
    elif this.connection and this.connection.is_connected():
        this.reconnect_wait_time = HEDB.RECONNECT_WAIT  # reset the wait time
        return True
    else:
        time.sleep(this.reconnect_wait_time)
        this.reconnect_wait_time = HEDB.reconnect_wait_increase(current_wait=this.reconnect_wait_time)
        print(f'Connection to the database was lost, attempting to reconnect. (Attempt: {attempt})')
        make_db_connection()
        return db_is_connected(attempt + 1)


def get_object(object_id):
    """
    Gets the record of the object with the given ID.

    Returns:

    """
    result = _select(table=Tables.OBJECT, filters='WHERE `OB_ID` = %s', filters_args=(object_id,))
    return result


def get_object_id(object_name):
    """
    Get the ID of the object with the given name.

    Returns:
        (int): The object ID.
    """
    search = 'WHERE `OB_NAME` LIKE %s'
    search_data = (object_name,)
    result = _select(table=Tables.OBJECT, columns='OB_ID', filters=search, filters_args=search_data, f_elem=True)
    return result


def add_measurement(object_id, mea_values: dict, mea_valid=True):
    """
    Adds a measurement to the database. If the object currently has a Software Level Device, the measurement object will
    be the SLD. Otherwise, it will be the object itself.

    Args:
        object_id (int): Record/Object id of the object the measurement is for.
        mea_values (dict): A dict of the measurement values, max 5, in measurement_number(str)/pv_value pairs.
        mea_valid (boolean, optional): Whether the measurement is valid, Defaults to True.
    """
    record_name = _get_object_name(object_id)
    mea_obj_type = _get_object_type(object_id, name_only=True)
    mea_obj_class = _get_object_class(object_id, name_only=True)

    # Check if object has a Software Level Device
    sld = get_object_sld(object_id)
    if sld:
        sld_id = sld[0][0]
        mea_comment = f'SLD for {object_id} "{record_name}" ({mea_obj_type} - {mea_obj_class}) via HLM PV IMPORT'
        object_id = sld_id  # Add measurements to the SLD instead of directly to the object
    else:
        mea_comment = f'"{record_name}" ({mea_obj_type} - {mea_obj_class}) via HLM PV IMPORT'

    mea_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    measurement_dict = {
        'MEA_OBJECT_ID': object_id,
        'MEA_DATE': mea_date,
        'MEA_DATE2': mea_date,
        # 'MEA_STATUS': ,
        'MEA_COMMENT': mea_comment,
        'MEA_VALUE1': mea_values['1'],
        'MEA_VALUE2': mea_values['2'],
        'MEA_VALUE3': mea_values['3'],
        'MEA_VALUE4': mea_values['4'],
        'MEA_VALUE5': mea_values['5'],
        'MEA_VALID': 1 if mea_valid is True else 0,
        'MEA_BOOKINGCODE': 0,  # 0 = measurement is not from the balance program (HZB)
    }
    _insert(Tables.MEASUREMENT, data=measurement_dict)

    last_id = _get_table_last_id(Tables.MEASUREMENT)
    db_logger.log_new_measurement(record_no=last_id, obj_id=object_id,
                                  obj_name=record_name, values=mea_values, print_msg=True, print_only=True)


def get_object_sld(object_id: int):
    """
    Searches the relations table to find the Software Level Device of the given object and return its record.

    Args:
        object_id (int): The object ID.

    Returns:
        (list): The Software Level Device record.
    """
    # OR_OBJECT_ID = Object, OR_OBJECT_ID_ASSIGNED = ILM/SLD
    # Software level device TYPE ID = 18
    search = "WHERE OR_OBJECT_ID = %s AND OR_DATE_REMOVAL IS NULL ORDER BY OR_ID DESC;"
    relations = _select(table=Tables.OBJECT_RELATION, filters=search, filters_args=(object_id,))
    if not relations:
        return
    for relation in relations:
        ob_assigned_id = relation[3]
        ob_assigned = _select(table=Tables.OBJECT, filters='WHERE OB_ID = %s', filters_args=(ob_assigned_id,))
        ob_assigned_type_id = ob_assigned[0][1]
        if ob_assigned_type_id == 18:
            return ob_assigned


def _get_object_type(object_id, name_only=False):
    """
    Returns the type DB record of the given object.

    Args:
        object_id (int): The DB ID of the object.
        name_only (boolean, optional): Get only the type name, Defaults to False.

    Returns:
        (str/dict): The type name/record of the object.
    """

    type_id = _select(table=Tables.OBJECT, columns='OB_OBJECTTYPE_ID', filters='WHERE OB_ID LIKE %s',
                      filters_args=(object_id,), f_elem=True)

    columns = 'OT_NAME' if name_only else '*'
    record = _select(table=Tables.OBJECT_TYPE, columns=columns, filters='WHERE OT_ID LIKE %s', filters_args=(type_id,))
    if record and name_only:
        record = record[0]

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
    if type_record:
        class_id = type_record[0][1]
    else:
        return
    columns = 'OC_NAME' if name_only else '*'
    record = _select(table=Tables.OBJECT_CLASS, columns=columns, filters='WHERE OC_ID LIKE %s',
                     filters_args=(class_id,))
    if record and name_only:
        record = record[0]

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
    cursor = None
    try:
        if db_is_connected():
            cursor = this.connection.cursor()

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
        if cursor:
            cursor.close()


def _select(table, columns='*', filters=None, filters_args=None, f_elem=False):
    """
    Returns the list of records from the given table.

    Args:
        table (str): The table to look in.
        columns (str, optional): The columns to be fetched, Defaults to '*' (all).
        filters (str, optional): Search conditions, e.g. 'WHERE type LIKE %s', Defaults to None
        filters_args (tuple, optional): Search conditions data, e.g. ('cat',)
        f_elem (boolean, optional): If a list/tuple of one element is returned, return only the element,
            Defaults to False.

    Returns:
        (list/str): The list of records, or a string if single element list and to_str set to True.
    """
    cursor = None
    try:
        if db_is_connected():
            cursor = this.connection.cursor()
            columns = '*' if columns is None else columns
            query = f"SELECT {columns} FROM {table}"
            if filters:
                query += f' {filters}'

            cursor.execute(query, filters_args)
            records = cursor.fetchall()

            # If records are made of single-element tuples, convert to list of strings
            if records and len(records[0]) == 1:
                records = [elem[0] if len(elem) == 1 else elem for elem in records]

            if f_elem:
                if isinstance(records, list) and len(records) == 1:
                    records = records[0]

            return records

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if cursor:
            cursor.close()


def _insert(table, data):
    """
    Adds the given values into the specified columns of the table.

    Args:
        table (str): The table to insert into.
        data (dict): The values to be inserted, in a Column Name/Value dictionary.
    """
    cursor = None
    try:
        if db_is_connected():
            cursor = this.connection.cursor()

            placeholders = ', '.join(['%s'] * len(data))
            columns = ', '.join(data.keys())

            query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"

            values = list(data.values())
            cursor.execute(query, values)

            this.connection.commit()

            record_no = cursor.lastrowid
            if record_no == 0:  # If table has no AUTO_INCREMENT column
                record_no = _get_table_last_id(table)

            db_logger.log_insert(table=table, record_id=record_no)

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if cursor:
            cursor.close()


def _get_object_name(object_id):
    """
    Gets the DB object name corresponding to the record ID.

    Args:
        object_id (int): The object ID

    Returns:
        (str): The object name.
    """
    object_name = _select(table=Tables.OBJECT, columns='OB_NAME', filters='WHERE OB_ID LIKE %s',
                          filters_args=(object_id,), f_elem=True)

    return object_name


def _get_primary_key_column(table):
    """
    Gets the column name of the primary key in the given table.

    Returns:
        (str): The PK column name.
    """
    sql = "WHERE TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'"
    info_schema = 'information_schema.KEY_COLUMN_USAGE'
    pk_column = _select(table=info_schema, columns='COLUMN_NAME', filters=sql, filters_args=(table,), f_elem=True)

    return pk_column


def _get_table_last_id(table):
    """
    Gets the last/highest primary key ID of the given table.

    Returns:
        (int): The last table row ID.
    """

    pk_column = _get_primary_key_column(table)

    last_id = _select(table=table, columns=f'MAX({pk_column})', f_elem=True)

    return last_id
