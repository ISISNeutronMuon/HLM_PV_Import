from __future__ import absolute_import
import unittest

from mock import patch
from user_config import *


class TestUserConfig(unittest.TestCase):

    def setUp(self):
        patcher = patch.object(ValidateUserConfig, "__init__", lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_GIVEN_unique_records_WHEN_check_if_records_unique_THEN_no_error(self):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', 'c']
        validator.check_config_records_unique()

    def test_GIVEN_duplicate_records_WHEN_check_if_records_unique_THEN_error_raised(self):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', 'b']
        with self.assertRaises(ValueError):
            validator.check_config_records_unique()

    def test_GIVEN_no_empty_record_WHEN_check_if_records_tag_empty_THEN_no_error(self):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', 'c']
        validator.check_config_records_tag_not_empty()

    def test_GIVEN_empty_record_WHEN_check_if_records_tag_empty_THEN_error_raised(self):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', None]
        with self.assertRaises(ValueError):
            validator.check_config_records_tag_not_empty()

    @patch('db_functions._select_query')
    def test_GIVEN_records_exist_WHEN_check_if_records_exist_THEN_no_error(self, mock_query_res):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', 'c']
        mock_query_res.return_value = 1
        validator.check_config_records_exist()

    @patch('db_functions._select_query')
    def test_GIVEN_nonexistent_records_WHEN_check_if_records_exist_THEN_error_raised(self, mock_query_res):
        validator = ValidateUserConfig()
        validator.records = ['a', 'b', 'c']
        mock_query_res.return_value = None
        with self.assertRaises(ValueError):
            validator.check_config_records_exist()

    @patch('user_config.ValidateUserConfig._get_measurement_pvs')
    def test_GIVEN_existing_pvs_WHEN_check_if_measurement_pvs_exist_THEN_no_error(self, mock_meas_pvs):
        validator = ValidateUserConfig()
        validator.available_pvs = ['a', 'b', 'c']
        mock_meas_pvs.return_value = ['a', 'b', 'c']
        validator.check_measurement_pvs_exist()

    @patch('user_config.ValidateUserConfig._get_measurement_pvs')
    def test_GIVEN_nonexistent_pvs_WHEN_check_if_measurement_pvs_exist_THEN_error_raised(self, mock_meas_pvs):
        validator = ValidateUserConfig()
        validator.available_pvs = ['a', 'b', 'c']
        mock_meas_pvs.return_value = ['a', 'b', 'c', 'd', 'e']
        with self.assertRaises(ValueError):
            validator.check_measurement_pvs_exist()

    def test_GIVEN_entries_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        validator = ValidateUserConfig()
        validator.configs = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two', 'three_one']

        # Act
        result = validator._get_measurement_pvs()

        # Assert
        # unittest.TestCase.assertCountEqual:
        # a and b have the same elements in the same number, regardless of their order
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entry_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        validator = ValidateUserConfig()
        validator.configs = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
            ]
        }
        expected_value = ['one_one']

        # Act
        result = validator._get_measurement_pvs(no_duplicates=True)

        # Assert
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entries_WHEN_get_measurement_pvs_with_duplicates_THEN_pvs_returned(self):
        # Arrange
        validator = ValidateUserConfig()
        validator.configs = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two', 'three_one', 'one_one']

        # Act
        result = validator._get_measurement_pvs(no_duplicates=False)

        # Assert
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entries_with_empty_measurements_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        validator = ValidateUserConfig()
        validator.configs = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': None}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two']

        # Act
        result = validator._get_measurement_pvs()

        # Assert
        self.assertCountEqual(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_multiple_records_WHEN_get_all_config_records_THEN_records_returned(self, mock_to_dict):
        # Arrange
        config = {
            'configuration': {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': 'pv_name'}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': 'pv_name'}}
                ]}
        }
        expected_value = ['record_one', 'record_two']
        mock_to_dict.return_value = config

        # Act
        result = get_all_config_records()

        # Assert
        self.assertEquals(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_single_record_WHEN_get_all_config_records_THEN_records_returned(self, mock_xml_to_dict):
        # Arrange
        config = {'configuration': {'entry': {'record_name': 'record_one', 'measurements': {'pv_name': 'pv_name'}}}}
        expected_value = ['record_one']
        mock_xml_to_dict.return_value = config

        # Act
        result = get_all_config_records()

        # Assert
        self.assertEquals(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_pv_in_single_record_WHEN_get_pv_config_THEN_pv_config_returned(self, mock_xml_to_dict):
        # Arrange
        config = {
            'configuration': {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two', 'one_one']}},
                    {'record_name': 'record_three', 'measurements': {'pv_name': ['one_one', 'two_one', 'three_one']}},
                    {'record_name': 'record_four', 'measurements': {'pv_name': ['two_one', 'three_one', 'unique']}}
                ]}
        }
        pv_name = 'unique'
        expected_value = {'record_name': 'record_four', 'measurements': {'pv_name': ['two_one', 'three_one', 'unique']}}
        mock_xml_to_dict.return_value = config

        # Act
        result = get_pv_config(pv_name=pv_name)

        # Assert
        self.assertEquals(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_pv_in_multiple_records_WHEN_get_pv_config_THEN_pv_configs_returned(self, mock_xml_to_dict):
        # Arrange
        config = {
            'configuration': {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two', 'one_one']}},
                    {'record_name': 'record_three', 'measurements': {'pv_name': ['one_one', 'two_one', 'three_one']}},
                    {'record_name': 'record_four', 'measurements': {'pv_name': ['two_one', 'three_one']}}
                ]}
        }
        pv_name = 'one_one'
        expected_value = [
            {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
            {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two', 'one_one']}},
            {'record_name': 'record_three', 'measurements': {'pv_name': ['one_one', 'two_one', 'three_one']}},
        ]
        mock_xml_to_dict.return_value = config

        # Act
        result = get_pv_config(pv_name=pv_name)

        # Assert
        self.assertEquals(result, expected_value)
