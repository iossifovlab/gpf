'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from DAE import get_gene_sets_symNS, vDB
from enrichment_tool.config import DenovoStudies, ChildrenStats


@pytest.fixture(scope='module')
def gene_set(request):
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()
    return gene_set


@pytest.fixture(scope='session')
def denovo_studies(request):
    studies = vDB.get_studies('ALL WHOLE EXOME')
    return [st for st in studies if 'WE' == st.get_attr('study.type')]


@pytest.fixture(scope='session')
def autism_studies(request, denovo_studies):
    return [st for st in denovo_studies
            if 'autism' == st.get_attr('study.phenotype')]


@pytest.fixture(scope='session')
def schizophrenia_studies(request, denovo_studies):
    return [st for st in denovo_studies
            if 'schizophrenia' == st.get_attr('study.phenotype')]


@pytest.fixture(scope='session')
def unaffected_studies(request, denovo_studies):
    return denovo_studies


@pytest.fixture(scope='module')
def children_stats(request):
    denovo_studies = DenovoStudies()
    return ChildrenStats.build(denovo_studies)
