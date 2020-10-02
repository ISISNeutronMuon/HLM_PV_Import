import unittest

import caproto.sync.client

from hamcrest import *
from mock import MagicMock, patch
import ca_wrapper


class TestWrapperMethods(unittest.TestCase):

    def setUp(self):
        self.wrapper = ca_wrapper

    def test_GIVEN_invalid_pv_WHEN_get_pv_value_THEN_exception_raised(self):
        assert_that(calling(self.wrapper.get_pv_value).with_args('', timeout=1),
                    raises(caproto.sync.client.CaprotoTimeoutError))

    @patch('ca_wrapper.get_chan')
    def test_GIVEN_bytes_WHEN_get_pv_value_THEN_return_string(self, mock_get_chan):
        # Arrange
        expected_value = 'val'
        obj = MagicMock()
        obj.data = [b'val']
        mock_get_chan.return_value = obj

        # Act
        result = self.wrapper.get_pv_value('PV')

        # Assert
        assert_that(result, is_(expected_value))

