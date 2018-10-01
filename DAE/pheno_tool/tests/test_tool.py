'''
Created on Nov 9, 2016

@author: lubo
'''
from __future__ import unicode_literals

import pytest

from pheno_tool.tool import PhenoTool
from pheno_tool.genotype_helper import VariantsType as VT
from pheno.common import Role, Gender


def test_pheno_tool_create_default(phdb, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=[Role.prb],
                     measure_id='ssc_commonly_used.head_circumference')
    assert tool is not None

    assert tool.phdb is not None


@pytest.mark.slow
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

    # FIXME: changed after rennotation
    # assert 310 == male.positive_count
    assert 314 == male.positive_count
    # assert 2053 == male.negative_count
    assert 2049 == male.negative_count

    # assert 64 == female.positive_count
    assert 65 == female.positive_count
    assert 308 == female.negative_count

    assert -0.0354 == pytest.approx(male.positive_mean, abs=1E-4)
    assert 0.1208 == pytest.approx(male.negative_mean, abs=1E-4)

    assert 0.1616 == pytest.approx(male.pvalue, abs=1E-4)


def male_female_result(r):
    return r[Gender.M.name], r[Gender.F.name]


@pytest.mark.slow
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
            present_in_child=['affected only', 'affected and unaffected'],
            present_in_parent=['father only', 'mother only',
                               'mother and father', 'neither']
        ),
        gender_split=True,
    )
    assert r is not None

    male, female = male_female_result(r)

    # FIXME: changed after rennotation
    # assert 165 == male.positive_count
    assert 167 == male.positive_count
    # assert 2231 == male.negative_count
    assert 2229 == male.negative_count

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

    genotypes = r[Gender.M.name].genotypes
    assert 2363 == len(genotypes)
    assert 3 == max(genotypes.values())

    genotypes = r[Gender.F.name].genotypes
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

    phenotypes = r[Gender.M.name].phenotypes
    assert 2363 == len(phenotypes)

    phenotypes = r[Gender.F.name].phenotypes
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

    # FIXME: changed after rennotation
    # assert 374 == r.positive_count
    assert 379 == r.positive_count
    # assert 2362 == r.negative_count
    assert 2357 == r.negative_count
