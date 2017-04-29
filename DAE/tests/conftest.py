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


def slow():
    pytest.mark.skipif(
        not pytest.config.getoption("--runslow"),  # @UndefinedVariable
        reason="need --runslow option to run"
    )
