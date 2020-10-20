from __future__ import absolute_import
import unittest
from hamcrest import assert_that, is_, calling, raises
import utilities


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.utilities = utilities

    def test_GIVEN_single_element_tuples_WHEN_convert_to_strings_THEN_string_list_is_returned(self):
        # Arrange
        input_value = [
            ('String 1',),
            ('String 2',),
            ('String 3',),
        ]
        expected_value = ['String 1', 'String 2', 'String 3']

        # Act
        result = self.utilities.single_tuples_to_strings(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_empty_list_WHEN_convert_to_strings_THEN_empty_list_is_returned(self):
        # Arrange
        input_value = []
        expected_value = []

        # Act
        result = self.utilities.single_tuples_to_strings(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_some_multiple_elem_tuples_WHEN_convert_to_strings_THEN_correct_list_is_returned(self):
        # Arrange
        input_value = [
            ('String 1',),
            ('String 2', 'Extra 2'),
            ('String 3',),
        ]
        expected_value = [
            'String 1',
            ('String 2', 'Extra 2'),
            'String 3',
        ]

        # Act
        result = self.utilities.single_tuples_to_strings(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_all_multiple_elem_tuples_WHEN_convert_to_strings_THEN_correct_list_is_returned(self):
        # Arrange
        input_value = [
            ('String 1', 'Extra 1'),
            ('String 2', 'Extra 2'),
            ('String 3', 'Extra 3'),
        ]
        expected_value = [
            ('String 1', 'Extra 1'),
            ('String 2', 'Extra 2'),
            ('String 3', 'Extra 3'),
        ]

        # Act
        result = self.utilities.single_tuples_to_strings(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_pv_name_WHEN_get_short_name_THEN_name_without_domain_is_returned(self):
        # Arrange
        input_value = f'{self.utilities.PvConfig.PV_PREFIX}:{self.utilities.PvConfig.PV_DOMAIN}:NAME1'
        expected_value = 'NAME1'

        # Act
        result = self.utilities.pv_name_without_prefix_and_domain(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_pv_name_without_prefix_and_domain_WHEN_get_short_name_THEN_name_without_domain_is_returned(self):
        # Arrange
        input_value = 'NAME1'
        expected_value = 'NAME1'

        # Act
        result = self.utilities.pv_name_without_prefix_and_domain(input_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_short_pv_name_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = 'MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PvConfig.PV_PREFIX}:{self.utilities.PvConfig.PV_DOMAIN}:{name}'
        
        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_full_pv_name_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        expected = f'{self.utilities.PvConfig.PV_PREFIX}:{self.utilities.PvConfig.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(expected)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_pv_name_with_domain_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = f'{self.utilities.PvConfig.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PvConfig.PV_PREFIX}:{self.utilities.PvConfig.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_pv_name_with_prefix_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = f'{self.utilities.PvConfig.PV_PREFIX}:MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PvConfig.PV_PREFIX}:{self.utilities.PvConfig.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_empty_list_WHEN_add_list_blank_values_THEN_return_correct_list_size(self):
        # Arrange
        list_ = []
        size = 5
        expected = [None, None, None, None, None]

        # Act
        result = self.utilities.list_add_blank_values(list_, size)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_list_with_values_WHEN_add_list_blank_values_THEN_return_correct_list_size(self):
        # Arrange
        list_ = [1, 2]
        size = 5
        expected = [1, 2, None, None, None]

        # Act
        result = self.utilities.list_add_blank_values(list_, size)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_list_desired_size_WHEN_add_list_blank_values_THEN_return_correct_list_size(self):
        # Arrange
        list_ = [1, 2, 3, 4, 5]
        size = 5
        expected = [1, 2, 3, 4, 5]

        # Act
        result = self.utilities.list_add_blank_values(list_, size)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_list_bigger_size_WHEN_add_list_blank_values_THEN_return_correct_list_size(self):
        # Arrange
        list_ = [1, 2, 3, 4, 5]
        size = 4

        # Assert
        assert_that(calling(self.utilities.list_add_blank_values).with_args(list_, size),
                    raises(ValueError))
