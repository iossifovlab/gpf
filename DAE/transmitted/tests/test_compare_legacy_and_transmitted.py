'''
Created on May 22, 2017

@author: lubo
'''
# from pheno_tool.genotype_helper import VariantsType as VT
from DAE import vDB
from transmitted.legacy_query import TransmissionLegacy
from transmitted.mysql_query import MysqlTransmittedQuery
import pytest


# def test_get_variants_father_ultra_rare(
#         autism_candidates_genes, genotype_helper):
#
#     vs = genotype_helper.get_variants(
#         VT(
#             effect_types=['LGDs'],
#             gene_syms=autism_candidates_genes,
#             present_in_child=['affected only', 'affected and unaffected'],
#             present_in_parent=[
#                 'father only', 'mother and father', 'neither'],
#         )
#     )
#     variants = [v for v in vs]
#     assert 176 == len(variants)


@pytest.mark.mysql
def test_compare_father_ultra_rare(autism_candidates_genes):
    transmitted_study = vDB.get_study("w1202s766e611")

    query = {
        'minParentsCalled': -1,
        'maxAltFreqPrcnt': -1,
        'minAltFreqPrcnt': -1,
        'ultraRareOnly': True,
        'presentInChild': ['affected only', 'affected and unaffected'],
        'presentInParent': ['father only', 'mother and father'],
        'geneSyms': autism_candidates_genes,
        'effectTypes': [
            "frame-shift",
            "nonsense",
            "splice-site",
        ],
    }

    impl = TransmissionLegacy(transmitted_study, "old")
    tvs = impl.get_transmitted_variants(**query)
    lvs = [v for v in tvs]

    impl = MysqlTransmittedQuery(transmitted_study)
    tvs = impl.get_transmitted_variants(**query)
    mvs = [v for v in tvs]

    for v in mvs:
        assert 'dad' in v.fromParentS

    for v in lvs:
        assert 'dad' in v.fromParentS

    assert len(mvs) == len(lvs)
    assert len(mvs) == 39


@pytest.mark.mysql
def test_compare_father_rarity(autism_candidates_genes):
    transmitted_study = vDB.get_study("w1202s766e611")

    query = {
        'minParentsCalled': -1,
        'maxAltFreqPrcnt': 1.0,
        'minAltFreqPrcnt': -1,
        'presentInChild': ['affected only', 'affected and unaffected'],
        'presentInParent': ['father only', 'mother and father', 'neither'],
        'geneSyms': autism_candidates_genes,
        'effectTypes': [
            "frame-shift",
            "nonsense",
            "splice-site",
        ],
    }

    impl = TransmissionLegacy(transmitted_study, "old")
    tvs = impl.get_transmitted_variants(**query)
    lvs = [v for v in tvs]

    impl = MysqlTransmittedQuery(transmitted_study)
    tvs = impl.get_transmitted_variants(**query)
    mvs = [v for v in tvs]

    assert len(mvs) == len(lvs)
    assert len(mvs) == 73
