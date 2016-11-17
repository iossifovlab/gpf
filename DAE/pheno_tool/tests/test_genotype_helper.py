'''
Created on Nov 16, 2016

@author: lubo
'''
from pheno_tool.genotype_helper import GenotypeHelper, PhenoRequest
from pprint import pprint


def test_get_variants_denovo(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)
    assert 1 == len(helper.transmitted_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither',
        gene_syms=autism_candidates_genes,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 137 == len(variants)


def test_get_variants_father_ultra_rare(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither,father only',
        gene_syms=autism_candidates_genes,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 176 == len(variants)


def test_get_variants_father_rarity(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither,father only',
        gene_syms=autism_candidates_genes,
        rarity='rare',
        rarity_max=1.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 196 == len(variants)


def test_get_variants_father_interval(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither,father only',
        gene_syms=autism_candidates_genes,
        rarity='interval',
        rarity_max=50.0,
        rarity_min=1.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 366 == len(variants)


def test_get_single_gene_all(all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    pheno_request = PhenoRequest(
        in_child=None,
        present_in_parent=[
            'neither',
            'father only',
            'mother only',
            'mother and father'],
        gene_syms=['POGZ'],
        rarity='all',
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 6 == len(variants)


def test_get_single_gene_persons_variants_all(all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    pheno_request = PhenoRequest(
        in_child=None,
        present_in_parent=[
            'neither',
            'father only',
            'mother only',
            'mother and father'],
        gene_syms=['POGZ'],
        rarity='all',
    )

    res = helper.get_persons_variants(pheno_request)
    pprint(res)
    assert 6 == len(res)


def test_get_persons_variants_denovo(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)
    assert 1 == len(helper.transmitted_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither',
        gene_syms=autism_candidates_genes,
    )

    res = helper.get_persons_variants(pheno_request)
    assert 137 == len(res)


def test_get_person_variants_father_all(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        in_child='prb',
        present_in_parent='neither,father only',
        gene_syms=autism_candidates_genes,
        rarity='all',
    )

    res = helper.get_persons_variants(pheno_request)
    assert 704 == len(res)
    assert 3 == max(res.values())
    ps3 = [p for (p, c) in res.items() if c == 3]
    assert 6 == len(ps3)

    assert '13528.p1' in ps3
    assert '13528.fa' in ps3

    assert '13216.p1' in ps3
    assert '13216.fa' in ps3
