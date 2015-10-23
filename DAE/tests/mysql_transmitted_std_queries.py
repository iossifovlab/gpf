'''
Created on Oct 15, 2015

@author: lubo
'''
from DAE import vDB, get_gene_sets_symNS
from transmitted.mysql_query import MysqlTransmittedQuery
from transmitted.legacy_query import TransmissionLegacy


def get_gene_set_syms(gene_set, gene_term):
    gt = get_gene_sets_symNS(gene_set)
    if gt and gene_term in gt.t2G:
            return gt.t2G[gene_term].keys()


def dae_query_q101():
    transmitted_study = vDB.get_study("w1202s766e611")
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        geneSyms=['CHD8'])

    res = [v for v in tvs]
    return res


def mysql_query_q101():
    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)
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
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        familyIds=['13785'])

    res = [v for v in tvs]
    return res


def mysql_query_q201():
    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)
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
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
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
    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)
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
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'])

    res = [v for v in tvs]
    return res


def mysql_query_q401():
    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)
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
    gene_syms = get_gene_set_syms('main', 'FMR1-targets')
    assert gene_syms

    transmitted_study = vDB.get_study("w1202s766e611")
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs',
        geneSyms=gene_syms)

    res = [v for v in tvs]
    return res


def mysql_query_q501():
    gene_syms = get_gene_set_syms('main', 'FMR1-targets')
    assert gene_syms

    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)
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
    impl = TransmissionLegacy(transmitted_study, "old")

    tvs = impl.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs',
        inChild='prb')

    res = [v for v in tvs]
    return res


def mysql_query_q601():
    transmitted_study = vDB.get_study("w1202s766e611")

    m = MysqlTransmittedQuery(transmitted_study)
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
