import os
import mysql.connector

import utilities


def get_pv_records(f_arg=None, *args):
    """
    Get the list of PVs containing the Helium Recovery PLC data.

    args:
        f_arg (str, optional): The column to get from the table row. Defaults to None.
        *args: Variable length argument list containing multiple columns.

    returns:
        The list of PV records.

    notes:
        Columns/PV Attributes: ['pvname', 'record_type', 'record_desc', 'iocname'].

        If arguments are not provided, all columns (PV attributes) will be selected.

        Invalid arguments (not a valid column) will be ignored.
    """

    db_user = os.environ['DB_IOC_USER']
    db_pass = os.environ['DB_IOC_PASS']

    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='iocdb',
                                             user=db_user,
                                             password=db_pass)
        if connection.is_connected():
            cursor = connection.cursor()

            valid_columns = ['pvname', 'record_type', 'record_desc', 'iocname']
            columns = []
            if f_arg and f_arg in valid_columns:
                columns.append(f_arg)
                for arg in args:
                    if arg in valid_columns and arg not in columns:
                        columns.append(arg)
                columns = ','.join(columns)
            else:
                columns = '*'

            query = f"SELECT {columns} FROM pvs WHERE pvname LIKE '%HLM%'"

            cursor.execute(query)
            records = cursor.fetchall()

            if len(records[0]) == 1:  # If records is made of single-element tuples, convert to strings
                records = utilities.single_elem_tuples_to_strings(records)

            return records

    except mysql.connector.Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
