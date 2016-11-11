'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from pheno_tool.measures import Measures, NormalizedMeasure
from pheno.pheno_db import PhenoDB


@pytest.fixture(scope='session')
def phdb(request):
    db = PhenoDB()
    db.load()
    return db


@pytest.fixture(scope='session')
def measures(request, phdb):
    ms = Measures(phdb)
    ms.load()
    return ms


@pytest.fixture(scope='session')
def head_circumference(request, measures):
    measure = NormalizedMeasure(
        'ssc_commonly_used.head_circumference', measures)
    return measure


@pytest.fixture(scope='session')
def verbal_iq(request, measures):
    measure = NormalizedMeasure(
        'pheno_common.verbal_iq', measures)
    return measure
