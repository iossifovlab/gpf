import os
import pytest
from box import Box
from dae.pedigrees.tests.conftest import relative_to_this_folder
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_groups import PeopleGroup, \
    FamiliesGroup, FamiliesSizeGroup, \
    PEOPLE_GROUP_ROLES, PEOPLE_GROUP_STATUS, PEOPLE_GROUP_SEXES, \
    PEOPLE_GROUP_FAMILY_SIZES


@pytest.fixture
def people_group_config1():
    return Box({
        'name': 'Study phenotype',
        'domain': {
            'healthy': {
                'id': 'healthy',
                'name': 'healthy',
                'color': '#e35252',
            },
            'disease': {
                'id': 'disease',
                'name': 'disease',
                'color': '#b8008a',
            },
        },
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
        'domain': {
            'a': {
                'id': 'a',
                'name': 'a',
                'color': '#e35252',
            },
            'b': {
                'id': 'b',
                'name': 'b',
                'color': '#b8008a',
            },
            'c': {
                'id': 'c',
                'name': 'c',
                'color': '#a8008a',
            },
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa',
        },
        'source': 'pheno2',
    }, default_box=True)


@pytest.fixture
def people_group_role():
    return Box({
        'name': 'Role',
        'domain': {
            'prb': {
                'id': 'prb',
                'name': 'prb',
                'color': '#e35252',
            },
            'sib': {
                'id': 'sib',
                'name': 'sib',
                'color': '#b8008a',
            },
            'mom': {
                'id': 'mom',
                'name': 'mom',
                'color': '#a8008a',
            },
            'dad': {
                'id': 'dad',
                'name': 'dad',
                'color': '#a8008a',
            },
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa',
        },
        'source': 'role',
    }, default_box=True)


@pytest.fixture
def people_group_status():
    return Box({
        'name': 'Status',
        'domain': {
            'affected': {
                'id': 'affected',
                'name': 'affected',
                'color': '#e35252',
            },
            'unaffected': {
                'id': 'unaffected',
                'name': 'unaffected',
                'color': '#b8008a',
            },
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa',
        },
        'source': 'status',
    }, default_box=True)


def test_peple_group_config(people_group_config1):
    people_group = PeopleGroup.from_config('phenotype', people_group_config1)
    assert people_group is not None


def test_family_groups1(people_group_config1):
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('phenotype', people_group_config1)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['healthy', 'disease']


def test_family_groups2(people_group_config2):
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('phenotype', people_group_config2)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['a', 'b', 'c']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('a', 'a', 'a', 'b', 'b'), ('a', 'a', 'b', 'c')]


def test_family_groups2_unknown(people_group_config2):
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos_B.ped')
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
        ('a', 'a', 'a', 'b', 'b'),
        ('a', 'a', 'b', 'c'),
        ('a', 'a', 'b', 'c', 'unknown')]


def test_family_role_group(people_group_role):
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('role', people_group_role)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['prb', 'sib', 'mom', 'dad']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('prb', 'sib', 'sib', 'mom', 'dad'),
        ('prb', 'sib', 'mom', 'dad')
    ]


def test_family_role_group_predefined():
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PEOPLE_GROUP_ROLES

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['mom', 'dad', 'prb', 'sib']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('mom', 'dad', 'prb', 'sib', 'sib'),
        ('mom', 'dad', 'prb', 'sib'),
    ]


def test_family_status_group(people_group_status):
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    people_group = PeopleGroup.from_config('status', people_group_status)

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['affected', 'unaffected']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('affected', 'affected', 'unaffected', 'unaffected', 'unaffected'),
        ('affected', 'unaffected', 'unaffected', 'unaffected')
    ]


def test_family_status_group_predefined():
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    # people_group = PeopleGroup.from_config('status', people_group_status)
    people_group = PEOPLE_GROUP_STATUS

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['affected', 'unaffected']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('affected', 'affected', 'unaffected', 'unaffected', 'unaffected'),
        ('affected', 'unaffected', 'unaffected', 'unaffected')]


def test_family_sex_group_predefined():
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    # people_group = PeopleGroup.from_config('status', people_group_status)
    people_group = PEOPLE_GROUP_SEXES

    families_group = FamiliesGroup(families, people_group)
    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['M', 'F']

    assert families_group.families_types is not None
    assert families_group.families_types == [
        ('M', 'M', 'F', 'F', 'F'),
        ('M', 'M', 'F', 'F'),
    ]


def test_grayscale_colors():
    assert PeopleGroup.grayscale32(0) == '#ffffff'
    assert PeopleGroup.grayscale32(1) == '#f7f7f7'
    assert PeopleGroup.grayscale32(2) == '#efefef'
    assert PeopleGroup.grayscale32(32) == '#ffffff'


def test_family_sizes_group_predefined():
    filename = relative_to_this_folder(
        'fixtures/pedigrees/pedigree_phenos_B.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()
    # people_group = PeopleGroup.from_config('status', people_group_status)
    people_group = PEOPLE_GROUP_FAMILY_SIZES

    families_group = FamiliesSizeGroup(families)

    fam1 = families['f1']
    assert fam1 is not None
    assert len(fam1) == 5
    prb = fam1.get_member('f1.p1')
    assert prb is not None
    assert people_group.getter(prb) == '5'

    assert people_group.getter(fam1.get_member('f1.p1')) == '5'

    assert families_group is not None
    assert families_group.available_values is not None
    assert families_group.available_values == ['5', '4']

    assert families_group.families_types is not None
    assert families_group.families_types == [('5',), ('4',), ('5',)]
