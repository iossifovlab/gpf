'''
Created on Nov 22, 2016

@author: lubo
'''
from pheno_tool.genotype_helper import GenotypeHelper
from pheno_tool.tool import PhenoTool


def test_siblings(phdb, autism_candidates_genes, all_ssc_studies):
    genotype_helper = GenotypeHelper(all_ssc_studies)
    person_variants = genotype_helper.get_persons_variants(
        effect_types=['nonsynonymous', ],
        gene_syms=autism_candidates_genes,
        present_in_child=[
            'autism only', 'unaffected only', 'autism and unaffected'],
        present_in_parent=[
            'mother only', 'mother and father', 'neither'],
    )

    tool = PhenoTool(phdb, roles=['sib'])
    res = tool.calc(
        person_variants,
        'vineland_ii.community_raw_score')
    print(res)

    for vals in res.phenotypes.values():
        assert vals['role'] == 'sib'


def test_prb_or_sib(phdb, autism_candidates_genes, all_ssc_studies):
    genotype_helper = GenotypeHelper(all_ssc_studies)
    person_variants = genotype_helper.get_persons_variants(
        effect_types=['nonsynonymous', ],
        gene_syms=autism_candidates_genes,
        present_in_child=[
            'autism only', 'unaffected only', 'autism and unaffected'],
        present_in_parent=[
            'mother only', 'mother and father', 'neither'],
    )

    tool = PhenoTool(phdb, roles=['prb', 'sib'])
    res = tool.calc(
        person_variants,
        'vineland_ii.community_raw_score')
    print(res)

    for vals in res.phenotypes.values():
        assert vals['role'] in set(['prb', 'sib'])
