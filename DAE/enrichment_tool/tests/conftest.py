'''
Created on Nov 8, 2016

@author: lubo
'''
import pytest
from DAE import vDB
from datasets.config import DatasetsConfig
from datasets.datasets_factory import DatasetsFactory
from enrichment_tool.background import SamochaBackground
from gene.gene_set_collections import GeneSetsCollection


@pytest.fixture(scope='session')
def gene_set(request):
    # gt = get_gene_sets_symNS('main')
    # gene_set = gt.t2G['chromatin modifiers'].keys()
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_set = gsc.get_gene_set('chromatin modifiers')

    return gene_set['syms']


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


# @pytest.fixture(scope='module')
# def children_stats(request):
#     denovo_studies = DenovoStudies()
#     return ChildrenStats.build(denovo_studies)


@pytest.fixture(scope='session')
def datasets_config(request):
    return DatasetsConfig()


@pytest.fixture(scope='session')
def datasets_factory(request, datasets_config):
    return DatasetsFactory(datasets_config)


@pytest.fixture(scope='session')
def ssc(request, datasets_factory):
    return datasets_factory.get_dataset('SSC')


@pytest.fixture(scope='session')
def vip(request,  datasets_factory):
    return datasets_factory.get_dataset('VIP')


@pytest.fixture(scope='session')
def sd(request,  datasets_factory):
    return datasets_factory.get_dataset('SD')


@pytest.fixture(scope='module')
def samocha_background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg
