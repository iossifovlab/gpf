# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from scipy import stats
from dae.enrichment_tool.background import poisson_test


def test_experiments():
    observed = 21
    expected = 18.1
    expected_pvalue = 0.5546078

    pvalue = poisson_test(observed, expected)
    assert expected_pvalue == pytest.approx(pvalue, abs=1e-3)

    observed = 4
    expected = 3.3
    expected_pvalue = 0.839

    pvalue = poisson_test(observed, expected)
    assert expected_pvalue == pytest.approx(pvalue, abs=1e-3)


def test_samocha_poisson_vs_binom():
    observed = 10
    expected = 12.5750980546
    trails = 10
    bg_prob = 0.00320451005262

    poisson_pvalue = poisson_test(observed, expected)
    binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)

    print(f"poisson: {poisson_pvalue}, binom: {binom_pvalue}")

    observed = 10
    trails = 10
    expected = 85.8545045253
    bg_prob = 0.0218703617989

    poisson_pvalue = poisson_test(observed, expected)
    binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom_pvalue}")

    observed = 46
    trails = 546
    expected = 12.5750980546
    bg_prob = 0.00320451005262

    poisson_pvalue = poisson_test(observed, expected)
    binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom_pvalue}")

    observed = 95
    trails = 2583
    expected = 85.8545045253
    bg_prob = 0.0218703617989

    poisson_pvalue = poisson_test(observed, expected)
    binom_pvalue = stats.binom_test(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom_pvalue}")
