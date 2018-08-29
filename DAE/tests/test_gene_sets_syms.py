'''
Created on Feb 28, 2018

@author: lubo
'''
from DAE import get_gene_sets_symNS
from DAE import vDB
from VariantAnnotation import get_effect_types_set


def test_gene_sets_sym_main():
    main_sets = get_gene_sets_symNS('main')
    assert main_sets is not None
    print(main_sets.t2G.keys())
    assert "autism candidates from Iossifov PNAS 2015" in main_sets.t2G


def test_gene_sets_sym_denovo():
    group = vDB.get_study_group('ALL WHOLE EXOME')
    studies = vDB.get_studies(",".join(group.studyNames))
    assert len(studies) == 17

    denovo_sets = get_gene_sets_symNS('denovo', studies)
    assert denovo_sets is not None
    print(denovo_sets.t2G.keys())
    assert len(denovo_sets.t2G.keys()) == 13


def test_get_effect_types_set():
    eff = get_effect_types_set("splice-site")
    assert eff is not None

    assert len(eff) == 1

    eff = get_effect_types_set('nonsynonymous')
    assert len(eff) == 9
