'''
Created on Feb 10, 2017

@author: lubo
'''
from __future__ import unicode_literals
from common.query_base import VariantTypesMixin
import pytest


@pytest.fixture(scope='session')
def variant_types(request):
    return VariantTypesMixin()
