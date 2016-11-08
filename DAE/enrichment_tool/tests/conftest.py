'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from DAE import get_gene_sets_symNS
from enrichment_tool.config import DenovoStudies, ChildrenStats


@pytest.fixture(scope='module')
def gene_set(request):
    gt = get_gene_sets_symNS('main')
    gene_set = gt.t2G['chromatin modifiers'].keys()
    return gene_set


@pytest.fixture(scope='module')
def denovo_studies(request):
    return DenovoStudies()


@pytest.fixture(scope='module')
def children_stats(request):
    denovo_studies = DenovoStudies()
    return ChildrenStats.build(denovo_studies)
