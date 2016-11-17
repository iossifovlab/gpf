'''
Created on Nov 9, 2016

@author: lubo
'''
import pytest
from pheno_tool.tool import PhenoTool, PhenoRequest
from pprint import pprint


def test_pheno_tool_create_default(phdb, default_request):
    assert default_request is not None

    tool = PhenoTool(phdb)
    assert tool is not None

    assert tool.phdb is not None


def test_build_families_variants(tool, default_request, genotype_helper):
    result = genotype_helper.get_families_variants(default_request)

    assert result is not None
    assert 390 == len(result)


def test_tool_calc(tool, default_request, genotype_helper):

    families_variants = genotype_helper.get_families_variants(default_request)

    r = tool.calc(
        families_variants,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )
    assert r is not None

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


def test_tool_present_in_parent_ultra_rare(tool, gene_set, genotype_helper):
    assert 239 == len(gene_set)

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        present_in_parent='mother only,father only,mother and father,neither',
        gene_syms=gene_set,
    )

    families_variants = genotype_helper.get_families_variants(pheno_request)

    r = tool.calc(
        families_variants,
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


def test_tool_present_in_parent_rare(tool, gene_set, genotype_helper):

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        gene_syms=gene_set,
        present_in_parent='mother only,father only,mother and father,neither',
        rarity='rare',
        rarity_max=10.0,
    )

    families_variants = genotype_helper.get_families_variants(pheno_request)

    r = tool.calc(
        families_variants,
        'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )
    assert r is not None

    male, female = male_female_result(r)

    assert 524 == male['positiveCount']
    assert 1859 == male['negativeCount']

    assert 114 == female['positiveCount']
    assert 260 == female['negativeCount']

    assert 0.04 == pytest.approx(male['pValue'], abs=1E-2)
    assert 0.3 == pytest.approx(female['pValue'], abs=1E-1)


def test_tool_present_in_parent_rarity_interval(
        tool, gene_set, genotype_helper):

    pheno_request = PhenoRequest(
        effect_type_groups=['LGDs'],
        gene_syms=gene_set,
        present_in_parent='mother only,father only,mother and father,neither',
        rarity='interval',
        rarity_max=10.0,
        rarity_min=5.0,
    )

    families_variants = genotype_helper.get_families_variants(pheno_request)

    r = tool.calc(
        families_variants,
        'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
    )
    assert r is not None

    male, female = male_female_result(r)

    assert 350 == male['positiveCount']
    assert 2033 == male['negativeCount']

    assert 84 == female['positiveCount']
    assert 290 == female['negativeCount']

    assert 0.02 == pytest.approx(male['pValue'], abs=1E-2)
    assert 0.5 == pytest.approx(female['pValue'], abs=1E-1)
