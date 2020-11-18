import unittest
from HLM_PV_Import import utilities
from HLM_PV_Import.constants import CA
from parameterized import parameterized


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.utilities = utilities

    @parameterized.expand([
        ([], []),
        ([('String 1',), ('String 2',), ('String 3',)], ['String 1', 'String 2', 'String 3']),
        ([('String 1',), ('String 2', 'Extra 2'), ('String 3',)], ['String 1', ('String 2', 'Extra 2'), 'String 3']),
        (
            [('String 1', 'Extra 1'), ('String 2', 'Extra 2'), ('String 3', 'Extra 3')],
            [('String 1', 'Extra 1'), ('String 2', 'Extra 2'), ('String 3', 'Extra 3')]
        )
    ])
    def test_GIVEN_single_element_tuples_WHEN_convert_to_strings_THEN_string_list_is_returned(self, input_val, exp_val):

        # Act
        result = self.utilities.single_tuples_to_strings(input_val)

        # Assert
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        (f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:NAME1', 'NAME1'),
        ('NAME1', 'NAME1')
    ])
    def test_GIVEN_pv_name_WHEN_get_short_name_THEN_name_without_domain_is_returned(self, input_val, exp_val):
        # Act
        result = self.utilities.pv_name_without_prefix_and_domain(input_val)

        # Assert
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        ('MOTHER_DEWAR:HE_LEVEL', f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'),
        (
            f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_PREFIX}:MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}:{CA.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'
        )
    ])
    def test_GIVEN_pv_name_WHEN_get_full_name_THEN_return_full_name(self, input_val, exp_val):
        # Act
        result = self.utilities.get_full_pv_name(input_val)

        # Assert
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        ([], 5, [None, None, None, None, None]),
        ([1, 2], 5, [1, 2, None, None, None]),
        ([1, 2, 3, 4, 5], 5, [1, 2, 3, 4, 5]),
    ])
    def test_GIVEN_list_WHEN_add_list_blank_values_THEN_return_correct_list_size(self, list_, size, expected):
        # Act
        result = self.utilities.list_add_blank_values(list_, size)

        # Assert
        self.assertEqual(expected, result)

    def test_GIVEN_list_bigger_size_WHEN_add_list_blank_values_THEN_return_correct_list_size(self):
        # Arrange
        list_ = [1, 2, 3, 4, 5]
        size = 4

        # Assert
        with self.assertRaises(ValueError):
            self.utilities.list_add_blank_values(list_, size)

    @parameterized.expand([
        (True, {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}),
        (False, {1: 1, 2: 2, 3: 3, 4: 4}),
        (False, {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}),
        (False, {1: 1, 2: 2, 6: 3, 4: 4, 5: 5}),
        (False, {}),
        (True, {1: None, 2: None, 3: None, 4: None, 5: None})
    ])
    def test_GIVEN_measurements_dict_WHEN_check_meas_dict_valid_THEN_return_validity(self, expected, meas_dict):
        result = self.utilities.meas_values_dict_valid(meas_dict)
        self.assertEqual(expected, result)

    def test_GIVEN_pv_names_WHEN_remove_raw_and_sim_pvs_THEN_correct_list_returned(self):
        # Arrange
        prefix = self.utilities.CA.PV_PREFIX
        domain = self.utilities.CA.PV_DOMAIN

        pv_names = [
            f'{prefix}:{domain}:230ABC:ALARM',
            f'{prefix}:{domain}:ALARM:_RAW',
            f'{prefix}:{domain}:SIM:230ABC:ALARM',
            f'{prefix}:{domain}:230ABC:ANOTHER'
        ]
        expected_result = [f'{prefix}:{domain}:230ABC:ALARM', f'{prefix}:{domain}:230ABC:ANOTHER']

        # Act
        result = self.utilities.remove_raw_and_sim_pvs(pv_names)

        # Assert
        self.assertEqual(result, expected_result)
