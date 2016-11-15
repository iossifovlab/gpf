'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from pheno.pheno_db import PhenoDB
from pheno_tool.tool import PhenoTool, PhenoRequest
from pheno_tool.family_filters import FamilyFilters
from DAE import get_gene_sets_symNS


@pytest.fixture(scope='session')
def phdb(request):
    db = PhenoDB()
    db.load()
    return db


@pytest.fixture
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


@pytest.fixture(scope='session')
def family_filters(request, phdb):
    return FamilyFilters(phdb)


@pytest.fixture(scope='session')
def gene_set(request):
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()
    return gene_set
