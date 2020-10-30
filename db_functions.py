"""
Contains functions for working with the IOC and HeRecovery database.
Environment variables: DB_IOCDB.USER, DB_IOCDB.PASS, DB_HEDB.USER, DB_HEDB.PASS
"""
import mysql.connector
from utilities import single_tuples_to_strings, meas_values_dict_valid
from datetime import datetime
from logger import log_db_error, log_error, DBLogger
from constants import IOCDB, HEDB, PV_IMPORT, Tables

db_logger = DBLogger()
db_logger.make_log()


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
    records = _select_query(table='pvs', columns=columns, filters=filters, db=IOCDB.NAME)

    return records


def get_object_id(object_name):
    """
    Get the ID of the object with the given name.

    Returns:
        (int): The object ID.
    """
    search = f"WHERE `OB_NAME` LIKE '{object_name}'"
    result = _select_query(table=Tables.OBJECT, columns='OB_ID', filters=search, f_elem=True)
    return result


def add_measurement(record_name, mea_values: dict, mea_valid=0):
    """
    Adds a measurement (and its relationship) to the database.

    Args:
        record_name (str): Record name of the object the measurement is for.
        mea_values (dict): A dict of the measurement values, max 5. (e.g. {1: 'val', 2: 'val2', ...} or {1: None,
            2: 'val2', 3: None, ...})
        mea_valid (boolean, optional): True if the measurement is valid, Defaults to False.
    """

    if not meas_values_dict_valid(mea_values):
        err_msg = f'Measurement values dictionary invalid: {mea_values}'
        log_error(err_msg)
        raise ValueError(err_msg)

    object_id = get_object_id(object_name=record_name)

    mea_obj_type = _get_object_type(object_id, name_only=True)
    mea_obj_class = _get_object_class(object_id, name_only=True)
    mea_comment = f'"{record_name}" ({mea_obj_type} - {mea_obj_class}) via {PV_IMPORT}'

    mea_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    measurement_dict = {
        'MEA_OBJECT_ID': object_id,
        'MEA_DATE': mea_date,
        # 'MEA_DATE2': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        # 'MEA_STATUS': ,
        'MEA_COMMENT': mea_comment,
        'MEA_VALUE1': mea_values[1],
        'MEA_VALUE2': mea_values[2],
        'MEA_VALUE3': mea_values[3],
        'MEA_VALUE4': mea_values[4],
        'MEA_VALUE5': mea_values[5],
        'MEA_VALID': 1 if mea_valid is True else 0,
        'MEA_BOOKINGCODE': 0,  # 0 = measurement is not from the balance program
    }

    _insert_query(Tables.MEASUREMENT, data=measurement_dict)

    last_id = _get_table_last_id(Tables.MEASUREMENT)
    db_logger.log_new_measurement(record_no=last_id, obj_id=object_id,
                                  obj_name=record_name, values=mea_values, print_msg=True)

    add_relationship(assigned=object_id, or_date=mea_date)


def add_relationship(assigned, or_date=None):
    """
    Adds a relationship between two objects.

    Args:
        assigned (int): The assigned object ID.
        or_date (str): The assignment and removal date of the relationship.
    """
    if not or_date:
        or_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pv_import_obj_id = _get_pv_import_object_id()
    relationship_dict = {
        'OR_PRIMARY': 0,
        'OR_OBJECT_ID': pv_import_obj_id,
        'OR_OBJECT_ID_ASSIGNED': assigned,
        'OR_DATE_ASSIGNMENT': or_date,
        'OR_DATE_REMOVAL': or_date,
        'OR_OUTFLOW': None,
        'OR_BOOKINGREQUEST': None
    }

    _insert_query(Tables.OBJECT_RELATION, relationship_dict)


def _create_pv_import_function_if_not_exist():
    """
    Creates the HLM PV Import object function if it doesn't exist in the DB yet.
    """
    # CREATE FUNCTION IF IT DOES NOT EXIST
    search = f"WHERE `OF_NAME` LIKE '{PV_IMPORT}'"
    results = _select_query(table=Tables.FUNCTION, filters=search, db=HEDB.NAME)
    if not results:
        function_dict = {'OF_NAME': PV_IMPORT, 'OF_COMMENT': 'HLM PV IMPORT'}

        _insert_query(table=Tables.FUNCTION, data=function_dict)


def _create_pv_import_class_if_not_exist():
    """
    Creates the HLM PV Import object class if it doesn't exist in the DB yet.
    """
    # CREATE CLASS IF IT DOES NOT EXIST
    search = f"WHERE OC_NAME LIKE '{PV_IMPORT}'"
    results = _select_query(table=Tables.OBJECT_CLASS, filters=search, db=HEDB.NAME)
    if not results:
        function_id = _select_query(table=Tables.FUNCTION, columns='OF_ID', filters=f"WHERE OF_NAME LIKE '{PV_IMPORT}'",
                                    db=HEDB.NAME, f_elem=True)

        last_id = _get_table_last_id(Tables.OBJECT_CLASS)
        new_id = last_id + 1

        class_dict = {
            'OC_ID': new_id,  # Need to set manually as OC_ID has no default value
            'OC_FUNCTION_ID': function_id,
            'OC_NAME': PV_IMPORT,
            'OC_POSITIONTYPE': 0,
            'OC_COMMENT': 'HLM PV IMPORT',
        }

        _insert_query(table=Tables.OBJECT_CLASS, data=class_dict)


def _create_pv_import_type_if_not_exist():
    """
    Creates the HLM PV Import type if it doesn't exist in the DB yet.
    """
    # CREATE TYPE IF IT DOES NOT EXIST
    search = f"WHERE `OT_NAME` LIKE '{PV_IMPORT}'"
    results = _select_query(table=Tables.OBJECT_TYPE, filters=search, db=HEDB.NAME)
    if not results:
        pv_import_class_id = _select_query(table=Tables.OBJECT_CLASS, columns='OC_ID',
                                           filters=f"WHERE OC_NAME LIKE '{PV_IMPORT}'", db=HEDB.NAME, f_elem=True)
        type_dict = {
            'OT_OBJECTCLASS_ID': pv_import_class_id,
            'OT_NAME': PV_IMPORT,
            'OT_COMMENT': 'HLM PV IMPORT',
            'OT_OUTOFOPERATION': 0
        }

        _insert_query(table=Tables.OBJECT_TYPE, data=type_dict)


def _create_pv_import_object_if_not_exist():
    """
    Creates the HLM PV Import object if it doesn't exist in the DB yet.
    """
    # CREATE OBJECT IF IT DOES NOT EXIST
    results = _select_query(table=Tables.OBJECT, filters=f"WHERE OB_NAME LIKE '{PV_IMPORT}'", db=HEDB.NAME)
    if not results:
        pv_import_type_id = _select_query(table=Tables.OBJECT_TYPE, columns='OT_ID',
                                          filters=f"WHERE OT_NAME LIKE '{PV_IMPORT}'", db=HEDB.NAME, f_elem=True)

        object_dict = {
            'OB_OBJECTTYPE_ID': pv_import_type_id,
            'OB_NAME': PV_IMPORT,
            'OB_COMMENT': 'HLM PV IMPORT',
        }

        _insert_query(table=Tables.OBJECT, data=object_dict)


def setup_db_pv_import():
    """
    Checks the DB for the function, class, type and object of PV IMPORT, and create them if any are missing.
    """
    _create_pv_import_function_if_not_exist()
    _create_pv_import_class_if_not_exist()
    _create_pv_import_type_if_not_exist()
    _create_pv_import_object_if_not_exist()


def _get_object_type(object_id, name_only=False):
    """
    Returns the type DB record of the given object.

    Args:
        object_id (int): The DB ID of the object.
        name_only (boolean, optional): Get only the type name, Defaults to False.

    Returns:
        (str/dict): The type name/record of the object.
    """

    type_id = _select_query(table=Tables.OBJECT, columns='OB_OBJECTTYPE_ID', filters=f'WHERE OB_ID LIKE {object_id}',
                            f_elem=True)

    columns = 'OT_NAME' if name_only else '*'
    record = _select_query(table=Tables.OBJECT_TYPE, columns=columns, filters=f'WHERE OT_ID LIKE {type_id}')
    if name_only:
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
    class_id = type_record[0][1]
    columns = 'OC_NAME' if name_only else '*'
    record = _select_query(table=Tables.OBJECT_CLASS, columns=columns, filters=f'WHERE OC_ID LIKE {class_id}')
    if name_only:
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
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(host=HEDB.HOST,
                                             database=HEDB.NAME,
                                             user=HEDB.USER,
                                             password=HEDB.PASS)
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
        if connection and cursor:
            if connection.is_connected():
                cursor.close()
                connection.close()


def _select_query(table, columns='*', filters=None, db=HEDB.NAME, f_elem=False):
    """
    Returns the list of records from the given table.

    Args:
        table (str): The table to look in.
        columns (str, optional): The columns to be fetched, Defaults to '*' (all).
        filters (str, optional): Search conditions, e.g. 'WHERE type LIKE "cat"', Defaults to None
        db (str, optional): The database to look in, Defaults to the Helium DB.
        f_elem (boolean, optional): If a list/tuple of one element is returned, return only the element,
            Defaults to False.

    Returns:
        (list/str): The list of records, or a string if single element list and to_str set to True.
    """
    connection = None
    cursor = None
    try:
        if db == IOCDB.NAME:
            connection = mysql.connector.connect(host=IOCDB.HOST,
                                                 database=IOCDB.NAME,
                                                 user=IOCDB.USER,
                                                 password=IOCDB.PASS)
        elif db == HEDB.NAME:
            connection = mysql.connector.connect(host=HEDB.HOST,
                                                 database=HEDB.NAME,
                                                 user=HEDB.USER,
                                                 password=HEDB.PASS)
        else:
            raise ValueError(f'Invalid DB "{db}".')

        if connection.is_connected():
            cursor = connection.cursor()
            columns = '*' if columns is None else columns
            query = f"SELECT {columns} FROM {table}"
            if filters:
                query += f' {filters}'

            cursor.execute(query)
            records = cursor.fetchall()

            # If records are made of single-element tuples, convert to list of strings
            if records and len(records[0]) == 1:
                records = single_tuples_to_strings(records)

            if f_elem:
                if isinstance(records, list) and len(records) == 1:
                    records = records[0]

            return records

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if connection and cursor:
            if connection.is_connected():
                cursor.close()
                connection.close()


def _insert_query(table, data):
    """
    Adds the given values into the specified columns of the table.

    Args:
        table (str): The table to insert into.
        data (dict): The values to be inserted, in a Column Name/Value dictionary.
    """
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(host=HEDB.HOST,
                                             database=HEDB.NAME,
                                             user=HEDB.USER,
                                             password=HEDB.PASS)
        if connection.is_connected():
            cursor = connection.cursor()

            placeholders = ', '.join(['%s'] * len(data))
            columns = ', '.join(data.keys())

            query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"

            values = list(data.values())
            cursor.execute(query, values)

            connection.commit()

            record_no = cursor.lastrowid
            if record_no == 0:  # If table has no AUTO_INCREMENT column
                record_no = _get_table_last_id(table)

            print(f"Added record no. {record_no} to {table}")

    except mysql.connector.Error as e:
        log_db_error(f'{e}', print_err=True)
    finally:
        if connection and cursor:
            if connection.is_connected():
                cursor.close()
                connection.close()


def _get_object_name(object_id):
    """
    Gets the DB object name corresponding to the record ID.

    Args:
        object_id (int): The object ID

    Returns:
        (str): The object name.
    """
    object_name = _select_query(table=Tables.OBJECT, columns='OB_NAME', filters=f'WHERE OB_ID LIKE {object_id}',
                                f_elem=True)

    return object_name


def _get_primary_key_column(table):
    """
    Gets the column name of the primary key in the given table.

    Returns:
        (str): The PK column name.
    """
    sql = f"WHERE TABLE_NAME = '{table}'AND CONSTRAINT_NAME = 'PRIMARY'"

    pk_column = _select_query(table='information_schema.KEY_COLUMN_USAGE', columns='COLUMN_NAME', filters=sql,
                              db=HEDB.NAME, f_elem=True)

    return pk_column


def _get_table_last_id(table):
    """
    Gets the last/highest primary key ID of the given table.

    Returns:
        (int): The last table row ID.
    """

    pk_column = _get_primary_key_column(table)

    last_id = _select_query(table=table, columns=f'MAX({pk_column})', db=HEDB.NAME, f_elem=True)

    return last_id


def _get_pv_import_object_id():
    """
    Gets the ID of the PV IMPORT object from the Objects He DB table.

    Returns:
        (int): The PV Import object ID.
    """
    search = f"WHERE OB_NAME LIKE '{PV_IMPORT}'"
    result = _select_query(table=Tables.OBJECT, columns='OB_ID', filters=search, db=HEDB.NAME, f_elem=True)

    return result
