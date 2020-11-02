import unittest

from mock import patch
from HLM_PV_Import import ca_wrapper
from HLM_PV_Import.ca_wrapper import PvMonitors
from parameterized import parameterized
from caproto.threading import client


class TestWrapper(unittest.TestCase):

    @parameterized.expand([
        ([b'val'], 'val'),
        (['val'], 'val')
    ])
    @patch('HLM_PV_Import.ca_wrapper.read')
    def test_GIVEN_value_WHEN_get_pv_value_THEN_return_string(self, return_val, exp_val, mock_read):
        mock_read.return_value.data = return_val
        result = ca_wrapper.get_pv_value('')
        self.assertEqual(exp_val, result)


class TestPvMonitors(unittest.TestCase):

    def setUp(self):
        patcher = patch('HLM_PV_Import.ca_wrapper.Context')
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

    @patch.object(client, 'PV')
    def test_WHEN_start_monitors_THEN_add_default_callback_and_store_token(self, mock_pv):
        # Arrange
        mock_sub = mock_pv.subscribe
        mock_add_callback = mock_sub.return_value.add_callback
        self.mock_ctx.get_pvs.return_value = [mock_pv]

        # Act
        self.pvm.start_monitors()

        # Assert
        default_callback = self.pvm._callback_f
        mock_add_callback.assert_called_with(default_callback)

        token_callback = self.pvm.subscriptions[mock_pv.name]['token']
        self.assertEqual(mock_add_callback.return_value, token_callback)

    @patch.object(client, 'PV')
    def test_GIVEN_pv_name_WHEN_clear_callbacks_THEN_clear_pv_subscription(self, mock_pv):
        # Arrange
        self.mock_ctx.get_pvs.return_value = [mock_pv]
        self.pvm.start_monitors()

        # Act
        self.pvm.clear_callbacks(mock_pv.name)

        # Assert
        sub = self.pvm.subscriptions[mock_pv.name]['sub']
        sub.clear.assert_called()

    @patch.object(client, 'PV')
    def test_GIVEN_pv_name_WHEN_remove_pv_THEN_clear_callback_and_remove_from_data(self, mock_pv):
        with patch.object(self.pvm, 'clear_callbacks') as mock_clear_cbs:
            # Arrange
            self.mock_ctx.get_pvs.return_value = [mock_pv]
            self.pvm.start_monitors()
            self.pvm._pv_data = {mock_pv.name: 1}

            # Act
            self.pvm.remove_pv(mock_pv.name)

            # Assert
            mock_clear_cbs.assert_called_with(mock_pv.name)
            self.assertNotIn(mock_pv.name, self.pvm._pv_data)

    @patch.object(client, 'PV')
    def test_GIVEN_only_pv_name_WHEN_add_callback_THEN_default_callback_added(self, mock_pv):
        # Arrange
        sub = mock_pv.subscribe.return_value
        self.pvm.subscriptions[mock_pv.name] = {'sub': sub}

        # Act
        self.pvm.add_callback(mock_pv.name, callback_f=None)

        # Assert
        sub.add_callback.assert_called_with(self.pvm._callback_f)

    @patch.object(client, 'PV')
    def test_GIVEN_pv_name_and_callback_f_WHEN_add_callback_THEN_given_callback_added(self, mock_pv):
        # Arrange
        sub = mock_pv.subscribe.return_value
        self.pvm.subscriptions[mock_pv.name] = {'sub': sub}

        def cb_f(): pass

        # Act
        self.pvm.add_callback(mock_pv.name, callback_f=cb_f)

        # Assert
        sub.add_callback.assert_called_with(cb_f)

    @parameterized.expand([
        (1, 2, True),
        (1, 3, True),
        (2, 1, False),
        (1, 1, False)
    ])
    def test_GIVEN_pv_name_WHEN_check_if_data_is_stale_THEN_correct_check(self, last_update, current_time, expected):
        with patch('time.time') as mock_time, patch('HLM_PV_Import.logger.log_stale_pv_warning'):

            # Arrange
            ca_wrapper.TIME_AFTER_STALE = 1  # set 1 second old as stale data
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
