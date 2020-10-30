import unittest

from mock import patch
import ca_wrapper
from ca_wrapper import PvMonitors
from parameterized import parameterized


class TestWrapper(unittest.TestCase):

    @parameterized.expand([
        ([b'val'], 'val'),
        (['val'], 'val')
    ])
    @patch('ca_wrapper.read')
    def test_GIVEN_value_WHEN_get_pv_value_THEN_return_string(self, return_val, exp_val, mock_read):
        mock_read.return_value.data = return_val
        result = ca_wrapper.get_pv_value('')
        self.assertEqual(exp_val, result)


class TestPvMonitors(unittest.TestCase):

    def setUp(self):
        patcher = patch('ca_wrapper.Context')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.pvm = PvMonitors([])
        self.dummy_data = {'PV_name_1': 123, 'PV_name_2': 117.4, 'PV_name_3': 'High', 'PV_name_4': None}

    def test_GIVEN_pv_name_WHEN_clear_callbacks_THEN_clear_pv_subscription(self):
        pass

    def test_GIVEN_pv_name_WHEN_remove_pv_THEN_clear_callback_and_remove_from_data(self):
        pass
