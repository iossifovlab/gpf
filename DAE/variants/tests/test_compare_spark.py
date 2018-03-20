'''
Created on Mar 20, 2018

@author: lubo
'''
from __future__ import print_function
from variants.vcf_utils import mat2str
from RegionOperations import Region
from variants.attributes import VariantType as VT
import pytest
from variant_annotation.multitool.adapters.old import OldVariantAnnotation
from variant_annotation.gene_codes import NuclearCode
import logging


@pytest.mark.slow
def test_compare_1_874817(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 874817, 874817)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    assert len(vl) == 2
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    [v1, v2] = vl
    assert v1.variant_type == VT.insertion
    assert v2.variant_type == VT.deletion


@pytest.mark.slow
def test_compare_1_889455(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 889455, 889455)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')
    assert len(vl) == 1
    [v1] = vl
    assert v1.variant_type == VT.substitution


@pytest.mark.slow
def test_compare_1_899910(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 899910, 899910)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    [v1, v2] = vl
    assert v1.variant_type == VT.deletion
    assert v2.variant_type == VT.deletion


@pytest.mark.slow
def test_compare_1_901972(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 901972, 901972)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    assert len(vl) == 1
    [v1] = vl
    assert v1.variant_type == VT.insertion
    assert v1.family_id == 'SF0007707'


@pytest.mark.slow
def test_compare_1_902133(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 902133, 902133)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    assert len(vl) == 1
    [v1] = vl
    assert v1.variant_type == VT.substitution
    assert v1.family_id == 'SF0003825'


@pytest.mark.slow
def test_compare_1_905958(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 905958, 905958)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    assert len(vl) == 1
    [v1] = vl
    assert v1.variant_type == VT.deletion
    assert v1.family_id == 'SF0010944'


@pytest.mark.slow
def test_compare_1_905970(nvcf19):
    vs = nvcf19.query_variants(
        regions=[Region('1', 905970, 905970)],
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')

    assert len(vl) == 1
    [v1] = vl
    assert v1.variant_type == VT.insertion
    assert v1.family_id == 'SF0010944'


@pytest.fixture(scope='session')
def old_annotator():
    from DAE import genomesDB
    genome = genomesDB.get_genome()  # @UndefinedVariable
    gene_models = genomesDB.get_gene_models()  # @UndefinedVariable

    annotator = OldVariantAnnotation(
        genome, gene_models, code=NuclearCode(), promoter_len=0)
    return annotator


@pytest.mark.slow
def test_compare_all_lgds_1_908275(nvcf19, old_annotator, effect_annotator):
    logging.basicConfig(level=logging.DEBUG)
    regions = [
        Region('1', 874817, 874817),
        Region('1', 889455, 889455),
        Region('1', 899910, 899910),
        Region('1', 901972, 901972),
        Region('1', 902133, 902133),
        Region('1', 905958, 905958),
        Region('1', 905970, 905970),
    ]
    vs = nvcf19.query_variants(
        regions=regions,
        inheritance='mendelian or denovo',
        # effect_types=['frame-shift', 'nonsense', 'splice-site']
    )
    vl = list(vs)
    for v in vl:
        print("")
        print(v, v.family_id, mat2str(v.best_st), v.inheritance,
              v.effect_type, v.effect_gene,
              v.get_attr('all.nAltAlls'), v.get_attr('all.altFreq'),
              sep='\t')
        _effects, desc = old_annotator.annotate_variant(
            chr=v.chromosome,
            position=v.position,
            var=v.variant)
        print("N:>", v.effect_type, v.effect_gene, v.effect_details)
        print("V:>", v.chromosome, v.start, v.reference, v.alt)
        for d in desc:
            print("E:>", d.effect_type, d.effect_details)

    assert len(vl) == 9
