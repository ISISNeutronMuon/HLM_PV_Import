from __future__ import absolute_import

import functools
import unittest
from decimal import Decimal

from mock import patch, call, DEFAULT, ANY
import db_functions
from constants import Tables, PV_IMPORT, HEDB
from datetime import datetime


def patch_measurement(f):
    """
    For testing add_measurement.
    """

    @patch.multiple('db_functions', datetime=DEFAULT, db_logger=DEFAULT, _get_table_last_id=DEFAULT,
                    add_relationship=DEFAULT, _insert_query=DEFAULT, _get_object_class=DEFAULT,
                    _get_object_type=DEFAULT, get_object_id=DEFAULT, log_error=DEFAULT, log_db_error=DEFAULT)
    @functools.wraps(f)
    def functor(*args, **kwargs):
        return f(*args, **kwargs)

    return functor


class TestDbFunctions(unittest.TestCase):

    @patch('db_functions._select_query')
    def test_GIVEN_valid_column_WHEN_get_pv_records_THEN_get_records_column(self, mock_select_query):
        db_functions.get_pv_records('pvname')
        mock_select_query.assert_called_with(table='pvs', columns='pvname',
                                             filters="WHERE pvname LIKE '%HLM%'", db='iocdb')

    @patch('db_functions._select_query')
    def test_GIVEN_valid_columns_WHEN_get_pv_records_THEN_get_records_columns(self, mock_select_query):
        db_functions.get_pv_records('pvname', 'record_type')
        mock_select_query.assert_called_with(table='pvs', columns='pvname,record_type',
                                             filters="WHERE pvname LIKE '%HLM%'", db='iocdb')

    @patch('db_functions._select_query')
    def test_GIVEN_mixed_columns_WHEN_get_pv_records_THEN_get_only_valid_columns(self, mock_select_query):
        db_functions.get_pv_records('pvname', 'nonexisting_column', 'record_type')
        mock_select_query.assert_called_with(table='pvs', columns='pvname,record_type',
                                             filters="WHERE pvname LIKE '%HLM%'", db='iocdb')

    @patch('db_functions._select_query')
    def test_GIVEN_no_columns_WHEN_get_pv_records_THEN_get_all_columns(self, mock_select_query):
        db_functions.get_pv_records()
        mock_select_query.assert_called_with(table='pvs', columns='*',
                                             filters="WHERE pvname LIKE '%HLM%'", db='iocdb')

    @patch('db_functions._select_query')
    def test_GIVEN_invalid_columns_WHEN_get_pv_records_THEN_get_all_columns(self, mock_select_query):
        db_functions.get_pv_records('wrong', 'wrong2')
        mock_select_query.assert_called_with(table='pvs', columns='*',
                                             filters="WHERE pvname LIKE '%HLM%'", db='iocdb')

    @patch('db_functions._select_query')
    def test_GIVEN_object_name_WHEN_get_object_id_THEN_correct_search_query(self, mock_select_query):
        db_functions.get_object_id('obj_name')
        search = f"WHERE `OB_NAME` LIKE 'obj_name'"
        mock_select_query.assert_called_with(table=Tables.OBJECT, columns='OB_ID',
                                             filters=search, to_str=True)

    @patch_measurement
    def test_GIVEN_valid_values_WHEN_add_measurement_THEN_correct_insert_query(self, **mocks):
        # Arrange
        mock_obj_id = mocks['get_object_id']
        mock_obj_type = mocks['_get_object_type']
        mock_obj_class = mocks['_get_object_class']
        mock_datetime = mocks['datetime']
        mock_insert_query = mocks['_insert_query']

        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e'}
        mea_valid = True

        mock_obj_id.return_value = 0
        mock_datetime.now.return_value = datetime(1, 2, 3, 4, 5, 6)
        mock_obj_type.return_value = 'obj_type_name'
        mock_obj_class.return_value = 'obj_class_name'

        expected_comment = f'"record_name" (obj_type_name - obj_class_name) via {PV_IMPORT}'
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

    @patch_measurement  # mock functions even if unused in case it works
    def test_GIVEN_invalid_dict_WHEN_add_measurement_THEN_error_raised(self, **mocks):
        # Arrange
        record_name = 'record_name'
        mea_values = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 'a': 'n'}
        mea_valid = True

        # Act & Assert
        with self.assertRaises(ValueError):
            db_functions.add_measurement(record_name, mea_values, mea_valid)

    @patch_measurement
    def test_WHEN_add_measurement_THEN_relationship_added(self, **mocks):
        # Arrange
        mock_add_relationship = mocks['add_relationship']
        mock_obj_id = mocks['get_object_id']
        mock_datetime = mocks['datetime']

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

    @patch_measurement
    def test_WHEN_add_measurement_THEN_logger_called_correctly(self, **mocks):
        # Arrange
        mock_logger = mocks['db_logger']
        mock_obj_id = mocks['get_object_id']
        mock_last_id = mocks['_get_table_last_id']
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

    @patch.multiple('db_functions', _get_pv_import_object_id=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_date_WHEN_add_relationship_THEN_call_correct_insert_query(self, **mocks):
        # Assert
        mock_get_import_id = mocks['_get_pv_import_object_id']
        mock_insert = mocks['_insert_query']
        mock_get_import_id.return_value = 42

        assigned_obj = 1
        or_date = 'date'

        expected_dict = {
            'OR_PRIMARY': 0,
            'OR_OBJECT_ID': 42,
            'OR_OBJECT_ID_ASSIGNED': 1,
            'OR_DATE_ASSIGNMENT': 'date',
            'OR_DATE_REMOVAL': 'date',
            'OR_OUTFLOW': None,
            'OR_BOOKINGREQUEST': None
        }

        # Act
        db_functions.add_relationship(assigned_obj, or_date)

        # Assert
        mock_insert.assert_called_with(Tables.OBJECT_RELATION, expected_dict)

    @patch.multiple('db_functions', _get_pv_import_object_id=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_no_date_WHEN_add_relationship_THEN_call_correct_insert_query(self, **mocks):
        # Assert
        mock_get_import_id = mocks['_get_pv_import_object_id']
        mock_insert = mocks['_insert_query']
        mock_get_import_id.return_value = 42

        assigned_obj = 1

        expected_dict = {
            'OR_PRIMARY': 0,
            'OR_OBJECT_ID': 42,
            'OR_OBJECT_ID_ASSIGNED': 1,
            'OR_DATE_ASSIGNMENT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'OR_DATE_REMOVAL': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'OR_OUTFLOW': None,
            'OR_BOOKINGREQUEST': None
        }

        # Act
        db_functions.add_relationship(assigned_obj)

        # Assert
        mock_insert.assert_called_with(Tables.OBJECT_RELATION, expected_dict)

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_no_function_WHEN_create_db_pv_import_function_if_not_exist_THEN_correct_insert_query(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']

        mock_select.return_value = None
        expected_dict = {'OF_NAME': PV_IMPORT, 'OF_COMMENT': 'HLM PV IMPORT'}

        # Act
        db_functions._create_pv_import_function_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.FUNCTION, data=expected_dict)

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_function_exists_WHEN_create_db_pv_import_function_if_not_exist_THEN_no_insert_query(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_function_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT, _get_table_last_id=DEFAULT)
    def test_GIVEN_no_class_WHEN_create_db_pv_import_class_if_not_exist_THEN_correct_insert_query(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']
        mock_last_id = mocks['_get_table_last_id']

        # Assign an iterable to side_effect - the mock will return the next value in the sequence each time it is called
        mock_select.side_effect = [None, 42]
        mock_last_id.return_value = 10

        expected_insert = {
            'OC_ID': 11,
            'OC_FUNCTION_ID': 42,
            'OC_NAME': PV_IMPORT,
            'OC_POSITIONTYPE': 0,
            'OC_COMMENT': 'HLM PV IMPORT',
        }

        # Act
        db_functions._create_pv_import_class_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT_CLASS, data=expected_insert)

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT, _get_table_last_id=DEFAULT)
    def test_GIVEN_class_exists_WHEN_create_db_pv_import_class_if_not_exist_THEN_no_insert(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_class_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_no_type_WHEN_create_db_pv_import_type_if_not_exist_THEN_correct_insert_query(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']
        mock_select.side_effect = [None, 42]

        expected_insert = {
            'OT_OBJECTCLASS_ID': 42,
            'OT_NAME': PV_IMPORT,
            'OT_COMMENT': 'HLM PV IMPORT',
            'OT_OUTOFOPERATION': 0
        }

        # Act
        db_functions._create_pv_import_type_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT_TYPE, data=expected_insert)

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_type_exists_WHEN_create_db_pv_import_type_if_not_exist_THEN_no_insert(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_type_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_no_object_WHEN_create_db_pv_import_object_if_not_exist_THEN_correct_insert_query(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']
        mock_select.side_effect = [None, 42]

        expected_insert = {
            'OB_OBJECTTYPE_ID': 42,
            'OB_NAME': PV_IMPORT,
            'OB_COMMENT': 'HLM PV IMPORT',
        }

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_called_with(table=Tables.OBJECT, data=expected_insert)

    @patch.multiple('db_functions', _select_query=DEFAULT, _insert_query=DEFAULT)
    def test_GIVEN_object_exists_WHEN_create_db_pv_import_object_if_not_exist_THEN_no_insert(self, **mocks):
        # Arrange
        mock_select = mocks['_select_query']
        mock_insert = mocks['_insert_query']

        mock_select.return_value = True

        # Act
        db_functions._create_pv_import_object_if_not_exist()

        # Assert
        mock_insert.assert_not_called()

    @patch.multiple('db_functions',
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

    @patch('db_functions._select_query')
    def test_GIVEN_object_id_WHEN_get_object_type_THEN_correct_type_row_returned(self, mock_select):
        # Arrange
        object_type = [(1, 2, 'Coordinator default', 3, None, None, None)]
        mock_select.side_effect = [123, object_type]

        expected = object_type

        # Act
        result = db_functions._get_object_type(1)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_TYPE, columns='*',
                                       filters=f'WHERE OT_ID LIKE {123}')
        self.assertEqual(expected, result)

    @patch('db_functions._select_query')
    def test_GIVEN_object_id_name_only_WHEN_get_object_type_THEN_correct_query_and_name_returned(self, mock_select):
        # Arrange
        object_type = ['Coordinator default']
        mock_select.side_effect = [123, object_type]

        expected = 'Coordinator default'

        # Act
        result = db_functions._get_object_type(1, name_only=True)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_TYPE, columns='OT_NAME',
                                       filters=f'WHERE OT_ID LIKE {123}')
        self.assertEqual(expected, result)

    @patch.multiple('db_functions', _get_object_type=DEFAULT, _select_query=DEFAULT)
    def test_GIVEN_object_id_WHEN_get_object_class_THEN_correct_class_row_returned(self, **mocks):
        # Arrange
        mock_get_type = mocks['_get_object_type']
        mock_select = mocks['_select_query']

        mock_get_type.return_value = [(1, 123, 'Coordinator default', 3, None, None, None)]
        mock_select.return_value = [(1, 1, 'Coordinator', Decimal('1'), '', None, None, None)]

        expected = mock_select()

        # Act
        result = db_functions._get_object_class(1)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_CLASS, columns='*',
                                       filters=f'WHERE OC_ID LIKE {123}')
        self.assertEqual(expected, result)

    @patch.multiple('db_functions', _get_object_type=DEFAULT, _select_query=DEFAULT)
    def test_GIVEN_object_id_name_only_WHEN_get_object_class_THEN_correct_query_and_name_returned(self, **mocks):
        # Arrange
        mock_get_type = mocks['_get_object_type']
        mock_select = mocks['_select_query']

        mock_get_type.return_value = [(1, 123, 'Coordinator default', 3, None, None, None)]
        mock_select.return_value = ['Coordinator default']

        expected = 'Coordinator default'

        # Act
        result = db_functions._get_object_class(1, name_only=True)

        # Assert
        mock_select.assert_called_with(table=Tables.OBJECT_CLASS, columns='OC_NAME',
                                       filters=f'WHERE OC_ID LIKE {123}')
        self.assertEqual(expected, result)

    @patch('db_functions._select_query')
    def test_GIVEN_object_id_WHEN_get_object_name_THEN_correct_select_query_called(self, mock_select):
        obj_id = 123
        db_functions._get_object_name(obj_id)
        mock_select.assert_called_with(
            table=Tables.OBJECT,
            columns='OB_NAME',
            filters=f'WHERE OB_ID LIKE {obj_id}',
            to_str=True
        )

    @patch.multiple('db_functions', _select_query=DEFAULT, _get_primary_key_column=DEFAULT)
    def test_GIVEN_table_name_WHEN_get_table_last_row_id_THEN_correct_select_query_called(self, **mocks):
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
            db=HEDB.NAME,
            to_str=True
        )

    @patch('db_functions._select_query')
    def test_GIVEN_table_name_WHEN_get_table_last_row_id_THEN_correct_select_query_called(self, mock_select):
        # Arrange
        table = 'table_name'

        # Act
        db_functions._get_primary_key_column(table)

        # Assert
        mock_select.assert_called_with(
            table='information_schema.KEY_COLUMN_USAGE',
            columns='COLUMN_NAME',
            filters=f"WHERE TABLE_NAME = '{table}'AND CONSTRAINT_NAME = 'PRIMARY'",
            db=HEDB.NAME,
            to_str=True
        )

