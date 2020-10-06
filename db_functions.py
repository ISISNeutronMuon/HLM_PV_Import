"""
Contains functions for working with the IOC and HeRecovery database.
Environment variables: DB_IOC_USER, DB_IOC_PASS, DB_HE_USER, DB_HE_PASS
"""
import os
import mysql.connector

import utilities

# the IOC DB containing the list of PVs
IOC_HOST = "localhost"
IOC_DB = "iocdb"
IOC_USER = os.environ['DB_IOC_USER']
IOC_PASS = os.environ['DB_IOC_PASS']

# the HLM GAM DB
HE_HOST = "localhost"
HE_DB = "helium"
HE_USER = os.environ['DB_HE_USER']
HE_PASS = os.environ['DB_HE_PASS']


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

    try:
        connection = mysql.connector.connect(host=IOC_HOST,
                                             database=IOC_DB,
                                             user=IOC_USER,
                                             password=IOC_PASS)
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

            # If records is made of single-element tuples, convert to strings
            if len(records[0]) == 1:
                records = utilities.single_tuples_to_strings(records)

            return records

    except mysql.connector.Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# def add_coordinator(name, value):
#     """
#     OB_OBJECTTYPE_ID (int): ID of the type of this object. Set to 1 (coordinator).
#     OB_NAME (str): Name of object
#     OB_ADDRESS (str): The XBee Address (or IP for LAN Gascount. Mod.)
#     OB_COMMENT (str): Comments regarding this object
#     OB_POSINFORMATION (str): Physical position of the device
#     OB_IP (str): The IP address of the device
#     OB_COMPORT (str): Device COM Port
#     OB_NW_ID (int): ID of the network this object is on
#     """
#     try:
#         connection = mysql.connector.connect(host=HE_HOST,
#                                              database=HE_DB,
#                                              user=HE_USER,
#                                              password=HE_PASS)
#         if connection.is_connected():
#             cursor = connection.cursor()
#
#             insert_statement = ("INSERT INTO gam_object "
#                                 "(OB_OBJECTTYPE_ID, OB_NAME, OB_ADDRESS, OB_COMMENT, OB_POSINFORMATION, OB_IP, "
#                                 "OB_COMPORT, OB_NW_ID) "
#                                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
#
#             device_data = ('1', 'test_name', 'test_addr', 'commen', 'posinfo', 'ip1929932', 'COMTEST', '2')
#
#             cursor.execute(insert_statement, device_data)
#
#             connection.commit()
#
#             device_no = cursor.lastrowid
#             print(f"Added device no. {device_no} to DB")
#
#     except mysql.connector.Error as e:
#         print("Error while connecting to MySQL", e)
#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()

