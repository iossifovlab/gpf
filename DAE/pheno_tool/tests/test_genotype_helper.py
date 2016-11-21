'''
Created on Nov 16, 2016

@author: lubo
'''
from pprint import pprint
from pheno_tool.genotype_helper import GenotypeHelper, VariantTypes


def test_get_variants_denovo(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)
    assert 1 == len(helper.transmitted_studies)

    pheno_request = VariantTypes(
        effect_types='LGDs',
        gene_syms=autism_candidates_genes,
        present_in_child=['autism only', 'autism and unaffected'],
        present_in_parent=['neither'],
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 137 == len(variants)


def test_get_variants_father_ultra_rare(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        present_in_child=['autism only', 'autism and unaffected'],
        present_in_parent=['father only', 'mother and father', 'neither'],
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 176 == len(variants)


def test_get_variants_father_rarity(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        present_in_child=['autism only', 'autism and unaffected', 'neither'],
        present_in_parent=['father only', 'mother and father', 'neither'],
        rarity='rare',
        rarity_max=1.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 250 == len(variants)


def test_get_variants_father_interval(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        rarity='interval',
        rarity_max=50.0,
        rarity_min=1.0,
        present_in_child=['autism only', 'autism and unaffected', 'neither'],
        present_in_parent=['father only', 'mother and father', 'neither'],
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 593 == len(variants)


def test_get_single_gene_all(
        all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        gene_syms=['POGZ'],
        rarity='all',
        present_in_child=['autism only', 'autism and unaffected', 'neither'],
        present_in_parent=['father only', 'mother and father', 'neither'],

    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 6 == len(variants)


def test_get_single_gene_persons_variants_all(
        all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        gene_syms=['POGZ'],
        rarity='all',
        present_in_child=['autism only', 'autism and unaffected', 'neither'],
        present_in_parent=['father only', 'mother only',
                           'mother and father', 'neither'],
    )

    res = helper.get_persons_variants(pheno_request)
    pprint(res)
    assert 6 == len(res)


def test_get_persons_variants_denovo(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)
    assert 1 == len(helper.transmitted_studies)

    pheno_request = VariantTypes(
        effect_types=['LGDs'],
        present_in_child=['autism only', 'autism and unaffected'],
        present_in_parent=['neither'],
        gene_syms=autism_candidates_genes,
    )

    res = helper.get_persons_variants(pheno_request)
    assert 137 == len(res)


def test_get_person_variants_father_all(
        all_ssc_studies, autism_candidates_genes):

    helper = GenotypeHelper(all_ssc_studies)

    pheno_request = VariantTypes(
        effect_types='Frame-shift,Nonsense,Splice-site',
        gene_syms=autism_candidates_genes,
        rarity='rare',
        rarity_max=10.0,
        present_in_child=['autism only', 'autism and unaffected'],
        present_in_parent=['father only', 'mother and father', 'neither'],

    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 503 == len(variants)

    res = helper.get_persons_variants(pheno_request)
    assert 934 == len(res)
    assert 3 == max(res.values())
    ps3 = [p for (p, c) in res.items() if c == 3]
    assert 6 == len(ps3)

    assert '13528.p1' in ps3
    assert '13528.fa' in ps3

    assert '13216.p1' in ps3
    assert '13216.fa' in ps3
