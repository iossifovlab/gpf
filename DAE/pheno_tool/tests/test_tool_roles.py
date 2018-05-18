'''
Created on Nov 22, 2016

@author: lubo
'''
from __future__ import unicode_literals
from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role


def test_siblings(phdb, autism_candidates_genes, all_ssc_studies):

    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.sib],
        measure_id='vineland_ii.community_raw_score')
    res = tool.calc(
        VT(
            effect_types=['nonsynonymous', ],
            gene_syms=autism_candidates_genes,
            present_in_child=[
                'affected only', 'unaffected only', 'affected and unaffected'],
            present_in_parent=[
                'mother only', 'mother and father', 'neither'],
        )
    )

    for vals in list(res.phenotypes.values()):
        assert vals['role'] == Role.sib


def test_prb_or_sib(phdb, autism_candidates_genes, all_ssc_studies):

    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb, Role.sib],
        measure_id='vineland_ii.community_raw_score')
    res = tool.calc(
        VT(
            effect_types=['nonsynonymous', ],
            gene_syms=autism_candidates_genes,
            present_in_child=[
                'affected only', 'unaffected only', 'affected and unaffected'],
            present_in_parent=[
                'mother only', 'mother and father', 'neither'],
        )
    )

    for vals in list(res.phenotypes.values()):
        assert vals['role'] in set([Role.prb, Role.sib])
