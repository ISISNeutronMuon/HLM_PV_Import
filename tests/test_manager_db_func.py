import unittest
import mock

from tests import mock_database
from ServiceManager import db_func

VESSEL = 2
CRYOSTAT = 4
GAS_COUNTER = 7
SLD = 18
GCM = 16


class TestManagerDBFunc(unittest.TestCase):

    def test_db_connect_WHEN_database_not_mocked_THEN_raise_exception(self):
        self.assertRaises(db_func.DBConnectionError, db_func.db_connect)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    def test_db_connect_WHEN_mock_database_THEN_raise_exception(self):
        db_func.db_connect()
        mock_database.database.close()

    @mock.patch("ServiceManager.db_func.database.is_connection_usable")
    def test_db_connected_WHEN_db_connected_THEN_returns_true(self, mock_func):
        mock_func.return_value = True
        self.assertTrue(db_func.db_connected())
        mock_func.assert_called()

    @mock.patch("ServiceManager.db_func.database.is_connection_usable")
    def test_db_connected_WHEN_db_not_connected_THEN_returns_false(self, mock_func):
        mock_func.return_value = False
        self.assertFalse(db_func.db_connected())
        mock_func.assert_called()

    def test_get_object_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object(0))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertIsNone(db_func.get_object(0))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_object(1), obj)

    def test_get_object_id_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_id("test"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_id_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_id("test"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_id_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_object_id("test"), obj.ob_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_id_WHEN_multiple_present_THEN_returns_lowest_id(self):
        with mock_database.Database():
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_object_id("test"), obj.ob_id)

    def test_get_max_object_id_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_max_object_id())

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_max_object_id_WHEN_not_present_THEN_returns_zero(self):
        with mock_database.Database():
            self.assertTrue(db_func.db_connected())
            self.assertEqual(db_func.get_max_object_id(), 0)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_max_object_id_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_max_object_id(), obj.ob_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_max_object_id_WHEN_multi_present_THEN_returns_highest(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            obj = mock_database.GamObject.create(ob_name="test", ob_objecttype=1)
            self.assertEqual(db_func.get_max_object_id(), obj.ob_id)

    def test_get_object_name_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_name(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_name_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_name(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_name_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertEqual(db_func.get_object_name(1), "test1")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_name_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=1)
            self.assertEqual(db_func.get_object_name(1), "test1")

    def test_get_object_type_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_type(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_type_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_type(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_type_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            self.assertEqual(db_func.get_object_type(1), "test2")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_type_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=2)
            mock_database.GamObjecttype.create(ot_name="test3", ot_objectclass=0)
            self.assertEqual(db_func.get_object_type(1), "test3")

    def test_get_object_class_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_class(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_class_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_class(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_class_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=1)
            mock_database.GamObjectclass.create(oc_name="test3", oc_function=0, oc_positiontype=0)
            self.assertEqual(db_func.get_object_class(1), "test3")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_class_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=2)
            mock_database.GamObjecttype.create(ot_name="test3", ot_objectclass=1)
            mock_database.GamObjectclass.create(oc_name="test4", oc_function=0, oc_positiontype=0)
            self.assertEqual(db_func.get_object_class(1), "test4")

    def test_get_object_function_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_function(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_function_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_function(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_function_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=1)
            mock_database.GamObjectclass.create(oc_name="test3", oc_function=1, oc_positiontype=0)
            mock_database.GamFunction.create(of_name="test4")
            self.assertEqual(db_func.get_object_function(1), "test4")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_function_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=2)
            mock_database.GamObjecttype.create(ot_name="test3", ot_objectclass=1)
            mock_database.GamObjectclass.create(oc_name="test4", oc_function=1, oc_positiontype=0)
            mock_database.GamFunction.create(of_name="test5")
            self.assertEqual(db_func.get_object_function(1), "test5")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_function_WHEN_present_but_unnamed_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=1)
            mock_database.GamObjectclass.create(oc_name="test3", oc_function=1, oc_positiontype=0)
            mock_database.GamFunction.create()
            self.assertIsNone(db_func.get_object_function(1))

    def test_get_object_display_group_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_object_display_group(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_display_group_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertIsNone(db_func.get_object_display_group(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_display_group_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1, ob_displaygroup=1)
            mock_database.GamDisplaygroup.create(dg_name="test2")
            self.assertEqual(db_func.get_object_display_group(1), "test2")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_display_group_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1, ob_displaygroup=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=2, ob_displaygroup=2)
            mock_database.GamDisplaygroup.create(dg_name="test4")
            mock_database.GamDisplaygroup.create(dg_name="test3")
            self.assertEqual(db_func.get_object_display_group(1), "test4")
            self.assertEqual(db_func.get_object_display_group(2), "test3")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_object_display_group_WHEN_present_but_unnamed_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1, ob_displaygroup=1)
            mock_database.GamDisplaygroup.create()
            self.assertIsNone(db_func.get_object_display_group(1))

    def test_get_class_id_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_class_id(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_class_id_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObjectclass.create(oc_name="test3", oc_function=0, oc_positiontype=0)
            self.assertIsNone(db_func.get_class_id(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_class_id_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=1)
            test_class = mock_database.GamObjectclass.create(oc_name="test3", oc_function=0, oc_positiontype=0)
            self.assertEqual(db_func.get_class_id(1), test_class.oc_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_class_id_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test3", ot_objectclass=1)
            test_class = mock_database.GamObjectclass.create(oc_name="test4", oc_function=0, oc_positiontype=0)
            self.assertEqual(db_func.get_class_id(1), test_class.oc_id)

    def test_get_measurement_types_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_measurement_types(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_measurement_types_WHEN_class_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObjectclass.create(oc_name="test1", oc_function=0, oc_positiontype=0)
            self.assertIsNone(db_func.get_measurement_types(2))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_measurement_types_WHEN_no_types_THEN_returns_list_of_none(self):
        with mock_database.Database():
            mock_database.GamObjectclass.create(oc_name="test1", oc_function=0, oc_positiontype=0)
            self.assertListEqual(db_func.get_measurement_types(1), [None, None, None, None, None])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_measurement_types_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObjectclass.create(oc_name="test1", oc_function=0, oc_positiontype=0,
                                                oc_measuretype1="test2", oc_measuretype2="test3",
                                                oc_measuretype3="test4", oc_measuretype4="test5",
                                                oc_measuretype5="test6")
            self.assertListEqual(db_func.get_measurement_types(1), ['test2', 'test3', 'test4', 'test5', 'test6'])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_measurement_types_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObjectclass.create(oc_name="test1", oc_function=0, oc_positiontype=0,
                                                oc_measuretype1="test2", oc_measuretype2="test3",
                                                oc_measuretype3="test4", oc_measuretype4="test5",
                                                oc_measuretype5="test6")
            mock_database.GamObjectclass.create(oc_name="test7", oc_function=0, oc_positiontype=0)
            self.assertEqual(db_func.get_measurement_types(2), [None, None, None, None, None])
            self.assertListEqual(db_func.get_measurement_types(1), ['test2', 'test3', 'test4', 'test5', 'test6'])

    def test_get_all_object_names_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_all_object_names())

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_object_names_WHEN_not_present_THEN_returns_empty(self):
        with mock_database.Database():
            self.assertListEqual(db_func.get_all_object_names(), [])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_object_names_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            self.assertListEqual(db_func.get_all_object_names(), ["test1"])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_object_names_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=1)
            mock_database.GamObject.create(ob_name="test2", ob_objecttype=1)
            self.assertListEqual(db_func.get_all_object_names(), ["test1", "test2"])

    def test_get_type_id_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_type_id("test1"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_type_id_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            self.assertIsNone(db_func.get_type_id("test1"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_type_id_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            obj = mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            self.assertEqual(db_func.get_type_id("test1"), obj.ot_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_type_id_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            obj = mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            self.assertEqual(db_func.get_type_id("test2"), obj.ot_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_type_id_WHEN_multi_same_THEN_returns_first(self):
        with mock_database.Database():
            obj = mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            self.assertEqual(db_func.get_type_id("test1"), obj.ot_id)

    def test_get_all_type_names_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_all_type_names())

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_type_names_WHEN_not_present_THEN_returns_empty(self):
        with mock_database.Database():
            self.assertListEqual(db_func.get_all_type_names(), [])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_type_names_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            self.assertListEqual(db_func.get_all_type_names(), ["test1"])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_type_names_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            self.assertListEqual(db_func.get_all_type_names(), ["test1", "test2"])

    def test_display_group_id_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_display_group_id("test1"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_display_group_id_WHEN_not_present_THEN_returns_none(self):
        with mock_database.Database():
            mock_database.GamDisplaygroup.create(dg_name="test2")
            self.assertIsNone(db_func.get_display_group_id("test1"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_display_group_id_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            obj = mock_database.GamDisplaygroup.create(dg_name="test1")
            self.assertEqual(db_func.get_display_group_id("test1"), obj.dg_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_display_group_id_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamDisplaygroup.create(dg_name="test1")
            obj = mock_database.GamDisplaygroup.create(dg_name="test2")
            self.assertEqual(db_func.get_display_group_id("test2"), obj.dg_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_display_group_id_WHEN_multi_same_THEN_returns_first(self):
        with mock_database.Database():
            obj = mock_database.GamDisplaygroup.create(dg_name="test1")
            mock_database.GamDisplaygroup.create(dg_name="test1")
            self.assertEqual(db_func.get_display_group_id("test1"), obj.dg_id)

    def test_get_all_display_names_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.get_all_display_names())

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_display_names_WHEN_not_present_THEN_returns_empty(self):
        with mock_database.Database():
            self.assertListEqual(db_func.get_all_display_names(), [])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_display_names_WHEN_present_THEN_returns_it(self):
        with mock_database.Database():
            mock_database.GamDisplaygroup.create(dg_name="test1")
            self.assertListEqual(db_func.get_all_display_names(), ["test1"])

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_get_all_display_names_WHEN_multi_present_THEN_returns_correct(self):
        with mock_database.Database():
            mock_database.GamDisplaygroup.create(dg_name="test1")
            mock_database.GamDisplaygroup.create(dg_name="test2")
            self.assertListEqual(db_func.get_all_display_names(), ["test1", "test2"])

    def test_add_object_WHEN_no_connection_THEN_returns_none(self):
        self.assertIsNone(db_func.add_object("test1", 0))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_THEN_returns_id(self):
        with mock_database.Database():
            ob_id = db_func.add_object("test1", 0)
            self.assertEqual(ob_id, 1)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test1"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_AND_already_exists_THEN_exception(self):
        with mock_database.Database():
            mock_database.GamObject.create(ob_name="test1", ob_objecttype=0)
            with self.assertRaises(db_func.DBObjectNameAlreadyExists):
                db_func.add_object("test1", 0)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_AND_add_multi_THEN_returns_id(self):
        with mock_database.Database():
            ob_id = db_func.add_object("test1", 0)
            self.assertEqual(ob_id, 1)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test1"))
            ob_id = db_func.add_object("test2", 0)
            self.assertEqual(ob_id, 2)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test2"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_AND_valid_type_THEN_object_added_AND_has_type(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            ob_id = db_func.add_object("test1", 1)
            self.assertEqual(ob_id, 1)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test1"))
            self.assertEqual(db_func.get_object_type(ob_id), "test2")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_AND_valid_display_group_THEN_object_added_AND_has_display_group(self):
        with mock_database.Database():
            mock_database.GamDisplaygroup.create(dg_name="test2")
            ob_id = db_func.add_object("test1", 0, 1)
            self.assertEqual(ob_id, 1)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test1"))
            self.assertEqual(db_func.get_object_display_group(ob_id), "test2")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_object_WHEN_connection_AND_comment_THEN_has_comment(self):
        with mock_database.Database():
            ob_id = db_func.add_object("test1", 0, 0, "test_comment")
            self.assertEqual(ob_id, 1)
            self.assertIsNotNone(db_func.get_object(ob_id))
            self.assertIsNotNone(db_func.get_object_id("test1"))
            self.assertEqual(db_func.get_object(1).ob_comment, "test_comment")

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_relation_WHEN_connection_AND_valid_objects_THEN_adds_relation(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test1", ot_objectclass=0)
            mock_database.GamObjecttype.create(ot_name="test2", ot_objectclass=0)
            db_func.add_relation(1, 2)
            self.assertIsNotNone(mock_database.GamObjectrelation.get_or_none(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_add_relation_WHEN_connectionTHEN_adds_relation(self):
        with mock_database.Database():
            db_func.add_relation(1, 2)
            self.assertIsNotNone(mock_database.GamObjectrelation.get_or_none(1))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_create_module_if_required_WHEN_connection_AND_module_not_required_THEN_no_module(self):
        with mock_database.Database():
            db_func.create_module_if_required(1, "test1", "test2", 1)
            self.assertIsNone(mock_database.GamObjectrelation.get_or_none(1))
            self.assertIsNone(db_func.get_object_id("SLD \"test1\" (ID: 1)"))

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_create_module_if_required_WHEN_connection_AND_sld_required_THEN_sld(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test3", ot_id=SLD, ot_objectclass=0)
            db_func.create_module_if_required(1, "test1", "test2", VESSEL)
            self.assertIsNotNone(mock_database.GamObjectrelation.get_or_none(1))
            obj = mock_database.GamObject.get_or_none(1)
            self.assertEqual("SLD \"test1\" (ID: 1)", obj.ob_name)
            self.assertEqual("Software Level Device for test2 \"test1\" (ID: 1)", obj.ob_comment)
            self.assertEqual(SLD, obj.ob_objecttype.ot_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_create_module_if_required_WHEN_connection_AND_sld_required_for_cryostat_THEN_sld(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test3", ot_id=SLD, ot_objectclass=0)
            db_func.create_module_if_required(1, "test1", "test2", CRYOSTAT)
            self.assertIsNotNone(mock_database.GamObjectrelation.get_or_none(1))
            obj = mock_database.GamObject.get_or_none(1)
            self.assertEqual("SLD \"test1\" (ID: 1)", obj.ob_name)
            self.assertEqual("Software Level Device for test2 \"test1\" (ID: 1)", obj.ob_comment)
            self.assertEqual(SLD, obj.ob_objecttype.ot_id)

    @mock.patch("ServiceManager.db_func.database", new=mock_database.database)
    @mock.patch("shared.utils.database", new=mock_database.database)
    def test_create_module_if_required_WHEN_connection_AND_gcm_required_THEN_gcm(self):
        with mock_database.Database():
            mock_database.GamObjecttype.create(ot_name="test3", ot_id=GCM, ot_objectclass=0)
            db_func.create_module_if_required(1, "test1", "test2", GAS_COUNTER)
            self.assertIsNotNone(mock_database.GamObjectrelation.get_or_none(1))
            obj = mock_database.GamObject.get_or_none(1)
            self.assertEqual("GCM \"test1\" (ID: 1)", obj.ob_name)
            self.assertEqual("Gas Counter Module for test2 \"test1\" (ID: 1)", obj.ob_comment)
            self.assertEqual(GCM, obj.ob_objecttype.ot_id)
