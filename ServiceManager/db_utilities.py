"""
Contains functions for working with the HeRecovery database.
"""
import mysql.connector
from ServiceManager.utilities import single_tuples_to_strings
from ServiceManager.settings import Settings, Tables
from ServiceManager.logger import logger


def get_object(object_id):
    """
    Gets the record of the object with the given ID.

    Returns:

    """
    result = _select(table=Tables.OBJECT, filters='WHERE `OB_ID` = %s', filters_args=(object_id,))
    return result


def get_object_id(object_name: str):
    """
    Get the ID of the object with the given name.

    Returns:
        (int/list): The object ID, empty list if it wasn't found.
    """
    search = 'WHERE `OB_NAME` LIKE %s'
    search_data = (object_name,)
    result = _select(table=Tables.OBJECT, columns='OB_ID', filters=search, filters_args=search_data, f_elem=True)
    return result


def get_object_name(object_id):
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


def get_all_object_names():
    """
    Get a list of all object names in the Helium DB.

    Returns:
        (list): The PV names.
    """
    object_names = _select(table=Tables.OBJECT, columns='OB_NAME')
    return object_names


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
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(host=Settings.Service.HeliumDB.get_host(),
                                             database=Settings.Service.HeliumDB.get_name(),
                                             user=Settings.Service.HeliumDB.get_user(),
                                             password=Settings.Service.HeliumDB.get_pass())

        if connection.is_connected():
            cursor = connection.cursor()
            columns = '*' if columns is None else columns
            query = f"SELECT {columns} FROM {table}"
            if filters:
                query += f' {filters}'

            cursor.execute(query, filters_args)
            records = cursor.fetchall()

            # If records are made of single-element tuples, convert to list of strings
            if records and len(records[0]) == 1:
                records = single_tuples_to_strings(records)

            if f_elem:
                if isinstance(records, list) and len(records) == 1:
                    records = records[0]

            return records

    except mysql.connector.Error as e:
        logger.ERROR(f'{e}')
    finally:
        if connection and cursor:
            if connection.is_connected():
                cursor.close()
                connection.close()


def _insert(table, data):
    """
    Adds the given values into the specified columns of the table.

    Args:
        table (str): The table to insert into.
        data (dict): The values to be inserted, in a Column Name/Value dictionary.
    """
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(host=Settings.Service.HeliumDB.get_host(),
                                             database=Settings.Service.HeliumDB.get_name(),
                                             user=Settings.Service.HeliumDB.get_user(),
                                             password=Settings.Service.HeliumDB.get_pass())
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
        logger.ERROR(f'{e}')
    finally:
        if connection and cursor:
            if connection.is_connected():
                cursor.close()
                connection.close()


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


def get_object_type(object_id, name_only=False):
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
    if name_only:
        record = record[0]

    return record


def get_object_class(object_id, name_only=False):
    """
    Returns the class DB record of the given object.

    Args:
        object_id (int): The DB ID of the object.
        name_only (boolean, optional): Get only the class name, Defaults to False.

    Returns:
        (str/dict): The class name/record of the object.
    """
    type_record = get_object_type(object_id)
    class_id = type_record[0][1]
    columns = 'OC_NAME' if name_only else '*'
    record = _select(table=Tables.OBJECT_CLASS, columns=columns, filters='WHERE OC_ID LIKE %s',
                     filters_args=(class_id,))
    if name_only:
        record = record[0]

    return record
