'''
Created on Aug 11, 2015

@author: lubo
'''
import unittest
from DAE import vDB
from query_prepare import prepare_gene_sets
from api.variants.hdf5_query import TransmissionQuery


def dae_query_q101():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        geneSyms='CHD8')

    res = [v for v in tvs]
    return res


def hdf_query_q101():
    tq = TransmissionQuery('w1202s766e611')
    tq['min_parents_called'] = None
    tq['max_alt_freq_prcnt'] = None
    tq['min_alt_freq_prcnt'] = None
    tq['gene_syms'] = ['CHD8']

    res = tq.get_variants()
    return res


def dae_query_q201():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        familyIds='13785')

    res = [v for v in tvs]
    return res


def dae_query_q202():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        familyIds='13785',
        TMM_ALL=True)

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
        familyIds='13785')

    res = [v for v in tvs]
    return res


def hdf_query_q301():
    tq = TransmissionQuery('w1202s766e611')
    tq['min_parents_called'] = None
    tq['max_alt_freq_prcnt'] = 1.0
    tq['min_alt_freq_prcnt'] = None
    tq['ultra_rare_only'] = True
    tq['effect_types'] = ['splice-site', 'frame-shift', 'nonsense',
                          'no-frame-shift-newStop',
                          'noStart', 'noEnd', 'missense',
                          'no-frame-shift']
    tq['family_ids'] = ['13785']

    res = tq.get_variants()
    return res


def dae_query_q401():
    transmitted_study = vDB.get_study("w1202s766e611")
    tvs = transmitted_study.get_transmitted_variants(
        minParentsCalled=-1,
        maxAltFreqPrcnt=-1,
        minAltFreqPrcnt=-1,
        ultraRareOnly=True,
        effectTypes='LGDs')

    res = [v for v in tvs]
    return res


def hdf_query_q401():
    tq = TransmissionQuery('w1202s766e611')
    tq['min_parents_called'] = None
    tq['max_alt_freq_prcnt'] = None
    tq['min_alt_freq_prcnt'] = None
    tq['ultra_rare_only'] = True
    tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']

    res = tq.get_variants()
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


def dae_query_q502():
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
        geneSyms=list(gene_syms)[:200])

    res = [v for v in tvs]
    return res


def hdf_query_q502():
    gene_syms = list(prepare_gene_sets({'geneSet': 'main',
                                        'geneTerm': 'FMR1-targets'}))
    print gene_syms
    assert gene_syms
    assert isinstance(gene_syms, list)

    tq = TransmissionQuery('w1202s766e611')
    tq['min_parents_called'] = None
    tq['max_alt_freq_prcnt'] = None
    tq['min_alt_freq_prcnt'] = None
    tq['ultra_rare_only'] = True
    tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
    tq['gene_syms'] = gene_syms[:200]
    res = tq.get_variants()
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


def hdf_query_q601():
    tq = TransmissionQuery('w1202s766e611')
    tq['min_parents_called'] = None
    tq['max_alt_freq_prcnt'] = None
    tq['min_alt_freq_prcnt'] = None
    tq['ultra_rare_only'] = True
    tq['effect_types'] = ['nonsense', 'frame-shift', 'splice-site']
    tq['present_in_child'] = ['prb']
    res = tq.get_variants()
    return res


# def dae_query_q201():
#     transmitted_study = vDB.get_study("w1202s766e611")
#     tvs = transmitted_study.get_transmitted_variants(
#         minParentsCalled=-1,
#         maxAltFreqPrcnt=-1,
#         minAltFreqPrcnt=-1,
#         familyIds='13785')
#
#     res = [v for v in tvs]
#     return res
#
#
# def dae_query_q202():
#     transmitted_study = vDB.get_study("w1202s766e611")
#     tvs = transmitted_study.get_transmitted_variants(
#         minParentsCalled=-1,
#         maxAltFreqPrcnt=-1,
#         minAltFreqPrcnt=-1,
#         familyIds='13785',
#         TMM_ALL=True)
#
#     res = [v for v in tvs]
#     return res
#
#
# def dae_query_q301():
#     transmitted_study = vDB.get_study("w1202s766e611")
#     tvs = transmitted_study.get_transmitted_variants(
#         minParentsCalled=-1,
#         maxAltFreqPrcnt=1.0,
#         minAltFreqPrcnt=-1,
#         familyIds='13785')
#
#     res = [v for v in tvs]
#     return res
#
#


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testName(self):
        pass

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
