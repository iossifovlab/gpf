'''
Created on Jan 22, 2018

@author: lubo
'''
from variant_db.variant_query import VariantQuery
from DAE import vDB
from transmitted.tests.mysql_transmitted_std_queries import mysql_query_q101,\
    mysql_query_q201, mysql_query_q401
from transmitted.tests.variants_compare_base import VariantsCompareBase


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
    print("mysql_query_q401: {}".format(len(res)))
    return res


def test_count_sqlalchemy_query_q101():
    res = sqlalchemy_query_q101()
    assert res is not None

    assert len(res) == 5777


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
