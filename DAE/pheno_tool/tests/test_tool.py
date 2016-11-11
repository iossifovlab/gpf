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
