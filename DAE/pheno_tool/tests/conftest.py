'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from pheno.pheno_db import PhenoDB
from pheno_tool.family_filters import FamilyFilters
from DAE import get_gene_sets_symNS, vDB
from pheno_tool.genotype_helper import GenotypeHelper


@pytest.fixture(scope='session')
def phdb(request):
    db = PhenoDB()
    db.load()
    return db


@pytest.fixture
def default_request(request):
    data = {
        'effect_types': ['LGDs'],
        'present_in_child': ['autism only', 'autism and unaffected'],
        'present_in_parent': ['neither'],
    }
    return data


@pytest.fixture(scope='session')
def family_filters(request, phdb):
    return FamilyFilters(phdb)


@pytest.fixture(scope='session')
def gene_set(request):
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()
    return gene_set


@pytest.fixture(scope='session')
def all_ssc_studies(request):
    studies = vDB.get_studies('ALL SSC')
    assert studies is not None
    assert 7 == len(studies)
    transmitted_study = vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)
    assert 8 == len(studies)
    return studies


@pytest.fixture(scope='session')
def autism_candidates_genes(request):
    gt = get_gene_sets_symNS('main')
    gene_syms = gt.t2G['autism candidates from Iossifov PNAS 2015'].keys()
    return gene_syms


@pytest.fixture(scope='session')
def genotype_helper(request, all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    return helper
