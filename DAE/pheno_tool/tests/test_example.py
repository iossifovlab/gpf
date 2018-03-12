'''
Created on Nov 15, 2016

@author: lubo
'''
from DAE import vDB, pheno
from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role
from gene.gene_set_collections import GeneSetsCollection


def test_example_1():
    # load gene set
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_syms = gsc.get_gene_set('autism candidates from Iossifov PNAS 2015')

    studies = vDB.get_studies('ALL SSC')
    transmitted_study = vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)

    phdb = pheno.get_pheno_db('ssc')

    tool = PhenoTool(phdb, studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.head_circumference',
                     normalize_by=['pheno_common.age_at_assessment']
                     )

    res = tool.calc(
        VT(
            effect_types=['LGDs'],
            gene_syms=gene_syms,
            present_in_child=['affected only', 'affected and unaffected'],
            present_in_parent=['neither'],
        )
    )

    assert res is not None


def test_example_2():
    # load gene set
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_syms = gsc.get_gene_set('autism candidates from Iossifov PNAS 2015')

    studies = vDB.get_studies('ALL SSC')
    transmitted_study = vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)

    phdb = pheno.get_pheno_db('ssc')

    tool = PhenoTool(
        phdb, studies, roles=[Role.prb, Role.mom, Role.dad],
        measure_id='ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )

    res = tool.calc(
        VT(
            effect_types=['LGDs'],
            gene_syms=gene_syms,
            rarity='rare',
            rarity_max=10.0,
            present_in_child=['affected only', 'affected and unaffected'],
            present_in_parent=['father only', 'mother only',
                               'mother and father', 'neither'],
        )
    )

    assert res is not None
