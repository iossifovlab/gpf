'''
Created on Jan 22, 2018

@author: lubo
'''
from variant_db.variant_query import VariantQuery
from DAE import vDB
from transmitted.tests.mysql_transmitted_std_queries import mysql_query_q101,\
    mysql_query_q201, mysql_query_q401, get_gene_set_syms
from transmitted.tests.variants_compare_base import VariantsCompareBase
import time
from transmitted.mysql_query import MysqlTransmittedQuery


class Timer(object):
    def __init__(self, msg):
        self.start = None
        self.msg = msg

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = time.time()
        print("{}: time elapsed: {}s".format(self.msg, self.end - self.start))


def sqlalchemy_query_q101(limit=None):
    transmitted_study = vDB.get_study("variant_db")
    query = VariantQuery(transmitted_study)

    tvs = query.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['CHD8'],
        # effectTypes=['missense'],
        limit=limit)

    res = [v for v in tvs]
    print("sqlalchemy_query_q101: {}".format(len(res)))
    return res


def sqlalchemy_query_q201(limit=None):
    transmitted_study = vDB.get_study("variant_db")
    query = VariantQuery(transmitted_study)

    tvs = query.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        familyIds=['13785'],
        limit=limit)

    res = [v for v in tvs]
    print("sqlalchemy_query_q201: {}".format(len(res)))
    return res


def sqlalchemy_query_q401(limit=None):
    transmitted_study = vDB.get_study("variant_db")
    query = VariantQuery(transmitted_study)

    tvs = query.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        limit=limit)

    res = [v for v in tvs]
    print("sqlalchemy_query_q401: {}".format(len(res)))
    return res


def sqlalchemy_query_q501(limit=None):
    gene_syms = get_gene_set_syms('main', 'FMRP Tuschl')
    assert gene_syms

    gene_syms = set(gene_syms)
    print(len(gene_syms))
    # gene_syms = gene_syms - set(['INTS7'])
    print(len(gene_syms))

    transmitted_study = vDB.get_study("variant_db")
    query = VariantQuery(transmitted_study)

    tvs = query.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        geneSyms=list(gene_syms),
        limit=limit)

    res = [v for v in tvs]
    print("sqlalchemy_query_q501: {}".format(len(res)))
    return res


def test_count_sqlalchemy_query_q101():
    res = sqlalchemy_query_q101()
    assert res is not None

    assert len(res) == 5777


def mysql_query_q501_without_SRGAP2(limit=None):
    gene_syms = get_gene_set_syms('main', 'FMRP Tuschl')
    assert gene_syms

    print(len(gene_syms))
    gene_syms = gene_syms - set(['SRGAP2'])
    print(len(gene_syms))

    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        ultraRareOnly=True,
        effectTypes=['nonsense', 'frame-shift', 'splice-site'],
        geneSyms=list(gene_syms),
        limit=limit)

    res = [v for v in tvs]
    print("mysql_query_q501: {}".format(len(res)))
    return res


class Test(VariantsCompareBase):

    def test_compare_sqlalchemy_query_q101(self):
        res = sqlalchemy_query_q101()
        mres = mysql_query_q101()

        assert res is not None
        self.assertVariantsEquals(res, mres, "q101")

    def test_compare_sqlalchemy_query_q201(self):
        res = sqlalchemy_query_q201()
        mres = mysql_query_q201()

        assert res is not None
        self.assertVariantsEquals(res, mres, "q201")

    def test_compare_sqlalchemy_query_q401(self):
        res = sqlalchemy_query_q401()
        mres = mysql_query_q401()

        assert res is not None
        self.assertVariantsEquals(res, mres, "q401")

    def test_compare_sqlalchemy_query_q501(self):
        with Timer('sqlal q501') as _timeit:
            res = sqlalchemy_query_q501()
        with Timer('mysql q501') as _timeit:
            mres = mysql_query_q501_without_SRGAP2()

        self.assertVariantsEquals(res, mres, "q501")

# def test_sqlalchemy_debug_query_effect_no_duplicate():
#     transmitted_study = vDB.get_study("variant_db")
#     query = VariantQuery(transmitted_study)
#
#     tvs = query.get_transmitted_variants(
#         minParentsCalled=None,
#         maxAltFreqPrcnt=None,
#         minAltFreqPrcnt=None,
#         geneSyms=['CHD8'],
#         familyIds=['11198'],
#         # effectTypes=['intron'],
#         effectTypes=['missense', 'intron'],
#     )
#
#     res = [v for v in tvs]
#     print("")
#     for v in res:
#         print(v.atts)


def test_sqlalchemy_debug_query_genes():
    transmitted_study = vDB.get_study("w1202s766e611")
    m = MysqlTransmittedQuery(transmitted_study)

    tvs = m.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['SRGAP2'],
        effectTypes=['frame-shift', 'splice-site', 'nonsense'],
        ultraRareOnly=True,
    )

    res = [v for v in tvs]
    print("")
    for v in res:
        print(v.atts)

    transmitted_study = vDB.get_study("variant_db")
    query = VariantQuery(transmitted_study)

    tvs = query.get_transmitted_variants(
        minParentsCalled=None,
        maxAltFreqPrcnt=None,
        minAltFreqPrcnt=None,
        geneSyms=['SRGAP2'],
        effectTypes=['frame-shift', 'splice-site', 'nonsense'],
        ultraRareOnly=True,
    )

    res = [v for v in tvs]
    print("")
    for v in res:
        print(v.atts)
