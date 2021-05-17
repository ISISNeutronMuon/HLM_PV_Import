import unittest
from parameterized import parameterized
from shared.utils import get_full_pv_name, get_short_pv_name

NAME = 'pv_name:4_test'
PREFIX = 'prefix:'
DOMAIN = 'domain:'


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
