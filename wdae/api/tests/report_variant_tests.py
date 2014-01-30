import unittest

from api.report_variant import prcnt_str, ratio_str


class UtilsTest(unittest.TestCase):
    def test_prcnt_str(self):
        self.assertEqual("10.0%", prcnt_str(1, 10))

    def test_ration_str(self):
        self.assertEqual("0.100", ratio_str(1, 10))
