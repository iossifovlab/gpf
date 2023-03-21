import pytest

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),  # type: ignore
    reason="need --runslow option to run",
)


veryslow = pytest.mark.skipif(
    not pytest.config.getoption("--runveryslow"),  # type: ignore
    reason="need --runveryslow option to run",
)


ssc_wg = pytest.mark.skipif(
    not pytest.config.getoption("--ssc_wg"),  # type: ignore
    reason="need --ssc_wg option to run",
)
