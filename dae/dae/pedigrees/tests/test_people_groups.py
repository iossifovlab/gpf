import os
import pytest
from box import Box
from dae.pedigrees.family import PeopleGroup
from dae.pedigrees.tests.conftest import relative_to_this_folder

from dae.pedigrees.family import FamiliesLoader, FamiliesGroup


@pytest.fixture
def people_group_config1():
    return Box({
        'name': 'Study phenotype',
        'domain': [
            {
                'id': 'healthy',
                'name': 'healthy',
                'color': '#e35252',
            },
            {
                'id': 'disease',
                'name': 'disease',
                'color': '#b8008a',
            },
        ],
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa',
        },
        'source': 'phenotype',
    }, default_box=True)


@pytest.fixture
def people_group_config2():
    return Box({
        'name': 'Study phenotype2',
        'domain': [
            {
                'id': 'a',
                'name': 'a',
                'color': '#e35252',
            },
            {
                'id': 'b',
                'name': 'b',
                'color': '#b8008a',
            },
            {
                'id': 'c',
                'name': 'c',
                'color': '#a8008a',
            },
        ],
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa',
        },
        'source': 'pheno2',
    }, default_box=True)


def test_peple_group_config(people_group_config1):
    people_group = PeopleGroup.from_config('phenotype', people_group_config1)
    assert people_group is not None


def test_family_groups1(people_group_config1):
    filename = relative_to_this_folder('fixtures/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('phenotype', people_group_config1)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['healthy', 'disease']


def test_family_groups2(people_group_config2):
    filename = relative_to_this_folder('fixtures/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('phenotype', people_group_config2)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['a', 'b', 'c']

    assert families_group.families_types is not None
    assert families_group.families_types == [('a', 'b'), ('a', 'b', 'c')]


def test_family_groups2_unknown(people_group_config2):
    filename = relative_to_this_folder('fixtures/pedigree_phenos_B.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('phenotype', people_group_config2)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['a', 'b', 'c', 'unknown']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('a', 'b'), ('a', 'b', 'c'), ('a', 'b', 'c', 'unknown')]
