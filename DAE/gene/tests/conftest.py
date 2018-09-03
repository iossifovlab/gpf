'''
Created on Mar 29, 2018

@author: lubo
'''
import pytest
from gene.gene_set_collections import GeneSetsCollections
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from study_groups.tests.conftest import study_group_facade, study_groups_factory


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(
        path_to_fixtures('studies', 'studies.conf'))


@pytest.fixture(scope='session')
def basic_groups_definition():
    return SingleFileStudiesGroupDefinition(
        path_to_fixtures('studies', 'study_group.conf'))


@pytest.fixture(scope='session')
def gscs(study_group_facade):
    res = GeneSetsCollections(study_group_facade=study_group_facade)
    return res
