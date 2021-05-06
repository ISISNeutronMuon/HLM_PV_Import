from parameterized import parameterized
import unittest
from mock import patch
from HLM_PV_Import.user_config import *
from HLM_PV_Import.settings import PVConfigConst


class TestUserConfig(unittest.TestCase):

    def setUp(self):
        patcher = patch.object(UserConfig, "__init__", lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.config = UserConfig()

    def test_GIVEN_unique_records_WHEN_check_if_records_unique_THEN_no_exception(self):
        self.config.records = ['a', 'b', 'c']
        self.config._check_config_records_unique()

    def test_GIVEN_duplicate_records_WHEN_check_if_records_unique_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.records = ['a', 'b', 'b']
            with self.assertRaises(PVConfigurationException):
                self.config._check_config_records_unique()

    def test_GIVEN_no_empty_record_WHEN_check_if_records_tag_empty_THEN_no_exception(self):
        self.config.records = ['a', 'b', 'c']
        self.config._check_config_records_id_is_not_empty()

    def test_GIVEN_empty_record_WHEN_check_if_records_tag_empty_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.records = ['a', 'b', None]
            with self.assertRaises(PVConfigurationException):
                self.config._check_config_records_id_is_not_empty()

    @parameterized.expand([
        ([{PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}}], ),
        ([
            {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c'}},
            {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'd', '2': 'a'}}
        ], )
    ])
    def test_GIVEN_pvs_WHEN_check_records_has_measurement_pvs_THEN_no_exception(self, entries):
        self.config.entries = entries
        self.config._check_records_have_at_least_one_measurement_pv()

    @parameterized.expand([
        ([{PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': None}}], ),
        ([{PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {}}], ),
        ([{PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40}], ),
        ([{PVConfigConst.OBJ: 3}], )
    ])
    def test_GIVEN_no_pvs_WHEN_check_if_records_have_measurement_pvs_THEN_exception_raised(self, entries):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.entries = entries
            with self.assertRaises(PVConfigurationException):
                self.config._check_records_have_at_least_one_measurement_pv()

    @patch('HLM_PV_Import.db_functions._select')
    def test_GIVEN_records_exist_WHEN_check_if_records_exist_THEN_no_exception(self, mock_query_res):
        self.config.records = ['a', 'b', 'c']
        mock_query_res.return_value = 1
        self.config._check_config_records_exist()

    @patch('HLM_PV_Import.db_functions._select')
    def test_GIVEN_nonexistent_records_WHEN_check_if_records_exist_THEN_exception_raised(self, mock_query_res):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.records = ['a', 'b', 'c']
            mock_query_res.return_value = None
            with self.assertRaises(PVConfigurationException):
                self.config._check_config_records_exist()

    @patch('HLM_PV_Import.user_config.get_connected_pvs')
    @patch('HLM_PV_Import.user_config.UserConfig.get_measurement_pvs')
    def test_GIVEN_existing_pvs_WHEN_check_if_measurement_pvs_connect_THEN_no_exception(self, mock_meas_pvs,
                                                                                        mock_connected_pvs):
        mock_meas_pvs.return_value = ['a', 'b', 'c']
        mock_connected_pvs.return_value = ['a', 'b', 'c']
        self.config._check_measurement_pvs_connect()

    @parameterized.expand([
        (
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}}
            ],
            ['a'], True
        ),
        (
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
                {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'a', '2': 'b', '3': None}}
            ],
            ['a', 'b', 'c'], True
        ),
        (
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
                {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'a', '2': 'b', '3': 'd'}}
            ],
            ['a', 'b', 'c', 'a', 'a', 'b', 'd'], False
        )
    ])
    def test_WHEN_get_measurement_pvs_THEN_pvs_returned(self, entries, expected_value, duplicates_):
        # Arrange
        self.config.entries = entries

        # Act
        result = self.config.get_measurement_pvs(no_duplicates=duplicates_)

        # Assert
        self.assertCountEqual(expected_value, result)

    @parameterized.expand([
        (
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
                {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'a', '2': 'b', '3': 'd'}}
            ],
            [1, 2, 3]
        ),
        (
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}}
            ],
            [1]
        )
    ])
    def test_WHEN_get_all_config_records_THEN_records_returned(self, entries, expected_value):
        # Arrange
        self.config.entries = entries

        # Act
        result = self.config._get_all_entry_records()

        # Assert
        self.assertEqual(expected_value, result)

    @parameterized.expand([
        (
            'a',
            [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
                {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'a', '2': 'b', '3': 'd'}}
            ]
        ),
        (
            'unique',
            [
                {PVConfigConst.OBJ: 4, PVConfigConst.LOG_PERIOD: 0, PVConfigConst.MEAS: {'1': 'b', '3': 'unique'}}
            ]
        )
    ])
    def test_WHEN_get_pv_records_THEN_records_returned(self, pv_name, expected_value):
        # Arrange
        self.config.entries = [
            {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
            {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
            {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'a', '2': 'b', '3': 'd'}},
            {PVConfigConst.OBJ: 4, PVConfigConst.LOG_PERIOD: 0, PVConfigConst.MEAS: {'1': 'b', '3': 'unique'}}
        ]

        # Act
        result = self.config._get_pv_config(pv_name=pv_name)

        # Assert
        self.assertEqual(expected_value, result)

    @parameterized.expand([
        (2, {'1': 'b', '2': 'c'}),
        (1, {'1': 'a'})
    ])
    def test_GIVEN_record_WHEN_get_record_measurement_pvs_THEN_pvs_returned(self, record_id, expected_value):
        # Arrange
        self.config.entries = [
            {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
            {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c'}},
            {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'd', '2': 'a'}}
        ]

        # Act
        result = self.config.get_record_measurement_pvs(record_id)

        # Assert
        self.assertEqual(expected_value, result)

    def test_GIVEN_entries_WHEN_get_logging_periods_THEN_records_and_periods_returned(self):
        # Arrange
        self.config.entries = [
                {PVConfigConst.OBJ: 1, PVConfigConst.LOG_PERIOD: 60, PVConfigConst.MEAS: {'1': 'a'}},
                {PVConfigConst.OBJ: 2, PVConfigConst.LOG_PERIOD: 1, PVConfigConst.MEAS: {'1': 'b', '2': 'c'}},
                {PVConfigConst.OBJ: 3, PVConfigConst.LOG_PERIOD: 40, PVConfigConst.MEAS: {'1': 'd', '2': 'a'}}
        ]
        expected_value = {1: 60, 2: 1, 3: 40}

        # Act
        result = self.config._get_logging_periods()

        # Assert
        self.assertCountEqual(expected_value, result)
