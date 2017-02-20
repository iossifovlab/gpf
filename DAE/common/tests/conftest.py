'''
Created on Feb 10, 2017

@author: lubo
'''
from common.query_base import VariantTypesMixin
import pytest


@pytest.fixture(scope='session')
def variant_types(request):
    return VariantTypesMixin()
