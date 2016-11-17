'''
Created on Nov 9, 2016

@author: lubo
'''
from pprint import pprint

import pytest

from pheno_tool.genotype_helper import PhenoRequest, GenotypeHelper
from pheno_tool.tool import PhenoTool


def test_pheno_tool_create_default(phdb, default_request):
    assert default_request is not None

    tool = PhenoTool(phdb)
    assert tool is not None

    assert tool.phdb is not None


def test_build_families_variants(tool, default_request, genotype_helper):
    result = genotype_helper.get_families_variants(default_request)

    assert result is not None
    assert 390 == len(result)


def test_tool_calc(tool, default_request, all_ssc_studies):
    genotype_helper = GenotypeHelper(all_ssc_studies, roles=['prb'])
    persons_variants = genotype_helper.get_persons_variants(default_request)

    r = tool.calc(
        persons_variants,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )
    assert r is not None
    print(r)

    male, female = male_female_result(r)

    assert 'M' == male['gender']
    assert 'F' == female['gender']

    assert 310 == male['positiveCount']
    assert 2047 == male['negativeCount']

    assert 64 == female['positiveCount']
    assert 308 == female['negativeCount']

    assert -0.0260 == pytest.approx(male['positiveMean'], abs=1E-4)
    assert 0.1201 == pytest.approx(male['negativeMean'], abs=1E-4)

    assert 0.1933 == pytest.approx(male['pValue'], abs=1E-4)


def male_female_result(r):
    if r[0]['gender'] == 'M':
        male = r[0]
        female = r[1]
    else:
        male = r[1]
        female = r[0]
    return male, female


def test_tool_present_in_parent_ultra_rare(tool, gene_set, all_ssc_studies):
    assert 239 == len(gene_set)

    pheno_request = PhenoRequest(
        effect_types=['LGDs'],
        gene_syms=gene_set,
    )
    genotype_helper = GenotypeHelper(
        all_ssc_studies, roles=['prb', 'mom', 'dad'])
    persons_variants = genotype_helper.get_persons_variants(pheno_request)

    r = tool.calc(
        persons_variants,
        'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )
    assert r is not None
    pprint(r)

    male, female = male_female_result(r)

    assert 165 == male['positiveCount']
    assert 2218 == male['negativeCount']

    assert 47 == female['positiveCount']
    assert 327 == female['negativeCount']

    assert 0.00002 == pytest.approx(male['pValue'], abs=1E-5)
    assert 0.2 == pytest.approx(female['pValue'], abs=1E-1)
