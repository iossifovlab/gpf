import pytest

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),  # @UndefinedVariable
    reason="need --runslow option to run",
)


veryslow = pytest.mark.skipif(
    not pytest.config.getoption("--runveryslow"),  # @UndefinedVariable
    reason="need --runveryslow option to run",
)


ssc_wg = pytest.mark.skipif(
    not pytest.config.getoption("--ssc_wg"),  # @UndefinedVariable
    reason="need --ssc_wg option to run",
)
