import os
import pytest
from pandas.api.types import is_string_dtype

from dae.pedigrees.tests.conftest import relative_to_this_folder

from dae.pedigrees.family import FamiliesLoader, FamiliesData


@pytest.mark.parametrize('pedigree', [
    ('pedigree_A.ped'),
    ('pedigree_B.ped'),
    ('pedigree_B2.ped'),
    ('pedigree_C.ped'),
])
def test_famlies_loader_simple(pedigree):
    filename = relative_to_this_folder(f'fixtures/{pedigree}')
    assert os.path.exists(filename)
    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None


def test_families_loader_phenotype():
    filename = relative_to_this_folder('fixtures/pedigree_D.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    for fam_id, family in families.families.items():
        print(fam_id, family, family.persons)
        for person_id, person in family.persons.items():
            print(person)
            print(person.atts)
            print(person.has_attr('phenotype'))
            assert person.has_attr('phenotype')


def test_families_loader_phenos():
    filename = relative_to_this_folder('fixtures/pedigree_phenos.ped')
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    for fam_id, family in families.families.items():
        for person_id, person in family.persons.items():
            assert person.has_attr('phenotype')
            assert person.has_attr('pheno2')
            assert person.has_attr('pheno3')

    ped_df = families.ped_df
    assert is_string_dtype(ped_df['pheno3'])
    assert is_string_dtype(ped_df['pheno2'])
    assert is_string_dtype(ped_df['phenotype'])


@pytest.mark.parametrize('pedigree', [
    ('sample_nuc_family.ped'),
    ('pedigree_no_role_A.ped'),
    # ('pedigree_no_role_B.ped'),
])
def test_families_loader_no_role(pedigree):
    filename = relative_to_this_folder(f'fixtures/{pedigree}')
    assert os.path.exists(filename)

    params = {
        'ped_no_role': True,
    }
    loader = FamiliesLoader(filename, params=params)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    fam = families.get_family('f1')
    assert fam is not None

    persons = fam.get_people_with_roles(['prb'])
    assert len(persons) == 1

    person = persons[0]
    assert person.person_id == 'f1.prb'

    persons = fam.get_people_with_roles(['sib'])
    assert len(persons) == 1

    person = persons[0]
    assert person.person_id == 'f1.sib'
