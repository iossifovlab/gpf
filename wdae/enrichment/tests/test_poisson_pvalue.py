'''
Created on Sep 28, 2016

@author: lubo
'''
import unittest
from enrichment.background import poisson_test
from scipy import stats


class PoissonTest(unittest.TestCase):

    def test_experiments(self):
        observed = 21
        expected = 18.1
        expected_pvalue = 0.5546078

        pvalue = poisson_test(observed, expected)
        print(pvalue)
        print(expected_pvalue)
        self.assertAlmostEqual(expected_pvalue, pvalue, 3)

        observed = 4
        expected = 3.3
        expected_pvalue = 0.839

        pvalue = poisson_test(observed, expected)
        print(pvalue)
        print(expected_pvalue)
        self.assertAlmostEqual(expected_pvalue, pvalue, 3)

    def test_samocha_poisson_vs_binom(self):
        observed = 10
        expected = 12.5750980546
        trails = 10
        bg_prob = 0.00320451005262

        poisson_pvalue = poisson_test(observed, expected)
        binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)

        print("poisson: {}, binom: {}".format(poisson_pvalue, binom_pvalue))

        observed = 10
        trails = 10
        expected = 85.8545045253
        bg_prob = 0.0218703617989

        poisson_pvalue = poisson_test(observed, expected)
        binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
        print("poisson: {}, binom: {}".format(poisson_pvalue, binom_pvalue))

        observed = 46
        trails = 546
        expected = 12.5750980546
        bg_prob = 0.00320451005262

        poisson_pvalue = poisson_test(observed, expected)
        binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
        print("poisson: {}, binom: {}".format(poisson_pvalue, binom_pvalue))

        observed = 95
        trails = 2583
        expected = 85.8545045253
        bg_prob = 0.0218703617989

        poisson_pvalue = poisson_test(observed, expected)
        binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
        print("poisson: {}, binom: {}".format(poisson_pvalue, binom_pvalue))
