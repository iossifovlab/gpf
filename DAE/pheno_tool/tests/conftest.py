'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from pheno.pheno_db import PhenoDB
from pheno_tool.tool import PhenoTool, PhenoRequest


@pytest.fixture(scope='session')
def phdb(request):
    db = PhenoDB()
    db.load()
    return db


@pytest.fixture(scope='session')
def default_request(request):
    data = {
        'effect_type_groups': ['LGDs'],
        'in_child': 'prb',
        'present_in_parent': 'neither',
    }
    req = PhenoRequest(**data)
    return req


@pytest.fixture(scope='session')
def tool(request, phdb):
    tool = PhenoTool(phdb)
    return tool
