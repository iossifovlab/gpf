'''
Created on Nov 9, 2016

@author: lubo
'''
import pytest
from pheno_tool.tool import PhenoTool, PhenoRequest


@pytest.fixture(scope='module')
def default_request(request):
    data = {
        'effect_type_groups': ['LGDs'],
        'in_child': 'prb',
        'present_in_parent': 'neither',
    }
    req = PhenoRequest(**data)
    return req


@pytest.fixture(scope='module')
def tool(request, measures):
    tool = PhenoTool(measures)
    return tool


def test_pheno_tool_create_default(measures, default_request):
    assert default_request is not None

    tool = PhenoTool(measures)
    assert tool is not None

    assert tool.measures is not None


def test_build_families_variants(tool, default_request):
    result = tool.build_families_variants(default_request)
    assert result is not None

    print(result)


def test_build_table_header(tool, default_request, head_circumference):
    head_circumference.normalize(['pheno_common.age'])

    result = tool.build_table_header(default_request, head_circumference)
    assert result is not None
    print(result)


def test_build_data_table(tool, default_request, head_circumference):
    head_circumference.normalize(['pheno_common.age'])

    result = tool.build_data_table(default_request, head_circumference)
    assert result is not None

    count = 0
    for _row in result:
        count += 1

    assert 2870 == count


def test_build_data_array(tool, default_request, head_circumference):
    head_circumference.normalize(['pheno_common.age'])

    result = tool.build_data_array(default_request, head_circumference)
    assert result is not None

    print(result)

    assert 2728 == len(result)


def test_tool_calc(tool, default_request):
    r = tool.calc(default_request,
                  'ssc_commonly_used.head_circumference',
                  normalized_by='pheno_common.age')
    assert r is not None
    print(r)

    if r[0]['gender'] == 'M':
        male = r[0]
        female = r[1]
    else:
        male = r[1]
        female = r[0]

    assert 'M' == male['gender']
    assert 'F' == female['gender']

    assert 310 == male['positiveCount']
    assert 2047 == male['negativeCount']

    assert 64 == female['positiveCount']
    assert 307 == female['negativeCount']

    assert -0.02620 == pytest.approx(male['positiveMean'], abs=1E-4)
    assert 0.11988 == pytest.approx(male['negativeMean'], abs=1E-4)

    assert 0.1933 == pytest.approx(male['pValue'], abs=1E-4)
