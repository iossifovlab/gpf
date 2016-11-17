'''
Created on Nov 16, 2016

@author: lubo
'''
from pprint import pprint
from pheno_tool.tool import PhenoTool, PhenoRequest


def test_get_variants_denovo(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    assert 1 == len(helper.transmitted_studies)

    pheno_request = PhenoRequest(
        effect_types='LGDs',
        gene_syms=autism_candidates_genes,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 137 == len(variants)


def test_get_variants_father_ultra_rare(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'dad'])

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 185 == len(variants)


def test_get_variants_father_rarity(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'dad'])

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        rarity='rare',
        rarity_max=1.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 250 == len(variants)


def test_get_variants_father_interval(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'dad'])

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=autism_candidates_genes,
        rarity='interval',
        rarity_max=50.0,
        rarity_min=1.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 593 == len(variants)


def test_get_single_gene_all(phdb, all_ssc_studies):
    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'dad'])
    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=['POGZ'],
        rarity='all',
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 6 == len(variants)


def test_get_single_gene_persons_variants_all(phdb, all_ssc_studies):
    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'mom', 'dad'])
    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=['POGZ'],
        rarity='all',
    )

    res = helper.get_persons_variants(pheno_request)
    pprint(res)
    assert 6 == len(res)


def test_get_persons_variants_denovo(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    assert 1 == len(helper.transmitted_studies)

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        #         in_child='prb',
        #         present_in_parent='neither',
        gene_syms=autism_candidates_genes,
    )

    res = helper.get_persons_variants(pheno_request)
    assert 137 == len(res)


def test_get_person_variants_father_all(
        phdb, all_ssc_studies, autism_candidates_genes):

    helper = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'dad'])

    pheno_request = PhenoRequest(
        effect_types='Frame-shift,Nonsense,Splice-site',
        gene_syms=autism_candidates_genes,
        rarity='rare',
        rarity_max=10.0,
    )

    variants = [v for v in helper.get_variants(pheno_request)]
    assert 683 == len(variants)

    res = helper.get_persons_variants(pheno_request)
    assert 1081 == len(res)
    assert 4 == max(res.values())
    ps3 = [p for (p, c) in res.items() if c == 3]
    assert 12 == len(ps3)

    assert '13528.p1' in ps3
    assert '13528.fa' in ps3

    assert '13216.p1' in ps3
    assert '13216.fa' in ps3
