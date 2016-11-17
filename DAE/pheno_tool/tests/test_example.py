'''
Created on Nov 15, 2016

@author: lubo
'''
from DAE import get_gene_sets_symNS, vDB
from pheno.pheno_db import PhenoDB
from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import GenotypeHelper, PhenoRequest


def test_example_1():
    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

    studies = vDB.get_studies('ALL SSC')
    transmitted_study = vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)

    phdb = PhenoDB()
    phdb.load()

    tool = PhenoTool(phdb)

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=gene_syms,
    )

    genotype_helper = GenotypeHelper(studies, roles=['prb'])
    families_variants = genotype_helper.get_families_variants(pheno_request)

    res = tool.calc(
        families_variants,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age'])

    print(res)
    #     [
    #         {
    #             'effectType': 'LGDs',
    #             'gender': 'M',
    #             'positiveCount': 98,
    #             'negativeCount': 2259,
    #             'positiveMean': -0.24415336174389424,
    #             'negativeMean': 0.11582221729709602,
    #             'positiveDeviation': 0.39541204342235059,
    #             'negativeDeviation': 0.075602233503285168,
    #             'pValue': 0.058240764767345257,
    #         },
    #         {
    #             'effectType': 'LGDs',
    #             'gender': 'F',
    #             'positiveCount': 34,
    #             'negativeCount': 338,
    #             'positiveMean': -0.79135045607117627,
    #             'negativeMean': -0.62369657963543668,
    #             'positiveDeviation': 0.78261262906505169,
    #             'negativeDeviation': 0.22346514664220996,
    #             'pValue': 0.66113586273086755,
    #         }
    #     ]


def test_example_2():
    # load gene set
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()

    studies = vDB.get_studies('ALL SSC')
    transmitted_study = vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)

    phdb = PhenoDB()
    phdb.load()

    tool = PhenoTool(phdb)

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=gene_syms,
        rarity='rare',
        rarity_max=10.0,
    )

    genotype_helper = GenotypeHelper(studies, roles=['prb', 'mom', 'dad'])
    families_variants = genotype_helper.get_families_variants(pheno_request)

    res = tool.calc(
        families_variants,
        'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )

    print(res)
    #     [
    #         {
    #             'effectType': 'LGDs',
    #             'gender': 'M',
    #             'positiveCount': 524,
    #             'negativeCount': 1859,
    #             'positiveMean': 83.496183206106863,
    #             'negativeMean': 86.147391070467989,
    #             'positiveDeviation': 2.1420548304730307,
    #             'negativeDeviation': 1.1934784184591305,
    #             'pValue': 0.039335912517152301,
    #         },
    #         {
    #             'effectType': 'LGDs',
    #             'gender': 'F',
    #             'positiveCount': 114,
    #             'negativeCount': 260,
    #             'positiveMean': 79.982456140350877,
    #             'negativeMean': 77.115384615384613,
    #             'positiveDeviation': 4.6735815772196778,
    #             'negativeDeviation': 3.1995644483398933,
    #             'pValue': 0.32934600678855175,
    #         }
    #     ]
