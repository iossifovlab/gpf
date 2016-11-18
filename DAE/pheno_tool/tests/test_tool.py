'''
Created on Nov 9, 2016

@author: lubo
'''
from pprint import pprint

import pytest

from pheno_tool.tool import PhenoTool, PhenoRequest


def test_pheno_tool_create_default(phdb, all_ssc_studies, default_request):
    assert default_request is not None

    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    assert tool is not None

    assert tool.phdb is not None


def test_build_families_variants(phdb, default_request, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])
    result = tool.get_families_variants(default_request)

    assert result is not None
    assert 390 == len(result)


def test_tool_calc(phdb, default_request, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])

    r = tool.calc(
        default_request,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )
    assert r is not None
    print(r)

    male, female = male_female_result(r)

    assert 'M' == male.gender
    assert 'F' == female.gender

    assert 310 == male.positive_count
    assert 2047 == male.negative_count

    assert 64 == female.positive_count
    assert 308 == female.negative_count

    assert -0.0260 == pytest.approx(male.positive_mean, abs=1E-4)
    assert 0.1201 == pytest.approx(male.negative_mean, abs=1E-4)

    assert 0.1933 == pytest.approx(male.pvalue, abs=1E-4)


def male_female_result(r):
    if r[0].gender == 'M':
        male = r[0]
        female = r[1]
    else:
        male = r[1]
        female = r[0]
    return male, female


def test_tool_present_in_parent_ultra_rare(phdb, gene_set, all_ssc_studies):
    assert 239 == len(gene_set)

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=gene_set,
    )
    tool = PhenoTool(
        phdb, all_ssc_studies, roles=['prb', 'mom', 'dad'])

    r = tool.calc(
        pheno_request,
        'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )
    assert r is not None
    pprint(r)

    male, female = male_female_result(r)

    assert 165 == male.positive_count
    assert 2218 == male.negative_count

    assert 47 == female.positive_count
    assert 327 == female.negative_count

    assert 0.00002 == pytest.approx(male.pvalue, abs=1E-5)
    assert 0.2 == pytest.approx(female.pvalue, abs=1E-1)


def test_genotypes(phdb, default_request, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])

    r = tool.calc(
        default_request,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )

    genotypes = r[0].genotypes
    assert 2357 == len(genotypes)
    assert 3 == max(genotypes.values())

    genotypes = r[1].genotypes
    assert 372 == len(genotypes)
    assert 3 == max(genotypes.values())


def test_phenotypes(phdb, default_request, all_ssc_studies):
    tool = PhenoTool(phdb, all_ssc_studies, roles=['prb'])

    r = tool.calc(
        default_request,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )

    phenotypes = r[0].phenotypes
    assert 2357 == len(phenotypes)
    # assert 3 == max(genotypes.values())

    phenotypes = r[1].phenotypes
    assert 372 == len(phenotypes)
    # assert 3 == max(genotypes.values())

    pprint(phenotypes)
