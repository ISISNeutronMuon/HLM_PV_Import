import unittest
from mock import patch, DEFAULT
from parameterized import parameterized
from HLM_PV_Import import db_functions
from HLM_PV_Import.settings import Tables, HEDB
from datetime import datetime


class TestDbFunctions(unittest.TestCase):

    @patch('HLM_PV_Import.db_functions._select')
    def test_GIVEN_object_name_WHEN_get_object_id_THEN_correct_search_query(self, mock_select_query):
        db_functions.get_object_id('obj_name')
        search = f"WHERE `OB_NAME` LIKE %s"
        mock_select_query.assert_called_with(table=Tables.OBJECT, columns='OB_ID',
                                             filters=search, filters_args=('obj_name',), f_elem=True)

    @parameterized.expand([('date', 'end', 'date', 'end'), (None, None, 'current date', None)])
    @patch.multiple('HLM_PV_Import.db_functions', _get_pv_import_object_id=DEFAULT,
                    _insert=DEFAULT, datetime=DEFAULT)
    def test_WHEN_add_relationship_THEN_correct_dates(self, start_date, end_date, exp_s, exp_e, **mocks):
        # Arrange
        mock_get_import_id = mocks['_get_pv_import_object_id']
        mock_insert = mocks['_insert']
        mock_datetime = mocks['datetime']
        mock_datetime.now.return_value.strftime.return_value = 'current date'
        mock_get_import_id.return_value = 42

        assigned_obj = 1

        expected_dict = {
            'OR_PRIMARY': 0,
            'OR_OBJECT_ID': 42,
            'OR_OBJECT_ID_ASSIGNED': 1,
            'OR_DATE_ASSIGNMENT': exp_s,
            'OR_DATE_REMOVAL': exp_e,
            'OR_OUTFLOW': None,
            'OR_BOOKINGREQUEST': None
        }

        # Act
        db_functions.add_relation(assigned=assigned_obj, start_date=start_date, removal_date=end_date)

        # Assert
        mock_insert.assert_called_with(Tables.OBJECT_RELATION, expected_dict)

    @parameterized.expand([
        (False, [(1, 2, 'Coordinator default')], [(1, 2, 'Coordinator default')], '*'),
        (True, ['Coordinator default'], 'Coordinator default', 'OT_NAME')
    ])
    @patch('HLM_PV_Import.db_functions._select')
    def test_GIVEN_object_id_WHEN_get_object_type_THEN_correct_type_row_returned(self, name_only, obj_type, exp_val,
                                                                                 columns, mock_select):
        # Arrange
        mock_select.side_effect = [123, obj_type]

        # Act
        result = db_functions._get_object_type(1, name_only=name_only)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_TYPE, columns=columns,
                                       filters='WHERE OT_ID LIKE %s', filters_args=(123, ))
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        (False, [(1, 1, 'Coordinator')], [(1, 1, 'Coordinator')], '*'),
        (True, ['Coordinator default'], 'Coordinator default', 'OC_NAME')
    ])
    @patch.multiple('HLM_PV_Import.db_functions', _get_object_type=DEFAULT, _select=DEFAULT)
    def test_GIVEN_object_id_WHEN_get_object_class_THEN_correct_class_row_returned(self, name_only, select_val, exp_val,
                                                                                   columns, **mocks):
        # Arrange
        mock_get_type = mocks['_get_object_type']
        mock_select = mocks['_select']

        mock_get_type.return_value = [(1, 123, 'Coordinator default', 3, None, None, None)]
        mock_select.return_value = select_val

        # Act
        result = db_functions._get_object_class(object_id=1, name_only=name_only)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_CLASS, columns=columns,
                                       filters='WHERE OC_ID LIKE %s', filters_args=(123, ))
        self.assertEqual(exp_val, result)

    @patch('HLM_PV_Import.db_functions._select')
    def test_WHEN_get_object_name_THEN_correct_select_query_called(self, mock_select):
        obj_id = 123
        db_functions._get_object_name(obj_id)
        mock_select.assert_called_with(
            table=Tables.OBJECT,
            columns='OB_NAME',
            filters=f'WHERE OB_ID LIKE %s',
            filters_args=(obj_id, ),
            f_elem=True
        )

    @patch.multiple('HLM_PV_Import.db_functions', _select=DEFAULT, _get_primary_key_column=DEFAULT)
    def test_WHEN_get_table_last_row_id_THEN_correct_select_query_called(self, **mocks):
        # Arrange
        mock_select = mocks['_select']
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

    @patch('HLM_PV_Import.db_functions._select')
    def test_WHEN_get_table_primary_key_column_THEN_correct_select_query_called(self, mock_select):
        # Arrange
        table = 'table_name'

        # Act
        db_functions._get_primary_key_column(table)

        # Assert
        mock_select.assert_called_with(
            table='information_schema.KEY_COLUMN_USAGE',
            columns='COLUMN_NAME',
            filters=f"WHERE TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'",
            filters_args=(table, ),
            f_elem=True
        )


class TestSelectAndInsert(unittest.TestCase):

    def setUp(self):
        patcher = patch('HLM_PV_Import.db_functions.connection')
        self.addCleanup(patcher.stop)
        self.mock_connection = patcher.start()

    @parameterized.expand([
        ('tbl_name', 'col1, col2', 'WHERE %s LIKE %s', ('a', 'b'), 'SELECT col1, col2 FROM tbl_name WHERE %s LIKE %s'),
        ('tbl_name', 'col_name', 'WHERE %s LIKE %s', ('a', 'b'), 'SELECT col_name FROM tbl_name WHERE %s LIKE %s'),
        ('tbl_name', None, 'WHERE %s LIKE %s', ('a', 'b'), 'SELECT * FROM tbl_name WHERE %s LIKE %s'),
        ('tbl_name', None, None, None, 'SELECT * FROM tbl_name')
    ])
    def test_GIVEN_args_WHEN_select_query_THEN_correct_query_created(self, table, columns, search, args, expected):
        cursor = self.mock_connection.cursor.return_value

        db_functions._select(table=table, columns=columns, filters=search, filters_args=args)
        cursor.execute.assert_called_with(expected, args)

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
        cursor = self.mock_connection.cursor.return_value

        cursor.fetchall.return_value = records

        result = db_functions._select(table='', f_elem=f_elem)
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
        cursor = self.mock_connection.cursor.return_value
        db_functions._insert('table', data)
        cursor.execute.assert_called_with(exp_query, exp_values)


class TestAddMeasurement(unittest.TestCase):

    def setUp(self):
        patcher = patch.multiple('HLM_PV_Import.db_functions', datetime=DEFAULT, db_logger=DEFAULT,
                                 _get_table_last_id=DEFAULT, add_relationship=DEFAULT, _insert=DEFAULT,
                                 _get_object_class=DEFAULT, _get_object_type=DEFAULT, _get_object_name=DEFAULT,
                                 log_db_error=DEFAULT)
        self.addCleanup(patcher.stop)
        self.mocks = patcher.start()

    def test_WHEN_add_measurement_THEN_logger_called_correctly(self):
        # Arrange
        mock_logger = self.mocks['db_logger']
        mock_obj_name = self.mocks['_get_object_name']
        mock_last_id = self.mocks['_get_table_last_id']
        mock_obj_name.return_value = 'name'
        mock_last_id.return_value = 1

        record_id = 1
        mea_values = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e'}
        mea_valid = True

        exp_last_id = 1
        exp_obj_id = 1
        exp_record_name = 'name'
        exp_mea_values = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e'}

        # Act
        db_functions.add_measurement(record_id, mea_values, mea_valid)

        # Assert
        mock_logger.log_new_measurement.assert_called_with(record_no=exp_last_id, obj_id=exp_obj_id,
                                                           obj_name=exp_record_name, values=exp_mea_values,
                                                           print_msg=True)


class TestImportObjectDBSetup(unittest.TestCase):

    def setUp(self):
        patcher = patch.multiple('HLM_PV_Import.db_functions', _select=DEFAULT, _insert=DEFAULT,
                                 _get_table_last_id=DEFAULT)
        self.addCleanup(patcher.stop)
        self.mocks = patcher.start()

    def test_GIVEN_no_object_WHEN_create_db_pv_import_object_if_not_exist_THEN_correct_insert_statement(self):
        # Arrange
        mock_select = self.mocks['_select']
        mock_insert = self.mocks['_insert']
        mock_select.side_effect = [None, 42]

        expected_insert = {
            'OB_OBJECTTYPE_ID': 42,
            'OB_NAME': HEDB.DB_OBJ_NAME,
            'OB_COMMENT': 'HLM PV IMPORT',
        }

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT, data=expected_insert)

    def test_GIVEN_object_exists_WHEN_create_db_pv_import_object_if_not_exist_THEN_no_insert(self):
        # Arrange
        mock_select = self.mocks['_select']
        mock_insert = self.mocks['_insert']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_not_called()
