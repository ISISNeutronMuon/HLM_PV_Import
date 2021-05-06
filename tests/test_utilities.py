import unittest
from HLM_PV_Import import utilities
from HLM_PV_Import.settings import CA
from parameterized import parameterized


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.utilities = utilities

    @parameterized.expand([
        (f'{CA.PV_PREFIX}{CA.PV_DOMAIN}NAME1', 'NAME1'),
        (f'{CA.PV_PREFIX}{CA.PV_DOMAIN}A:B:NAME1', 'A:B:NAME1'),
        (f'{CA.PV_DOMAIN}A:B:NAME1', 'A:B:NAME1'),
        (f'{CA.PV_PREFIX}A:B:NAME1', 'A:B:NAME1'),
        ('NAME1', 'NAME1'),
        ('A:B:NAME1', 'A:B:NAME1')
    ])
    def test_GIVEN_pv_name_WHEN_get_short_name_THEN_short_name_is_returned(self, input_val, exp_val):
        # Act
        result = self.utilities.pv_name_without_prefix_and_domain(input_val)

        # Assert
        self.assertEqual(exp_val, result)

    @parameterized.expand([
        (
            'MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'),
        (
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        ),
        (
            f'{CA.PV_PREFIX}MOTHER_DEWAR:HE_LEVEL',
            f'{CA.PV_PREFIX}{CA.PV_DOMAIN}MOTHER_DEWAR:HE_LEVEL'
        )
    ])
    def test_GIVEN_pv_name_WHEN_get_full_name_THEN_full_name_is_returned(self, input_val, exp_val):
        # Act
        result = self.utilities.get_full_pv_name(input_val)

        # Assert
        self.assertEqual(exp_val, result)
