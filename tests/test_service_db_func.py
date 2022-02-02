import unittest
import mock

from tests import mock_database
from HLM_PV_Import import db_func


RECONNECT_MAX_WAIT_TIME = 14400


class TestServiceDBFunc(unittest.TestCase):

    def test_increase_reconnect_wait_time_WHEN_0_THEN_return_0(self):
        self.assertEqual(db_func.increase_reconnect_wait_time(0), 0)

    def test_increase_reconnect_wait_time_WHEN_less_than_max_THEN_return_doubled(self):
        self.assertEqual(db_func.increase_reconnect_wait_time(1), 2)

    def test_increase_reconnect_wait_time_WHEN_double_less_than_max_THEN_return_doubled(self):
        self.assertEqual(db_func.increase_reconnect_wait_time(RECONNECT_MAX_WAIT_TIME/2), RECONNECT_MAX_WAIT_TIME)

    def test_increase_reconnect_wait_time_WHEN_double_not_less_than_max_THEN_return_max(self):
        self.assertEqual(db_func.increase_reconnect_wait_time(10000), RECONNECT_MAX_WAIT_TIME)

    @mock.patch("HLM_PV_Import.db_func.logger.info")
    @mock.patch("HLM_PV_Import.db_func.database.connect")
    def test_db_connect_WHEN_valid_db_THEN_connects(self, mock_connection, mock_logger):
        mock_connection.return_value = True
        db_func.db_connect()
        mock_logger.assert_called_with('Database connection successful.')

    @mock.patch("HLM_PV_Import.db_func.logger.error")
    @mock.patch("HLM_PV_Import.db_func.database.connect")
    def test_db_connect_WHEN_no_db_THEN_fails(self, mock_connection, mock_logger):
        error = Exception("Failed")
        mock_connection.side_effect = error
        db_func.db_connect()
        mock_logger.assert_called_with(error)

    @mock.patch("HLM_PV_Import.db_func.RECONNECT_ATTEMPTS_MAX", 100)
    @mock.patch("HLM_PV_Import.db_func.check_db_connection", side_effect=db_func.check_db_connection)
    def test_check_db_connection_WHEN_no_db_THEN_exception_AND_called_max_attempt_times_before_exception(self, mock_function):
        self.assertRaises(Exception, mock_function, 1, 0)
        self.assertEqual(101, mock_function.call_count)

    @mock.patch("HLM_PV_Import.db_func.check_db_connection", side_effect=db_func.check_db_connection)
    @mock.patch("HLM_PV_Import.db_func.database.is_connection_usable", return_value=True)
    def test_check_db_connection_WHEN_db_THEN_return_true_and_called_once(self, mock_function, mock_connection):
        self.assertTrue(mock_function(1, 1))
        self.assertEqual(1, mock_function.call_count)

    @mock.patch("shared.db_models.database.is_connection_usable")
    def test_GIVEN_database_connected_THEN_need_connection_succeeds(self, mock_function):
        mock_function.return_value = True

        @db_func.check_connection
        def test_function():
            return True

        self.assertTrue(test_function())
        mock_function.assert_called()

    @mock.patch("HLM_PV_Import.db_func.RECONNECT_ATTEMPTS_MAX", 1)
    @mock.patch("HLM_PV_Import.db_func.check_db_connection", side_effect=db_func.check_db_connection)
    def test_GIVEN_database_connected_THEN_need_connection_fails(self, mock_function):

        @db_func.check_connection
        def test_function():
            return True

        self.assertRaises(Exception, test_function)

    @mock.patch("HLM_PV_Import.db_func.database", new=mock_database.database)
    def test_get_object_GIVEN_no_object_THEN_returns_none(self):
        with mock_database.Database():
            self.assertIsNone(db_func.get_object(1))

    @mock.patch("HLM_PV_Import.db_func.database", new=mock_database.database)
    def test_get_object_GIVEN_object_THEN_returns_it(self):

        with mock_database.Database():
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_object(1), obj)
