# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from scipy import stats
from dae.enrichment_tool.samocha_background import poisson_test


def test_experiments() -> None:
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


def test_samocha_poisson_vs_binom() -> None:
    observed = 10
    expected = 12.5750980546
    trails = 10
    bg_prob = 0.00320451005262

    poisson_pvalue = poisson_test(observed, expected)
    binom = stats.binomtest(observed, trails, p=bg_prob)

    print(f"poisson: {poisson_pvalue}, binom: {binom.pvalue}")
    assert poisson_pvalue == pytest.approx(0.5798, rel=1e-3)
    assert binom.pvalue == pytest.approx(1.1418e-25, rel=1e-3)

    observed = 10
    trails = 10
    expected = 85.8545045253
    bg_prob = 0.0218703617989

    poisson_pvalue = poisson_test(observed, expected)
    binom = stats.binomtest(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom.pvalue}")
    assert poisson_pvalue == pytest.approx(7.0114e-25, rel=1e-3)
    assert binom.pvalue == pytest.approx(2.5035e-17, rel=1e-3)

    observed = 46
    trails = 546
    expected = 12.5750980546
    bg_prob = 0.00320451005262

    poisson_pvalue = poisson_test(observed, expected)
    binom = stats.binomtest(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom.pvalue}")
    assert poisson_pvalue == pytest.approx(6.4681e-13, rel=1e-3)
    assert binom.pvalue == pytest.approx(8.0600e-49, rel=1e-3)

    observed = 95
    trails = 2583
    expected = 85.8545045253
    bg_prob = 0.0218703617989

    poisson_pvalue = poisson_test(observed, expected)
    binom = stats.binomtest(observed, trails, p=bg_prob)
    print(f"poisson: {poisson_pvalue}, binom: {binom.pvalue}")
    assert poisson_pvalue == pytest.approx(0.3494, rel=1e-3)
    assert binom.pvalue == pytest.approx(2.1002e-06, rel=1e-3)
