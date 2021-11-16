import unittest
import mock
import sys
from parameterized import parameterized
from shared.utils import *

NAME = 'pv_name:4_test'
PREFIX = 'prefix:'
DOMAIN = 'domain:'
VESSEL = 2
CRYO = 4
GASCOUNTER = 7

class TestUtilities(unittest.TestCase):

    @parameterized.expand([
        (
                NAME
        ),
        (
                f'{PREFIX}{DOMAIN}{NAME}',
        ),
        (
                f'{DOMAIN}{NAME}'
        ),
        (
                f'{PREFIX}{NAME}'
        )
    ])
    def test_GIVEN_pv_name_WHEN_get_full_name_THEN_return_full_name(self, pv_name):
        result = get_full_pv_name(pv_name, prefix=PREFIX, domain=DOMAIN)
        self.assertEqual(f'{PREFIX}{DOMAIN}{NAME}', result)

    @parameterized.expand([
        (
                NAME
        ),
        (
                f'{PREFIX}{DOMAIN}{NAME}',
        ),
        (
                f'{DOMAIN}{NAME}'
        ),
        (
                f'{PREFIX}{NAME}'
        )
    ])
    def test_GIVEN_no_colons_WHEN_get_full_name_THEN_return_correct_full_pv_name(self, pv_name):
        result = get_full_pv_name(pv_name, prefix=PREFIX[:-1], domain=DOMAIN[:-1])
        self.assertEqual(f'{PREFIX}{DOMAIN}{NAME}', result)

    @parameterized.expand([
        (
                NAME
        ),
        (
                f'{PREFIX}{DOMAIN}{NAME}'
        ),
        (
                f'{DOMAIN}{NAME}'
        ),
        (
                f'{PREFIX}{NAME}'
        )
    ])
    def test_GIVEN_pv_name_WHEN_get_short_name_THEN_return_name_without_prefix_and_domain(self, input_val):
        result = get_short_pv_name(input_val, prefix=PREFIX, domain=DOMAIN)
        self.assertEqual(NAME, result)

    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_THEN_need_connection_succeeds(self, mock_func):
        mock_func.return_value = True

        @need_connection
        def test_function():
            return True

        self.assertTrue(test_function())
        mock_func.assert_called()

    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_not_connected_THEN_need_connection_fail(self, mock_func):
        mock_func.return_value = False

        @need_connection
        def test_function():
            return True

        self.assertIsNone(test_function())
        mock_func.assert_called()

    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_object_does_not_exist_THEN_return_None(self, _, mock_object):
        mock_object.return_value = None
        self.assertIsNone(get_object_module(1))
        mock_object.assert_called()

    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_invalid_class_THEN_return_None(self, _, mock_object):
        self.assertIsNone(get_object_module(1, "INVALID VALUE"))
        mock_object.assert_not_called()

    @mock.patch("shared.utils._get_module_object")
    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_object_is_vessel_THEN_return_module(self, _, mock_object, mock_get_module):
        obj = mock_object.return_value
        obj.ob_objecttype.ot_objectclass.oc_name = VESSEL
        mock_get_module.return_value = 1
        mock_id = 0
        self.assertEqual(get_object_module(mock_id), 1)
        mock_object.assert_called()
        mock_get_module.assert_called_with(mock_id, 18)

    @mock.patch("shared.utils._get_module_object")
    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_object_is_vessel_THEN_return_module(self, _, mock_object, mock_get_module):
        obj = mock_object.return_value
        obj.ob_objecttype.ot_objectclass.oc_name = VESSEL
        mock_get_module.return_value = 1
        mock_id = 0
        self.assertEqual(get_object_module(mock_id), 1)
        mock_object.assert_called()
        mock_get_module.assert_called_with(mock_id, 18)

    @mock.patch("shared.utils._get_module_object")
    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_object_is_cryostat_THEN_return_module(self, _, mock_object, mock_get_module):
        obj = mock_object.return_value

        obj.ob_objecttype.ot_objectclass.oc_name = CRYO
        mock_get_module.return_value = 1
        mock_id = 0
        self.assertEqual(get_object_module(mock_id), 1)
        mock_object.assert_called()
        mock_get_module.assert_called_with(mock_id, 18)

    @mock.patch("shared.utils._get_module_object")
    @mock.patch("shared.utils.GamObject.get_or_none")
    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_AND_object_is_counter_THEN_return_module(self, _, mock_object, mock_get_module):
        obj = mock_object.return_value

        obj.ob_objecttype.ot_objectclass.oc_name = GASCOUNTER
        mock_get_module.return_value = 1
        mock_id = 0
        self.assertEqual(get_object_module(mock_id), 1)
        mock_object.assert_called()
        mock_get_module.assert_called_with(mock_id, 16)