"""
Contains functions for working with the HeRecovery database.
"""
from datetime import datetime

import mysql.connector
from ServiceManager.utilities import single_tuples_to_strings
from ServiceManager.logger import manager_logger


class Tables:
    MEASUREMENT = 'gam_measurement'
    OBJECT = 'gam_object'
    OBJECT_TYPE = 'gam_objecttype'
    OBJECT_CLASS = 'gam_objectclass'
    OBJECT_RELATION = 'gam_objectrelation'
    FUNCTION = 'gam_function'


class DatabaseUtilities:

    def __init__(self):
        self.connection = None
        self.logger = None

    def make_connection(self, host, database, user, password):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
        try:
            self.connection = mysql.connector.connect(host=host, database=database, user=user, password=password)
        except Exception as e:
            raise DBConnectionError(f'DB Connection Error: {e}')

    def is_connected(self):
        return self.connection and self.connection.is_connected()

    def get_object(self, object_id):
        """
        Gets the record of the object with the given ID.

        Returns:

        """
        result = self._select(table=Tables.OBJECT, filters='WHERE `OB_ID` = %s', filters_args=(object_id,))
        return result

    def get_object_id(self, object_name: str):
        """
        Get the ID of the object with the given name.

        Returns:
            (int/list): The object ID, empty list if it wasn't found.
        """
        search = 'WHERE `OB_NAME` LIKE %s'
        search_data = (object_name,)
        result = self._select(table=Tables.OBJECT, columns='OB_ID', filters=search, filters_args=search_data,
                              f_elem=True)
        return result if result else None

    def get_object_name(self, object_id):
        """
        Gets the DB object name corresponding to the record ID.

        Args:
            object_id (int): The object ID

        Returns:
            (str): The object name.
        """
        object_name = self._select(table=Tables.OBJECT, columns='OB_NAME', filters='WHERE OB_ID LIKE %s',
                                   filters_args=(object_id,), f_elem=True)

        return object_name

    def get_all_object_names(self):
        """
        Get a list of all object names in the Helium DB.

        Returns:
            (list): The object names.
        """
        object_names = self._select(table=Tables.OBJECT, columns='OB_NAME')
        return object_names

    def get_all_type_names(self):
        """
        Get a list of all type names from the Helium DB.

        Returns:
            (list): The type names.
        """
        type_names = self._select(table=Tables.OBJECT_TYPE, columns='OT_NAME')
        return type_names

    def get_type_id(self, type_name: str):
        """
        Gets the type name using its ID.

        Args:
            type_name (str): The type name.

        Returns:
            type_id (int): The type ID.
        """
        type_id = self._select(table=Tables.OBJECT_TYPE, columns='OT_ID',
                               filters='WHERE OT_NAME LIKE %s', filters_args=(type_name,), f_elem=True)
        return type_id

    def add_object(self, name: str, type_id: int, comment: str = None):
        """
        Add an object to the database, with the given name, type and comment. Other fields will be blank.

        Args:
            name (str): The name of the object.
            type_id (int): The type ID of the object.
            comment (str): Comments regarding the object.

        Raises:
            ValueError: If an object with the given name already exists in the database.
        """
        already_exists = self.get_object_id(object_name=name)
        if already_exists:
            msg = f'Could not create object - Object with name "{name}" already exists in the database.'
            manager_logger.error(msg)
            raise DBUtilsObjectNameAlreadyExists(msg)

        data = {'OB_NAME': name, 'OB_OBJECTTYPE_ID': type_id, 'OB_COMMENT': comment}

        self._insert(table=Tables.OBJECT, data=data)

    def add_relation(self, or_object_id, or_object_id_assigned, start_date=None, removal_date=None):
        """
        Makes a relation between two objects. Dates must be in '%Y-%m-%d %H:%M:%S' format.

        Args:
            or_object_id (int): The object ID (the object itself).
            or_object_id_assigned (int): The assigned object ID (e.g. the SLD/ILM Module etc.).
            start_date (str, optional): The starting date of the relation, Defaults to current time.
            removal_date (str, optional): The removal date of the relation, Defaults to None.
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        relation_dict = {
            'OR_PRIMARY': 0,
            'OR_OBJECT_ID': or_object_id,
            'OR_OBJECT_ID_ASSIGNED': or_object_id_assigned,
            'OR_DATE_ASSIGNMENT': start_date,
            'OR_DATE_REMOVAL': removal_date,
            'OR_OUTFLOW': None,
            'OR_BOOKINGREQUEST': None
        }

        self._insert(Tables.OBJECT_RELATION, relation_dict)

    def _select(self, table: str, columns: str = '*', filters: str = None, filters_args: tuple = None,
                f_elem: bool = False):
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
            if self.connection and self.connection.is_connected():
                cursor = self.connection.cursor()
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
            manager_logger.error(f'{e}')
        finally:
            if cursor:
                cursor.close()

    def _insert(self, table: str, data: dict):
        """
        Adds the given values into the specified columns of the table.

        Args:
            table (str): The table to insert into.
            data (dict): The values to be inserted, in a Column Name/Value dictionary.
        """
        cursor = None
        try:
            if self.connection and self.connection.is_connected():
                cursor = self.connection.cursor()

                placeholders = ', '.join(['%s'] * len(data))
                columns = ', '.join(data.keys())

                query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"

                values = list(data.values())
                cursor.execute(query, values)

                self.connection.commit()

                record_no = cursor.lastrowid
                if record_no == 0:  # If table has no AUTO_INCREMENT column
                    record_no = self._get_table_last_id(table)

                manager_logger.info(f"Added record no. {record_no} to {table}")

        except mysql.connector.Error as e:
            manager_logger.error(f'{e}')
        finally:
            if cursor:
                cursor.close()

    def _get_primary_key_column(self, table: str):
        """
        Gets the column name of the primary key in the given table.

        Returns:
            (str): The PK column name.
        """
        sql = "WHERE TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'"
        info_schema = 'information_schema.KEY_COLUMN_USAGE'
        pk_column = self._select(table=info_schema, columns='COLUMN_NAME', filters=sql, filters_args=(table,),
                                 f_elem=True)

        return pk_column

    def _get_table_last_id(self, table):
        """
        Gets the last/highest primary key ID of the given table.

        Returns:
            (int): The last table row ID.
        """

        pk_column = self._get_primary_key_column(table)

        last_id = self._select(table=table, columns=f'MAX({pk_column})', f_elem=True)

        return last_id

    def get_object_type(self, object_id: int, name_only: bool = False):
        """
        Returns the type DB record of the given object.

        Args:
            object_id (int): The DB ID of the object.
            name_only (boolean, optional): Get only the type name, Defaults to False.

        Returns:
            (str/list): The type name/record of the object.
        """

        type_id = self._select(table=Tables.OBJECT, columns='OB_OBJECTTYPE_ID', filters='WHERE OB_ID LIKE %s',
                               filters_args=(object_id,), f_elem=True)
        columns = 'OT_NAME' if name_only else '*'
        record = self._select(table=Tables.OBJECT_TYPE, columns=columns, filters='WHERE OT_ID LIKE %s',
                              filters_args=(type_id,))
        if name_only and record:
            record = record[0]

        return record

    def get_object_class(self, object_id: int, name_only=False, id_only=False):
        """
        Returns the class DB record of the given object.

        Args:
            object_id (int): The DB ID of the object.
            name_only (boolean, optional): Get only the class name, Defaults to False.
            id_only (boolean, optional): Get only the class ID, Defaults to False.

        Returns:
            (str/list): The class name/record of the object.
        """
        type_record = self.get_object_type(object_id)
        class_id = type_record[0][1]
        columns = 'OC_NAME' if name_only else 'OC_ID' if id_only else '*'
        record = self._select(table=Tables.OBJECT_CLASS, columns=columns, filters='WHERE OC_ID LIKE %s',
                              filters_args=(class_id,))
        if name_only or id_only:
            record = record[0]

        return record

    def get_class_id(self, type_id: int):
        """
        Returns the class DB record of the given object.

        Args:
            type_id (int): The DB ID of the type.

        Returns:
            (int): The class ID of the object.
        """
        class_id = self._select(table=Tables.OBJECT_TYPE, columns='OT_OBJECTCLASS_ID',
                                filters='WHERE OT_ID = %s', filters_args=(type_id,))

        if isinstance(class_id, list):
            class_id = class_id[0]

        return class_id

    def get_object_function(self, object_id: int, name_only=False):
        """
        Returns the function DB record of the given object.

        Args:
            object_id (int): The DB ID of the object.
            name_only (boolean, optional): Get only the function name, Defaults to False.

        Returns:
            (str/list): The function name/record of the object.
        """
        class_record = self.get_object_class(object_id)
        func_id = class_record[0][1]
        columns = 'OF_NAME' if name_only else '*'
        record = self._select(table=Tables.FUNCTION, columns=columns, filters='WHERE OF_ID LIKE %s',
                              filters_args=(func_id,))
        if name_only:
            record = record[0]

        return record

    def get_object_sld(self, object_id: int, name_only=False, id_only=False):
        """
        Searches the relations table to find the Software Level Device of the given object and return its record.

        Args:
            object_id (int): The object ID.
            name_only (boolean, optional): Return only the name, Defaults to False.
            id_only (boolean, optional): Return the ID only, Defaults to False.

        Returns:
            (str/int/list): The Software Level Device record, ID or name.
        """
        # OR_OBJECT_ID = Object, OR_OBJECT_ID_ASSIGNED = ILM/SLD
        # Software level device TYPE ID = 18
        search = "WHERE OR_OBJECT_ID = %s AND OR_DATE_REMOVAL IS NULL ORDER BY OR_ID DESC;"
        relations = self._select(table=Tables.OBJECT_RELATION, filters=search, filters_args=(object_id,))
        if relations is None:
            return
        for relation in relations:
            ob_assigned_id = relation[3]
            ob_assigned = self._select(table=Tables.OBJECT, filters='WHERE OB_ID = %s', filters_args=(ob_assigned_id,))
            ob_assigned_type_id = ob_assigned[0][1]
            if ob_assigned_type_id == 18:
                if name_only is True:
                    return ob_assigned[0][2]
                elif id_only is True:
                    return ob_assigned[0][0]
                else:
                    return ob_assigned

    def get_class_measurement_types(self, class_id: int):
        """
        Returns the measurement types of the given class.

        Args:
            class_id (int): The class ID.

        Returns:
            (dict): The measurement types as a dict (Mea. No. / Type pairs).
        """
        mea_types = {}
        cols = 'OC_MEASURETYPE1, OC_MEASURETYPE2, OC_MEASURETYPE3, OC_MEASURETYPE4, OC_MEASURETYPE5'
        filter_ = 'WHERE OC_ID = %s'
        result = self._select(table=Tables.OBJECT_CLASS, columns=cols, filters=filter_, filters_args=(class_id,))

        for index, type_ in enumerate(result[0]):
            mea_types[index+1] = type_

        return mea_types


class DBUtilsObjectNameAlreadyExists(Exception):
    def __init__(self, err_msg):
        super(DBUtilsObjectNameAlreadyExists, self).__init__(err_msg)


class DBConnectionError(Exception):
    def __init__(self, err_msg):
        super(DBConnectionError, self).__init__(err_msg)


DBUtils = DatabaseUtilities()
