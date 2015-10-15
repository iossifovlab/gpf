'''
Created on Oct 15, 2015

@author: lubo
'''
from DAE import vDB
from transmitted.mysql_query import MysqlTransmittedQuery


def dae_query_q101():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
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


def mysql_query_q101():
    m = MysqlTransmittedQuery(vDB, 'w1202s766e611')
    tvs = m.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        geneSyms=['CHD8'])

    res = [v for v in tvs]
    return res


if __name__ == "__main__":
    import timeit
    t = timeit.Timer('dae_query_q101()',
                     setup="from __main__ import dae_query_q101")
    print("dae_query_q101: {}".format(t.timeit(3)))

    t = timeit.Timer('dae_query_q201()',
                     setup="from __main__ import dae_query_q201")
    print("dae_query_q201: {}".format(t.timeit(3)))
