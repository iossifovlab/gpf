'''
Created on Nov 9, 2016

@author: lubo
'''

import pytest

from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role, Gender


def test_pheno_tool_create_default(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.head_circumference')
    assert tool is not None

    assert tool.phdb is not None


def test_tool_calc(phdb, all_ssc_studies, default_request):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.head_circumference',
                     normalize_by=['pheno_common.age_at_assessment'],)

    r = tool.calc(
        VT(**default_request),
        gender_split=True,
    )
    assert r is not None

    male, female = male_female_result(r)

    assert 310 == male.positive_count
    assert 2053 == male.negative_count

    assert 64 == female.positive_count
    assert 309 == female.negative_count

    assert -0.0246 == pytest.approx(male.positive_mean, abs=1E-4)
    assert 0.1189 == pytest.approx(male.negative_mean, abs=1E-4)

    assert 0.2007 == pytest.approx(male.pvalue, abs=1E-4)


def male_female_result(r):
    return r[Gender.M], r[Gender.F]


def test_tool_present_in_parent_ultra_rare(
        phdb, all_ssc_studies, gene_set):

    tool = PhenoTool(
        phdb, all_ssc_studies,
        roles=[Role.prb, Role.mom, Role.dad],
        measure_id='ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )

    r = tool.calc(
        VT(
            effect_types=['LGDs'],
            gene_syms=gene_set,
            present_in_child=['autism only', 'autism and unaffected'],
            present_in_parent=['father only', 'mother only',
                               'mother and father', 'neither']
        ),
        gender_split=True,
    )
    assert r is not None

    male, female = male_female_result(r)

    assert 165 == male.positive_count
    assert 2231 == male.negative_count

    assert 47 == female.positive_count
    assert 329 == female.negative_count

    assert 0.00002 == pytest.approx(male.pvalue, abs=1E-5)
    assert 0.2 == pytest.approx(female.pvalue, abs=1E-1)


def test_genotypes(phdb, all_ssc_studies, default_request):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.head_circumference',
                     normalize_by=['pheno_common.age_at_assessment'],)

    r = tool.calc(
        VT(**default_request),
        gender_split=True,
    )

    genotypes = r[Gender.M].genotypes
    assert 2363 == len(genotypes)
    assert 3 == max(genotypes.values())

    genotypes = r[Gender.F].genotypes
    assert 373 == len(genotypes)
    assert 3 == max(genotypes.values())


def test_phenotypes(phdb, all_ssc_studies, default_request):
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
    )

    r = tool.calc(
        VT(**default_request),
        gender_split=True,
    )

    phenotypes = r[Gender.M].phenotypes
    assert 2363 == len(phenotypes)

    phenotypes = r[Gender.F].phenotypes
    assert 373 == len(phenotypes)


def test_gender_split_false(phdb, all_ssc_studies, default_request):
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=[Role.prb],
        measure_id='ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age_at_assessment'],
    )

    r = tool.calc(
        VT(**default_request),
        gender_split=False,
    )

    assert 374 == r.positive_count
    assert 2362 == r.negative_count
