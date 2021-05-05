import unittest
from HLM_PV_Import import utilities
from HLM_PV_Import.settings import CA
from parameterized import parameterized


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.utilities = utilities

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
