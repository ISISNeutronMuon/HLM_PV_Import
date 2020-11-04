
import unittest
from mock import patch
from HLM_PV_Import.user_config import *


class TestUserConfig(unittest.TestCase):

    def setUp(self):
        patcher = patch.object(UserConfig, "__init__", lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_GIVEN_unique_records_WHEN_check_if_records_unique_THEN_no_exception(self):
        config = UserConfig()
        config.records = ['a', 'b', 'c']
        config._check_config_records_unique()

    def test_GIVEN_duplicate_records_WHEN_check_if_records_unique_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.records = ['a', 'b', 'b']
            with self.assertRaises(UserConfigurationException):
                config._check_config_records_unique()

    def test_GIVEN_no_empty_record_WHEN_check_if_records_tag_empty_THEN_no_exception(self):
        config = UserConfig()
        config.records = ['a', 'b', 'c']
        config._check_config_records_tag_not_empty()

    def test_GIVEN_empty_record_WHEN_check_if_records_tag_empty_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.records = ['a', 'b', None]
            with self.assertRaises(UserConfigurationException):
                config._check_config_records_tag_not_empty()

    def test_GIVEN_records_with_pvs_WHEN_check_if_records_have_measurement_pvs_THEN_no_exception(self):
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        config._check_records_have_at_least_one_measurement_pv()

    def test_GIVEN_record_with_no_pvs_WHEN_check_if_records_have_measurement_pvs_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.entries = {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': None}},
                    {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
                ]
            }
            with self.assertRaises(UserConfigurationException):
                config._check_records_have_at_least_one_measurement_pv()

    def test_GIVEN_records_with_no_pvs_WHEN_check_if_records_have_measurement_pvs_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.entries = {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': None}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': None}},
                    {'record_name': 'record_three', 'measurements': {'pv_name': None}}
                ]
            }
            with self.assertRaises(UserConfigurationException):
                config._check_records_have_at_least_one_measurement_pv()

    @patch('HLM_PV_Import.db_functions._select_query')
    def test_GIVEN_records_exist_WHEN_check_if_records_exist_THEN_no_exception(self, mock_query_res):
        config = UserConfig()
        config.records = ['a', 'b', 'c']
        mock_query_res.return_value = 1
        config._check_config_records_exist()

    @patch('HLM_PV_Import.db_functions._select_query')
    def test_GIVEN_nonexistent_records_WHEN_check_if_records_exist_THEN_exception_raised(self, mock_query_res):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.records = ['a', 'b', 'c']
            mock_query_res.return_value = None
            with self.assertRaises(UserConfigurationException):
                config._check_config_records_exist()

    @patch('HLM_PV_Import.user_config.UserConfig.get_measurement_pvs')
    def test_GIVEN_existing_pvs_WHEN_check_if_measurement_pvs_exist_THEN_no_exception(self, mock_meas_pvs):
        config = UserConfig()
        config.available_pvs = ['a', 'b', 'c']
        mock_meas_pvs.return_value = ['a', 'b', 'c']
        config._check_measurement_pvs_exist()

    @patch('HLM_PV_Import.user_config.UserConfig.get_measurement_pvs')
    def test_GIVEN_nonexistent_pvs_WHEN_check_if_measurement_pvs_exist_THEN_exception_raised(self, mock_meas_pvs):
        with patch('HLM_PV_Import.user_config.log_error'):
            config = UserConfig()
            config.available_pvs = ['a', 'b', 'c']
            mock_meas_pvs.return_value = ['a', 'b', 'c', 'd', 'e']
            with self.assertRaises(UserConfigurationException):
                config._check_measurement_pvs_exist()

    def test_GIVEN_entries_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two', 'three_one']

        # Act
        result = config.get_measurement_pvs()

        # Assert
        # unittest.TestCase.assertCountEqual:
        # a and b have the same elements in the same number, regardless of their order
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entry_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
            ]
        }
        expected_value = ['one_one']

        # Act
        result = config.get_measurement_pvs(no_duplicates=True)

        # Assert
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entries_WHEN_get_measurement_pvs_with_duplicates_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two', 'three_one', 'one_one']

        # Act
        result = config.get_measurement_pvs(no_duplicates=False)

        # Assert
        self.assertCountEqual(result, expected_value)

    def test_GIVEN_entries_with_empty_measurements_WHEN_get_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': None}}
            ]
        }
        expected_value = ['one_one', 'two_one', 'two_two']

        # Act
        result = config.get_measurement_pvs()

        # Assert
        self.assertCountEqual(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_multiple_records_WHEN_get_all_config_records_THEN_records_returned(self, mock_to_dict):
        # Arrange
        config = UserConfig()
        config_dict = {
            'configuration': {
                'entry': [
                    {'record_name': 'record_one', 'measurements': {'pv_name': 'pv_name'}},
                    {'record_name': 'record_two', 'measurements': {'pv_name': 'pv_name'}}
                ]}
        }
        expected_value = ['record_one', 'record_two']
        mock_to_dict.return_value = config_dict

        # Act
        result = config._get_all_entry_records()

        # Assert
        self.assertEqual(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_single_record_WHEN_get_all_config_records_THEN_records_returned(self, mock_xml_to_dict):
        # Arrange
        config = UserConfig()
        config_dict = {
            'configuration': {'entry': {'record_name': 'record_one', 'measurements': {'pv_name': 'pv_name'}}}
        }
        expected_value = ['record_one']
        mock_xml_to_dict.return_value = config_dict

        # Act
        result = config._get_all_entry_records()

        # Assert
        self.assertEqual(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_pv_in_single_record_WHEN_get_pv_config_THEN_pv_config_returned(self, mock_xml_to_dict):
        # Arrange
        config = UserConfig()
        config_dict = {
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
        mock_xml_to_dict.return_value = config_dict

        # Act
        result = config._get_pv_config(pv_name=pv_name)

        # Assert
        self.assertEqual(result, expected_value)

    @patch('xmltodict.parse')
    def test_GIVEN_pv_in_multiple_records_WHEN_get_pv_config_THEN_pv_configs_returned(self, mock_xml_to_dict):
        # Arrange
        config = UserConfig()
        config_dict = {
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
        mock_xml_to_dict.return_value = config_dict

        # Act
        result = config._get_pv_config(pv_name=pv_name)

        # Assert
        self.assertEqual(result, expected_value)

    def test_GIVEN_entry_with_single_pv_WHEN_get_record_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        record_name = 'record_one'
        expected_value = ['one_one']

        # Act
        result = config.get_record_measurement_pvs(record_name)

        # Assert
        self.assertEqual(result, expected_value)

    def test_GIVEN_entry_with_multiple_pvs_WHEN_get_record_measurement_pvs_THEN_pvs_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'measurements': {'pv_name': ['three_one', 'one_one']}}
            ]
        }
        record_name = 'record_two'
        expected_value = ['two_one', 'two_two']

        # Act
        result = config.get_record_measurement_pvs(record_name)

        # Assert
        self.assertEqual(result, expected_value)

    def test_GIVEN_entries_WHEN_get_logging_periods_THEN_records_and_periods_returned(self):
        # Arrange
        config = UserConfig()
        config.entries = {
            'entry': [
                {'record_name': 'record_one', 'logging_period': 60, 'measurements': {'pv_name': 'one_one'}},
                {'record_name': 'record_two', 'logging_period': 1, 'measurements': {'pv_name': ['two_one', 'two_two']}},
                {'record_name': 'record_three', 'logging_period': 40, 'measurements': {
                    'pv_name': ['three_one', 'one_one']}}
            ]
        }
        expected_value = {'record_one': 60, 'record_two': 1, 'record_three': 40}

        # Act
        result = config._get_logging_periods()

        # Assert
        self.assertCountEqual(result, expected_value)
