'''
Created on Nov 23, 2016

@author: lubo
'''
import pytest


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     help="run slow tests")
    parser.addoption("--runveryslow", action="store_true",
                     help="run very slow tests")
    parser.addoption("--ssc_wg", action="store_true",
                     help="run SSC WG tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runveryslow"):
        # --runveryslow given in cli: do not skip slow tests
        skip_veryslow = pytest.mark.skip(
            reason="need --runveryslow option to run")
        for item in items:
            if "veryslow" in item.keywords:
                item.add_marker(skip_veryslow)

    if not config.getoption("--runslow") and \
            not config.getoption("--runveryslow"):
        # --runslow given in cli: do not skip slow tests
        skip_slow = pytest.mark.skip(
            reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
