import unittest

from mock import patch
from hlm_pv_import import ca_wrapper
from hlm_pv_import.ca_wrapper import PvMonitors
from parameterized import parameterized
from caproto.threading import client


class TestWrapper(unittest.TestCase):

    @parameterized.expand([
        ({'1': True, '2': True, '3': False, '4': False, '5': True}, ['1', '2', '5']),
        ({'1': True, '2': True, '3': True, '4': True, '5': True}, ['1', '2', '3', '4', '5']),
        ({'1': False, '2': False, '3': False, '4': False, '5': False}, []),
        ({'1': True}, ['1']), ({'1': False}, [])
    ])
    @patch('hlm_pv_import.ca_wrapper.Context')
    def test_WHEN_get_connected_pvs_THEN_return_correct_list(self, pvs_param, expected, mock_ctx):
        # Arrange
        class TestPV:
            def __init__(self, name_, connected_):
                self.name = name_
                self.connected = connected_
        pvs = []
        for name, connected in pvs_param.items():
            pvs.append(TestPV(name_=name, connected_=connected))

        mock_ctx.return_value.get_pvs.return_value = pvs

        # Act
        result = ca_wrapper.get_connected_pvs(pv_list=[], timeout=0)

        # Assert
        self.assertEqual(expected, result)


class TestPvMonitors(unittest.TestCase):

    def setUp(self):
        patcher = patch('hlm_pv_import.ca_wrapper.Context')
        self.mock_ctx = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.pvm = PvMonitors([])
        self.dummy_data = {'PV_name_1': 123, 'PV_name_2': 117.4, 'PV_name_3': 'High', 'PV_name_4': None}

    def test_GIVEN_pv_list_WHEN_start_monitors_THEN_get_pvs(self):
        # Arrange
        self.pvm.pv_name_list = ['a', 'b', 'c']

        # Act
        self.pvm.start_monitors()

        # Assert
        self.mock_ctx.get_pvs.assert_called_with('a', 'b', 'c')

    @patch.object(client, 'PV')
    def test_WHEN_start_monitors_THEN_subscribe_to_pvs(self, mock_pv):
        # Arrange
        mock_sub = mock_pv.subscribe
        self.mock_ctx.get_pvs.return_value = [mock_pv]

        # Act
        self.pvm.start_monitors()

        # Assert
        mock_sub.assert_called()

    @parameterized.expand([
        (1, 2, True),
        (1, 3, True),
        (2, 1, False),
        (1, 1, False)
    ])
    def test_GIVEN_pv_name_WHEN_check_if_data_is_stale_THEN_correct_check(self, last_update, current_time, expected):
        with patch('time.time') as mock_time, patch('hlm_pv_import.ca_wrapper.pv_logger'):

            # Arrange
            ca_wrapper.STALE_AGE = 1  # set 1 second old as stale data
            self.pvm._pv_last_update['pv_name'] = last_update
            mock_time.return_value = current_time

            # Act
            result = self.pvm.pv_data_is_stale('pv_name')

            # Assert
            self.assertEqual(expected, result)

    def test_WHEN_default_callback_THEN_store_data(self):
        with patch('caproto.threading.client.Subscription') as mock_sub, \
             patch('caproto._commands.EventAddResponse') as mock_resp:
            # Arrange
            mock_sub.pv.name = 'pv_name'
            mock_resp.data = [1]
            expected_data = {'pv_name': 1}

            # Act
            self.pvm._callback_f(mock_sub, mock_resp)

            # Assert
            self.assertDictEqual(expected_data, self.pvm._pv_data)

    def test_WHEN_default_callback_THEN_store_update_time(self):
        with patch('caproto.threading.client.Subscription') as mock_sub, \
             patch('caproto._commands.EventAddResponse') as mock_resp, \
             patch('time.time') as mock_time:
            # Arrange
            mock_time.return_value = 123
            mock_sub.pv.name = 'pv_name'
            expected_update = {'pv_name': 123}

            # Act
            self.pvm._callback_f(mock_sub, mock_resp)

            # Assert
            self.assertDictEqual(expected_update, self.pvm._pv_last_update)
