'''
Created on Nov 15, 2016

@author: lubo
'''
from DAE import get_gene_sets_symNS, vDB, pheno
from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role


def test_example_1():
    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

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
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['neither'],
        )
    )

    assert res is not None


def test_example_2():
    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

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
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['father only', 'mother only',
                               'mother and father', 'neither'],
        )
    )

    assert res is not None
