from parameterized import parameterized
import unittest
from mock import patch
from HLM_PV_Import.user_config import *
from HLM_PV_Import.settings import PVConfig


class TestUserConfig(unittest.TestCase):

    def setUp(self):
        patcher = patch.object(UserConfig, "__init__", lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.config = UserConfig()

    def test_GIVEN_unique_ids_WHEN_check_if_object_ids_unique_THEN_no_exception(self):
        self.config.object_ids = ['a', 'b', 'c']
        self.config._check_no_duplicate_object_ids()

    def test_GIVEN_duplicate_ids_WHEN_check_if_object_ids_unique_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.object_ids = ['a', 'b', 'b']
            with self.assertRaises(PVConfigurationException):
                self.config._check_no_duplicate_object_ids()

    def test_GIVEN_id_WHEN_check_if_entry_has_object_id_THEN_no_exception(self):
        self.config.object_ids = ['a', 'b', 'c']
        self.config._check_entries_have_object_ids()

    def test_GIVEN_no_id_WHEN_check_if_entry_has_object_id_THEN_exception_raised(self):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.object_ids = ['a', 'b', None]
            with self.assertRaises(PVConfigurationException):
                self.config._check_entries_have_object_ids()

    @parameterized.expand([
        ([{PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}}],),
        ([
            {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c'}},
            {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'd', '2': 'a'}}
        ], )
    ])
    def test_GIVEN_pvs_WHEN_check_if_entries_have_measurement_pvs_THEN_no_exception(self, entries):
        self.config.entries = entries
        self.config.object_ids = [entry[PVConfig.OBJ] for entry in self.config.entries]
        self.config._check_entries_have_measurement_pvs()

    @parameterized.expand([
        ([{PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': None}}],),
        ([{PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {}}],),
        ([{PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40}],),
        ([{PVConfig.OBJ: 3}],)
    ])
    def test_GIVEN_no_pvs_WHEN_check_if_entries_have_measurement_pvs_THEN_exception_raised(self, entries):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.entries = entries
            self.config.object_ids = [entry[PVConfig.OBJ] for entry in self.config.entries]
            with self.assertRaises(PVConfigurationException):
                self.config._check_entries_have_measurement_pvs()

    @patch('HLM_PV_Import.user_config.get_object')
    def test_GIVEN_objects_exist_WHEN_check_if_objects_exist_THEN_no_exception(self, mock_obj_res):
        self.config.object_ids = ['a', 'b', 'c']
        mock_obj_res.return_value = 1
        self.config._check_objects_exist()

    @patch('HLM_PV_Import.user_config.get_object')
    def test_GIVEN_objects_not_found_WHEN_check_if_objects_exist_THEN_exception_raised(self, mock_obj_res):
        with patch('HLM_PV_Import.user_config.logger'):
            self.config.object_ids = ['a', 'b', 'c']
            mock_obj_res.return_value = None
            with self.assertRaises(PVConfigurationException):
                self.config._check_objects_exist()

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
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}}
            ],
            ['a'], True
        ),
        (
            [
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}},
                {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'a', '2': 'b', '3': None}}
            ],
            ['a', 'b', 'c'], True
        ),
        (
            [
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}},
                {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'a', '2': 'b', '3': 'd'}}
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
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}},
                {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c', '3': 'a'}},
                {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'a', '2': 'b', '3': 'd'}}
            ],
            [1, 2, 3]
        ),
        (
            [
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}}
            ],
            [1]
        )
    ])
    def test_WHEN_get_all_config_entries_THEN_entries_returned(self, entries, expected_value):
        # Arrange
        self.config.entries = entries

        # Act
        result = [entry[PVConfig.OBJ] for entry in self.config.entries]

        # Assert
        self.assertEqual(expected_value, result)

    @parameterized.expand([
        (2, {'1': 'b', '2': 'c'}),
        (1, {'1': 'a'})
    ])
    def test_GIVEN_pvs_WHEN_get_entries_measurement_pvs_THEN_correct_pvs_returned(self, object_id, expected_value):
        # Arrange
        self.config.entries = [
            {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}},
            {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c'}},
            {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'd', '2': 'a'}}
        ]

        # Act
        result = self.config.get_entry_measurement_pvs(object_id)

        # Assert
        self.assertEqual(expected_value, result)

    def test_GIVEN_entries_WHEN_get_logging_periods_THEN_objects_and_their_logging_periods_returned(self):
        # Arrange
        self.config.entries = [
                {PVConfig.OBJ: 1, PVConfig.LOG_PERIOD: 60, PVConfig.MEAS: {'1': 'a'}},
                {PVConfig.OBJ: 2, PVConfig.LOG_PERIOD: 1, PVConfig.MEAS: {'1': 'b', '2': 'c'}},
                {PVConfig.OBJ: 3, PVConfig.LOG_PERIOD: 40, PVConfig.MEAS: {'1': 'd', '2': 'a'}}
        ]
        expected_value = {1: 60, 2: 1, 3: 40}

        # Act
        result = {entry[PVConfig.OBJ]: entry[PVConfig.LOG_PERIOD] for entry in self.config.entries}

        # Assert
        self.assertCountEqual(expected_value, result)

    @parameterized.expand([
        (
            'MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'),
        (
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_PREFIX}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        )
    ])
    def test_GIVEN_pv_name_WHEN_get_full_name_THEN_full_name_is_returned(self, pv_name, expected_name):
        # Act
        result = self.config._get_full_pv_name(pv_name)

        # Assert
        self.assertEqual(expected_name, result)
