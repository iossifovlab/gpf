'''
Created on Nov 9, 2016

@author: lubo
'''
import pytest
from pheno_tool.tool import PhenoTool


def test_pheno_tool_create_default(phdb, default_request):
    assert default_request is not None

    tool = PhenoTool(phdb)
    assert tool is not None

    assert tool.phdb is not None


def test_build_families_variants(tool, default_request):
    result = tool.build_families_variants(default_request)

    assert result is not None
    assert 'LGDs' in result
    assert 390 == len(result['LGDs'])


def test_tool_calc(tool, default_request):
    r = tool.calc(
        default_request,
        'ssc_commonly_used.head_circumference',
        normalize_by=['pheno_common.age']
    )
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
    assert 308 == female['negativeCount']

    assert -0.0260 == pytest.approx(male['positiveMean'], abs=1E-4)
    assert 0.1201 == pytest.approx(male['negativeMean'], abs=1E-4)

    assert 0.1933 == pytest.approx(male['pValue'], abs=1E-4)
