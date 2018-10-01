'''
Created on Sep 26, 2018

@author: lubo
'''
import pytest
from transmitted.legacy_query import TransmissionLegacy
from transmitted.mysql_query import MysqlTransmittedQuery


@pytest.fixture(scope='session')
def mysql_backend():
    from DAE import vDB
    study = vDB.get_study("w1202s766e611")
    return MysqlTransmittedQuery(study)


@pytest.fixture(scope='session')
def legacy_backend():
    from DAE import vDB
    study = vDB.get_study("w1202s766e611")
    return TransmissionLegacy(study, "old")


CADD_TRANSMITTED_QUERY = {
    'minParentsCalled': 0,
    'minAltFreqPrcnt': -1,
    'familyIds': None,
    'gender': None,
    'geneSyms': None,
    'limit': None,
    'genomicScores': [
        {
            'max': float('inf'),
            'metric': u'CADD_GS_raw',
            'min': 10.227635000000001
        }
    ],
    'presentInParent': [
        u'mother only'
    ],
    'regionS': ['1:1000000-10000000'],
    'effectTypes': ['nonsense', 'frame-shift', 'splice-site'],
    'inChild': None,
    'presentInChild': [u'neither'],
    'variantTypes': [u'sub', u'ins', u'del'],
    'ultraRareOnly': True,
    'TMM_ALL': False,
    'maxAltFreqPrcnt': -1
}


def test_mysql_cadd_query(mysql_backend):
    vs = mysql_backend.get_transmitted_variants(**CADD_TRANSMITTED_QUERY)
    vs = list(vs)

    assert len(vs) == 4


def test_legacy_cadd_query(legacy_backend):
    vs = legacy_backend.get_transmitted_variants(**CADD_TRANSMITTED_QUERY)
    vs = list(vs)

    assert len(vs) == 4
