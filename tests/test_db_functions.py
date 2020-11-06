
import unittest
from mock import patch, DEFAULT
from parameterized import parameterized
from HLM_PV_Import import db_functions
from HLM_PV_Import.constants import Tables, DB_OBJ_NAME, HEDB
from datetime import datetime


class TestDbFunctions(unittest.TestCase):

    @patch('HLM_PV_Import.db_functions._select_query')
    def test_GIVEN_object_name_WHEN_get_object_id_THEN_correct_search_query(self, mock_select_query):
        db_functions.get_object_id('obj_name')
        search = f"WHERE `OB_NAME` LIKE 'obj_name'"
        mock_select_query.assert_called_with(table=Tables.OBJECT, columns='OB_ID',
                                             filters=search, f_elem=True)

    @parameterized.expand([('date', 'date'), (None, 'current date')])
    @patch.multiple('HLM_PV_Import.db_functions', _get_pv_import_object_id=DEFAULT,
                    _insert_query=DEFAULT, datetime=DEFAULT)
    def test_WHEN_add_relationship_THEN_correct_date(self, date, expected, **mocks):
        # Arrange
        mock_get_import_id = mocks['_get_pv_import_object_id']
        mock_insert = mocks['_insert_query']
        mock_datetime = mocks['datetime']
        mock_datetime.now.return_value.strftime.return_value = 'current date'
        mock_get_import_id.return_value = 42

        assigned_obj = 1

        expected_dict = {
            'OR_PRIMARY': 0,
            'OR_OBJECT_ID': 42,
            'OR_OBJECT_ID_ASSIGNED': 1,
            'OR_DATE_ASSIGNMENT': expected,
            'OR_DATE_REMOVAL': expected,
            'OR_OUTFLOW': None,
            'OR_BOOKINGREQUEST': None
        }

        # Act
        db_functions.add_relationship(assigned_obj, date)

        # Assert
        mock_insert.assert_called_with(Tables.OBJECT_RELATION, expected_dict)

    @parameterized.expand([
        (False, [(1, 2, 'Coordinator default')], [(1, 2, 'Coordinator default')], '*'),
        (True, ['Coordinator default'], 'Coordinator default', 'OT_NAME')
    ])
    @patch('HLM_PV_Import.db_functions._select_query')
    def test_GIVEN_object_id_WHEN_get_object_type_THEN_correct_type_row_returned(self, name_only, obj_type, exp_val,
                                                                                 columns, mock_select):
        # Arrange
        mock_select.side_effect = [123, obj_type]

        # Act
        result = db_functions._get_object_type(1, name_only=name_only)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_TYPE, columns=columns,
                                       filters=f'WHERE OT_ID LIKE {123}')
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        (False, [(1, 1, 'Coordinator')], [(1, 1, 'Coordinator')], '*'),
        (True, ['Coordinator default'], 'Coordinator default', 'OC_NAME')
    ])
    @patch.multiple('HLM_PV_Import.db_functions', _get_object_type=DEFAULT, _select_query=DEFAULT)
    def test_GIVEN_object_id_WHEN_get_object_class_THEN_correct_class_row_returned(self, name_only, select_val, exp_val,
                                                                                   columns, **mocks):
        # Arrange
        mock_get_type = mocks['_get_object_type']
        mock_select = mocks['_select_query']

        mock_get_type.return_value = [(1, 123, 'Coordinator default', 3, None, None, None)]
        mock_select.return_value = select_val

        # Act
        result = db_functions._get_object_class(object_id=1, name_only=name_only)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_CLASS, columns=columns,
                                       filters=f'WHERE OC_ID LIKE {123}')
        self.assertEqual(exp_val, result)

    @patch('HLM_PV_Import.db_functions._select_query')
    def test_WHEN_get_object_name_THEN_correct_select_query_called(self, mock_select):
        obj_id = 123
        db_functions._get_object_name(obj_id)
        mock_select.assert_called_with(
            table=Tables.OBJECT,
            columns='OB_NAME',
            filters=f'WHERE OB_ID LIKE {obj_id}',
            f_elem=True
        )

    @patch.multiple('HLM_PV_Import.db_functions', _select_query=DEFAULT, _get_primary_key_column=DEFAULT)
    def test_WHEN_get_table_last_row_id_THEN_correct_select_query_called(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_pk_col = mocks['_get_primary_key_column']

        mock_pk_col.return_value = 'pk_column_name'
        mock_select.return_value = 123

        table = 'table_name'

        # Act
        db_functions._get_table_last_id(table)

        # Assert
        mock_select.assert_called_with(
            table=table,
            columns=f'MAX({mock_pk_col()})',
            f_elem=True
        )

    @patch('HLM_PV_Import.db_functions._select_query')
    def test_WHEN_get_table_primary_key_column_THEN_correct_select_query_called(self, mock_select):
        # Arrange
        table = 'table_name'

        # Act
        db_functions._get_primary_key_column(table)

        # Assert
        mock_select.assert_called_with(
            table='information_schema.KEY_COLUMN_USAGE',
            columns='COLUMN_NAME',
            filters=f"WHERE TABLE_NAME = '{table}'AND CONSTRAINT_NAME = 'PRIMARY'",
            f_elem=True
        )


class TestSelectAndInsert(unittest.TestCase):

    def setUp(self):
        patcher = patch('mysql.connector.connect')
        self.addCleanup(patcher.stop)
        self.mock_connect = patcher.start()

    @parameterized.expand([
        ('table_name', 'col1, col2', 'WHERE a LIKE b', 'SELECT col1, col2 FROM table_name WHERE a LIKE b'),
        ('table_name', 'column_name', 'WHERE a LIKE b', 'SELECT column_name FROM table_name WHERE a LIKE b'),
        ('table_name', None, 'WHERE a LIKE b', 'SELECT * FROM table_name WHERE a LIKE b'),
        ('table_name', None, None, 'SELECT * FROM table_name')
    ])
    def test_GIVEN_args_WHEN_select_query_THEN_correct_query_created(self, table, columns, search, expected):
        connection = self.mock_connect.return_value
        cursor = connection.cursor.return_value

        db_functions._select_query(table=table, columns=columns, filters=search)
        cursor.execute.assert_called_with(expected)

    @parameterized.expand([
        (False, [(64,)], [64]),
        (False, [(64, 'text')], [(64, 'text')]),
        (False, None, None),
        (True, [(64,)], 64),
        (True, [(64, 'text')], (64, 'text')),
        (True, None, None)
    ])
    def test_GIVEN_records_and_settings_WHEN_get_select_records_THEN_prepared_records_returned(self, f_elem, records,
                                                                                               expected):
        connection = self.mock_connect.return_value
        cursor = connection.cursor.return_value

        cursor.fetchall.return_value = records

        result = db_functions._select_query(table='', f_elem=f_elem)
        self.assertEqual(expected, result)

    @parameterized.expand([
        (
                {'col1': 'val1', 'col2': 'val2', 'col3': 'val3'},
                'INSERT INTO `table` (col1, col2, col3) VALUES (%s, %s, %s)',
                ['val1', 'val2', 'val3']
        ),
        (
                {'col1': 'val1'},
                'INSERT INTO `table` (col1) VALUES (%s)',
                ['val1']
        ),
        (
                {'col1': 'val1', 'col2': 2, 'col3': None, 'col4': [1, (1, 'a'), (2,)]},
                'INSERT INTO `table` (col1, col2, col3, col4) VALUES (%s, %s, %s, %s)',
                ['val1', 2, None, [1, (1, 'a'), (2,)]]
        ),
    ])
    def test_GIVEN_data_WHEN_insert_query_THEN_correct_query_and_values(self, data, exp_query, exp_values):
        connection = self.mock_connect.return_value
        cursor = connection.cursor.return_value
        db_functions._insert_query('table', data)
        cursor.execute.assert_called_with(exp_query, exp_values)


class TestAddMeasurement(unittest.TestCase):

    def setUp(self):
        patcher = patch.multiple('HLM_PV_Import.db_functions', datetime=DEFAULT, db_logger=DEFAULT,
                                 _get_table_last_id=DEFAULT, add_relationship=DEFAULT, _insert_query=DEFAULT,
                                 _get_object_class=DEFAULT, _get_object_type=DEFAULT, get_object_id=DEFAULT,
                                 log_error=DEFAULT, log_db_error=DEFAULT)
        self.addCleanup(patcher.stop)
        self.mocks = patcher.start()

    def test_GIVEN_valid_values_WHEN_add_measurement_THEN_correct_insert_query(self):
        # Arrange
        mock_obj_id = self.mocks['get_object_id']
        mock_obj_type = self.mocks['_get_object_type']
        mock_obj_class = self.mocks['_get_object_class']
        mock_datetime = self.mocks['datetime']
        mock_insert_query = self.mocks['_insert_query']

        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}
        mea_valid = True

        mock_obj_id.return_value = 0
        mock_datetime.now.return_value = datetime(1, 2, 3, 4, 5, 6)
        mock_obj_type.return_value = 'obj_type_name'
        mock_obj_class.return_value = 'obj_class_name'

        expected_comment = f'"record_name" (obj_type_name - obj_class_name) via {DB_OBJ_NAME}'
        expected_dict = {
            'MEA_OBJECT_ID': 0,
            'MEA_DATE': '0001-02-03 04:05:06',
            'MEA_COMMENT': expected_comment,
            'MEA_VALUE1': 'a',
            'MEA_VALUE2': 'b',
            'MEA_VALUE3': 'c',
            'MEA_VALUE4': 'd',
            'MEA_VALUE5': 'e',
            'MEA_VALID': 1,
            'MEA_BOOKINGCODE': 0
        }

        # Act
        db_functions.add_measurement(record_name, mea_values, mea_valid)

        # Assert
        mock_insert_query.assert_called_with(Tables.MEASUREMENT, data=expected_dict)

    def test_GIVEN_invalid_dict_WHEN_add_measurement_THEN_error_raised(self):
        # Arrange
        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 'a': 'n'}
        mea_valid = True

        # Act & Assert
        with self.assertRaises(ValueError):
            db_functions.add_measurement(record_name, mea_values, mea_valid)

    def test_WHEN_add_measurement_THEN_relationship_added(self):
        # Arrange
        mock_add_relationship = self.mocks['add_relationship']
        mock_obj_id = self.mocks['get_object_id']
        mock_datetime = self.mocks['datetime']

        mock_obj_id.return_value = 0
        mock_datetime.now.return_value = datetime(1, 2, 3, 4, 5, 6)

        expected_obj = 0
        expected_date = '0001-02-03 04:05:06'

        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}
        mea_valid = True

        # Act
        db_functions.add_measurement(record_name, mea_values, mea_valid)

        # Assert
        mock_add_relationship.assert_called_with(assigned=expected_obj, or_date=expected_date)

    def test_WHEN_add_measurement_THEN_logger_called_correctly(self):
        # Arrange
        mock_logger = self.mocks['db_logger']
        mock_obj_id = self.mocks['get_object_id']
        mock_last_id = self.mocks['_get_table_last_id']
        mock_obj_id.return_value = 0
        mock_last_id.return_value = 1

        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}
        mea_valid = True

        exp_last_id = 1
        exp_obj_id = 0
        exp_record_name = 'record_name'
        exp_mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}

        # Act
        db_functions.add_measurement(record_name, mea_values, mea_valid)

        # Assert
        mock_logger.log_new_measurement.assert_called_with(record_no=exp_last_id, obj_id=exp_obj_id,
                                                           obj_name=exp_record_name, values=exp_mea_values,
                                                           print_msg=True)


class TestImportObjectDBSetup(unittest.TestCase):

    def setUp(self):
        patcher = patch.multiple('HLM_PV_Import.db_functions', _select_query=DEFAULT, _insert_query=DEFAULT,
                                 _get_table_last_id=DEFAULT)
        self.addCleanup(patcher.stop)
        self.mocks = patcher.start()

    def test_GIVEN_no_function_WHEN_create_db_pv_import_function_if_not_exist_THEN_correct_insert_query(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']

        mock_select.return_value = None
        expected_dict = {'OF_NAME': DB_OBJ_NAME, 'OF_COMMENT': 'HLM PV IMPORT'}

        # Act
        db_functions._create_pv_import_function_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.FUNCTION, data=expected_dict)

    def test_GIVEN_function_exists_WHEN_create_db_pv_import_function_if_not_exist_THEN_no_insert_query(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_function_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    def test_GIVEN_no_class_WHEN_create_db_pv_import_class_if_not_exist_THEN_correct_insert_query(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']
        mock_last_id = self.mocks['_get_table_last_id']

        # Assign an iterable to side_effect - the mock will return the next value in the sequence each time it is called
        mock_select.side_effect = [None, 42]
        mock_last_id.return_value = 10

        expected_insert = {
            'OC_ID': 11,
            'OC_FUNCTION_ID': 42,
            'OC_NAME': DB_OBJ_NAME,
            'OC_POSITIONTYPE': 0,
            'OC_COMMENT': 'HLM PV IMPORT',
        }

        # Act
        db_functions._create_pv_import_class_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT_CLASS, data=expected_insert)

    def test_GIVEN_class_exists_WHEN_create_db_pv_import_class_if_not_exist_THEN_no_insert(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_class_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    def test_GIVEN_no_type_WHEN_create_db_pv_import_type_if_not_exist_THEN_correct_insert_query(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']
        mock_select.side_effect = [None, 42]

        expected_insert = {
            'OT_OBJECTCLASS_ID': 42,
            'OT_NAME': DB_OBJ_NAME,
            'OT_COMMENT': 'HLM PV IMPORT',
            'OT_OUTOFOPERATION': 0
        }

        # Act
        db_functions._create_pv_import_type_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT_TYPE, data=expected_insert)

    def test_GIVEN_type_exists_WHEN_create_db_pv_import_type_if_not_exist_THEN_no_insert(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_type_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    def test_GIVEN_no_object_WHEN_create_db_pv_import_object_if_not_exist_THEN_correct_insert_query(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']
        mock_select.side_effect = [None, 42]

        expected_insert = {
            'OB_OBJECTTYPE_ID': 42,
            'OB_NAME': DB_OBJ_NAME,
            'OB_COMMENT': 'HLM PV IMPORT',
        }

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT, data=expected_insert)

    def test_GIVEN_object_exists_WHEN_create_db_pv_import_object_if_not_exist_THEN_no_insert(self):
        # Arrange
        mock_select = self.mocks['_select_query']
        mock_insert = self.mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    @patch.multiple('HLM_PV_Import.db_functions',
                    _create_pv_import_function_if_not_exist=DEFAULT,
                    _create_pv_import_class_if_not_exist=DEFAULT,
                    _create_pv_import_type_if_not_exist=DEFAULT,
                    _create_pv_import_object_if_not_exist=DEFAULT)
    def test_WHEN_setup_db_pv_import_THEN_functions_called(self, **mocks):
        # Arrange
        mock_create_function = mocks['_create_pv_import_function_if_not_exist']
        mock_create_class = mocks['_create_pv_import_class_if_not_exist']
        mock_create_type = mocks['_create_pv_import_type_if_not_exist']
        mock_create_object = mocks['_create_pv_import_object_if_not_exist']

        # Act
        db_functions.setup_db_pv_import()

        # Assert
        mock_create_function.assert_called()
        mock_create_class.assert_called()
        mock_create_type.assert_called()
        mock_create_object.assert_called()
