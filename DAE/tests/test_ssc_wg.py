'''
Created on Nov 22, 2016

@author: lubo
'''
from DAE import vDB
import pytest
from transmitted.mysql_query import MysqlTransmittedQuery
import time


@pytest.fixture(scope='session')
def wg_study(request):
    study = vDB.get_study('SSC_WG_510')
    return study


def test_wg_lgds():
    study = vDB.get_study('SSC_WG_510')
    assert study is not None

    assert study.has_transmitted


def test_get_single_gene_lgds(wg_study):
    start = time.time()
    m = MysqlTransmittedQuery(wg_study)

    vs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['CHD8'],
    )
    res = [v for v in vs]
    assert 18884 == len(res)

    print(": {}s (count={})".format(
        time.time() - start, len(res)))


def test_get_rare_lgds_for_family_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop'],
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 75 == len(res)

    print(": {}s (count={})".format(
        time.time() - start, len(res)))


def test_get_ultra_rare_lgds_for_family_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense', ],
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 44 == len(res)

    print(": {}s (count={})".format(
        time.time() - start, len(res)))


def test_get_ultra_rare_lgds_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense', ],
    )

    res = [v for v in vs]
    assert 10228 == len(res)

    print(": {}s (count={})".format(
        time.time() - start, len(res)))


def test_get_family_ultra_rare_variants(wg_study):
    start = time.time()
    vs = wg_study.get_transmitted_variants(
        minParentsCalled=None,
        ultraRareOnly=True,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13884'],
    )

    res = [v for v in vs]
    assert 141213 == len(res)

    print(": {}s (count={})".format(
        time.time() - start, len(res)))
