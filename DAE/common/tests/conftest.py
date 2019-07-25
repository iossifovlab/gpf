'''
Created on Feb 10, 2017

@author: lubo
'''
import os
import pytest

from configparser import ConfigParser

from common.query_base import VariantTypesMixin


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def variant_types(request):
    return VariantTypesMixin()


@pytest.fixture
def configuration():
    filename = relative_to_this_test_folder(
        "fixtures/config_test.conf")

    config_parser = ConfigParser()
    config_parser.optionxform = str

    with open(filename, "r", encoding="utf8") as infile:
        config_parser.read_file(infile)
        return config_parser
