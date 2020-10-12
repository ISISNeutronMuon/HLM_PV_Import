from __future__ import absolute_import
import unittest
from hamcrest import *
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
        domain_value = 'DO:MAIN'
        input_value = 'AB:CD234:DO:MAIN:NAME1'
        expected_value = 'NAME1'

        # Act
        result = self.utilities.pv_name_without_domain(input_value, domain_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_pv_name_without_domain_WHEN_get_short_name_THEN_name_without_domain_is_returned(self):
        # Arrange
        domain_value = 'DO:MAIN'
        input_value = 'NAME1'
        expected_value = 'NAME1'

        # Act
        result = self.utilities.pv_name_without_domain(input_value, domain_value)

        # Assert
        assert_that(result, is_(expected_value))

    def test_GIVEN_short_pv_name_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = 'MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PV_PREFIX}:{self.utilities.PV_DOMAIN}:{name}'

        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_full_pv_name_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        expected = f'{self.utilities.PV_PREFIX}:{self.utilities.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(expected)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_pv_name_with_domain_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = f'{self.utilities.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PV_PREFIX}:{self.utilities.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))

    def test_GIVEN_pv_name_with_prefix_WHEN_get_full_name_THEN_return_correct_name(self):
        # Arrange
        name = f'{self.utilities.PV_PREFIX}:MOTHER_DEWAR:HE_LEVEL'
        expected = f'{self.utilities.PV_PREFIX}:{self.utilities.PV_DOMAIN}:MOTHER_DEWAR:HE_LEVEL'

        # Act
        result = self.utilities.get_full_pv_name(name)

        # Assert
        assert_that(result, is_(expected))
