from __future__ import absolute_import
import unittest

from hamcrest import *
from mock import patch
import ca_wrapper
import pv_functions


class TestPvFunctions(unittest.TestCase):

    def setUp(self):
        self.wrapper = ca_wrapper
        self.pv_func = pv_functions
        self.pv_prefix = pv_functions.PV_PREFIX
        self.pv_domain = pv_functions.PV_DOMAIN

    @patch('db_functions._select_query')
    @patch('db_functions.get_pv_records')
    def test_GIVEN_pv_records_WHEN_get_pv_names_THEN_list_is_returned(self, mock_get_records, mock_select_query):
        expected_value = [
            'TE:NDWXXXX:XX:XXX:123AAA:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123BBB:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123CCC:XXXX:XXXXX'
        ]
        mock_return_records = [
            'TE:NDWXXXX:XX:XXX:123AAA:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123BBB:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123CCC:XXXX:XXXXX',
        ]
        mock_get_records.return_value = mock_return_records
        mock_select_query.return_value = mock_return_records

        result = self.pv_func.get_pv_names()

        assert_that(result, is_(expected_value))

    @patch('db_functions._select_query')
    @patch('ca_wrapper.get_pv_value')              # Mock decorators are applied bottom-up
    @patch('db_functions.get_pv_records')          # and the order of the parameters needs to match this
    def test_GIVEN_pv_records_WHEN_get_pv_names_and_values_THEN_dict_is_returned(self, mock_get_records, mock_get_val,
                                                                                 mock_select_query):
        # Arrange
        expected_value = {
            'TE:NDWXXXX:XX:XXX:123AAA:XXXX:XXXXX': 'OK',
            'TE:NDWXXXX:XX:XXX:123BBB:XXXX:XXXXX': '99.6',
            'TE:NDWXXXX:XX:XXX:123CCC:XXXX:XXXXX': '1165920'
        }

        mock_return_records = [
            'TE:NDWXXXX:XX:XXX:123AAA:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123BBB:XXXX:XXXXX',
            'TE:NDWXXXX:XX:XXX:123CCC:XXXX:XXXXX',
        ]
        mock_get_records.return_value = mock_return_records
        mock_select_query.return_value = mock_return_records

        def mock_responses(responses, default_response=None):
            return lambda _input: responses[_input] if _input in responses else default_response
        mock_get_val.side_effect = mock_responses(
            {
                'TE:NDWXXXX:XX:XXX:123AAA:XXXX:XXXXX': 'OK',
                'TE:NDWXXXX:XX:XXX:123BBB:XXXX:XXXXX': '99.6',
                'TE:NDWXXXX:XX:XXX:123CCC:XXXX:XXXXX': '1165920'
            }
        )

        # Act
        result = self.pv_func.get_pv_names_and_values()

        # Assert
        assert_that(result, is_(expected_value))

    @patch('db_functions._select_query')
    @patch('ca_wrapper.get_pv_value')  # Mock decorators are applied bottom-up
    @patch('db_functions.get_pv_records')
    def test_GIVEN_pv_records_WHEN_get_pv_objects_THEN_correct_objects_returned(self, mock_get_records, mock_get_val,
                                                                                mock_select_query):
        # Arrange
        expected_value = [
            ['name_1', 'val_1', 'type_1', 'desc_1', 'ioc_1'],
            ['name_2', 'val_2', 'type_2', 'desc_2', 'ioc_2'],
            ['name_3', 'val_3', 'type_3', 'desc_3', 'ioc_3'],
        ]

        mock_return_records = [
            ('name_1', 'type_1', 'desc_1', 'ioc_1'),
            ('name_2', 'type_2', 'desc_2', 'ioc_2'),
            ('name_3', 'type_3', 'desc_3', 'ioc_3'),
        ]
        mock_get_records.return_value = mock_return_records
        mock_select_query.return_value = mock_return_records

        def mock_responses(responses, default_response=None):
            return lambda _input: responses[_input] if _input in responses else default_response
        mock_get_val.side_effect = mock_responses(
            {
                'name_1': 'val_1',
                'name_2': 'val_2',
                'name_3': 'val_3'
            }
        )

        # Act
        result = self.pv_func.get_pv_objects()

        # Assert
        result_list = []  # move object values to a list of lists to compare with expected values
        for pv in result:
            result_list.append([pv.name, pv.value, pv.record_type, pv.desc, pv.ioc_name])

        assert_that(result_list, is_(expected_value))
