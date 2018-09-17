'''
Created on Nov 8, 2016

@author: lubo
'''
from __future__ import unicode_literals
import pytest
from DAE import vDB
from datasets.config import DatasetsConfig
from datasets.datasets_factory import DatasetsFactory
from enrichment_tool.background import SamochaBackground, SynonymousBackground
from gene.gene_set_collections import GeneSetsCollection


@pytest.fixture(scope='session')
def gene_set():
    # gt = get_gene_sets_symNS('main')
    # gene_set = gt.t2G['chromatin modifiers'].keys()
    gsc = GeneSetsCollection('main')
    gsc.load()
    gene_set = gsc.get_gene_set('chromatin modifiers')

    return gene_set['syms']


@pytest.fixture(scope='session')
def denovo_studies():
    studies = vDB.get_studies('ALL WHOLE EXOME')
    return [st for st in studies if 'WE' == st.get_attr('study.type')]


@pytest.fixture(scope='session')
def autism_studies(denovo_studies):
    return [st for st in denovo_studies
            if 'autism' == st.get_attr('study.phenotype')]


@pytest.fixture(scope='session')
def schizophrenia_studies(denovo_studies):
    return [st for st in denovo_studies
            if 'schizophrenia' == st.get_attr('study.phenotype')]


@pytest.fixture(scope='session')
def unaffected_studies(denovo_studies):
    return denovo_studies


# @pytest.fixture(scope='module')
# def children_stats(request):
#     denovo_studies = DenovoStudies()
#     return ChildrenStats.build(denovo_studies)


@pytest.fixture(scope='session')
def datasets_config():
    return DatasetsConfig()


@pytest.fixture(scope='session')
def datasets_factory(datasets_config):
    return DatasetsFactory(datasets_config)


@pytest.fixture(scope='session')
def ssc(datasets_factory):
    return datasets_factory.get_dataset('SSC')


@pytest.fixture(scope='session')
def vip(datasets_factory):
    return datasets_factory.get_dataset('SVIP')


@pytest.fixture(scope='session')
def sd(datasets_factory):
    return datasets_factory.get_dataset('SD')


@pytest.fixture(scope='session')
def denovo_db(datasets_factory):
    return datasets_factory.get_dataset('denovo_db')


@pytest.fixture(scope='module')
def samocha_background():
    bg = SamochaBackground()
    bg.precompute()
    return bg


@pytest.fixture(scope='module')
def synonymous_background():
    bg = SynonymousBackground(use_cache=True)
    return bg
