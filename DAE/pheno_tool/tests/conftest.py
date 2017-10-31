'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest

import DAE
from pheno_tool.family_filters import FamilyFilters
from pheno_tool.genotype_helper import GenotypeHelper
from pheno_tool.tool import PhenoFilterBuilder
from gene.gene_set_collections import GeneSetsCollection


@pytest.fixture(scope='session')
def phdb(request):
    pf = DAE.pheno
    db = pf.get_pheno_db('ssc')
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
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_set = gsc.get_gene_set('autism candidates from Iossifov PNAS 2015')
    return gene_set['syms']


@pytest.fixture(scope='session')
def all_ssc_studies(request):
    studies = DAE.vDB.get_studies('ALL SSC')
    assert studies is not None
    assert 7 == len(studies)
    transmitted_study = DAE.vDB.get_study('w1202s766e611')
    studies.append(transmitted_study)
    assert 8 == len(studies)
    return studies


@pytest.fixture(scope='session')
def autism_candidates_genes(request):
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_syms = gsc.get_gene_set('autism candidates from Iossifov PNAS 2015')
    return gene_syms['syms']


@pytest.fixture(scope='session')
def genotype_helper(request, all_ssc_studies):
    helper = GenotypeHelper(all_ssc_studies)
    return helper


@pytest.fixture(scope='session')
def filter_builder(request, phdb):
    builder = PhenoFilterBuilder(phdb)
    return builder
