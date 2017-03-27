'''
Created on Mar 27, 2017

@author: lubo
'''
import copy
from datasets.tests.requests import EXAMPLE_QUERY_SD


def test_denovo_studies_study_types_sd(sd):
    query = copy.deepcopy(EXAMPLE_QUERY_SD)

    assert 14 == len(sd.denovo_studies)

    studies = sd.get_denovo_studies(**query)
    assert 14 == len(studies)

    query['studyTypes'] = ['tg']
    studies = sd.get_denovo_studies(**query)
    assert 3 == len(studies)

    query['studyTypes'] = ['we']
    studies = sd.get_denovo_studies(**query)
    assert 11 == len(studies)


def test_variants_study_types_sd(sd):
    query = copy.deepcopy(EXAMPLE_QUERY_SD)
    query['studyTypes'] = ['tg']

    vs = sd.get_variants(**query)

    assert 39 == len(list(vs))
