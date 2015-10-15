'''
Created on Oct 15, 2015

@author: lubo
'''
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery
from query_prepare import prepare_gene_sets


def dae_query_q101():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        geneSyms=['CHD8'])

    res = [v for v in tvs]
    return res


def mysql_query_q101():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['CHD8'])

    res = [v for v in tvs]
    return res


def dae_query_q201():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        familyIds=['13785'])

    res = [v for v in tvs]
    return res


def mysql_query_q201():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13785'])

    res = [v for v in tvs]
    return res


def dae_query_q301():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=-1,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop',
                     'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS'],
        familyIds=['13785'])

    res = [v for v in tvs]
    return res


def mysql_query_q301():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=1.0,
        minAltFreqPrcnt=None,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop',
                     'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS'],
        familyIds=['13785'])

    res = [v for v in tvs]
    return res


def dae_query_q401():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'])

    res = [v for v in tvs]
    return res


def mysql_query_q401():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'])

    res = [v for v in tvs]
    return res


def dae_query_q501():
    gene_syms = prepare_gene_sets({'geneSet': 'main',
                                   'geneTerm': 'FMR1-targets'})
    assert gene_syms

    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs',
        geneSyms=gene_syms)

    res = [v for v in tvs]
    return res


def mysql_query_q501():
    gene_syms = prepare_gene_sets({'geneSet': 'main',
                                   'geneTerm': 'FMR1-targets'})
    assert gene_syms

    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        geneSyms=list(gene_syms))

    res = [v for v in tvs]
    return res


def dae_query_q601():

    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs',
        inChild='prb')

    res = [v for v in tvs]
    return res


def mysql_query_q601():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    m.connect()
    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['splice-site', 'frame-shift', 'nonsense',
                     'no-frame-shift-newStop'],
        inChild='prb')

    res = [v for v in tvs]
    return res
