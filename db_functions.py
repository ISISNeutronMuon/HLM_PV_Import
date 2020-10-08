"""
Contains functions for working with the IOC and HeRecovery database.
Environment variables: DB_IOC_USER, DB_IOC_PASS, DB_HE_USER, DB_HE_PASS
"""
import os
import mysql.connector
from object_classes import *
import utilities as utilities

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


def add_vessel(vessel: EpicsVessel):
    """
    Create a new vessel record of given vessel type.

    Args:
        vessel (EpicsVessel): The vessel object

    """
    try:
        connection = mysql.connector.connect(host=HE_HOST,
                                             database=HE_DB,
                                             user=HE_USER,
                                             password=HE_PASS)
        if connection.is_connected():
            cursor = connection.cursor()

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
            placeholders = ', '.join(['%s'] * len(vessel_dict))
            columns = ', '.join(vessel_dict.keys())
            sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (table, columns, placeholders)

            # If keys, values and items views are iterated over with no intervening modifications
            # to the dictionary, the order of items will directly correspond.
            cursor.execute(sql, list(vessel_dict.values()))

            connection.commit()

            record_no = cursor.lastrowid
            print(f"Added record no. {record_no} to {table}")

    except mysql.connector.Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

