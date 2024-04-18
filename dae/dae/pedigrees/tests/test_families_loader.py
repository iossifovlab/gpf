# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
from typing import Callable

import pytest
from pandas.api.types import is_string_dtype

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role


@pytest.mark.parametrize(
    "pedigree",
    [
        ("pedigree_A.ped"),
        ("pedigree_B.ped"),
        ("pedigree_B2.ped"),
        ("pedigree_C.ped"),
    ],
)
def test_famlies_loader_simple(
    pedigree: str, fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname(f"pedigrees/{pedigree}")
    assert os.path.exists(filename)
    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None


def test_families_loader_phenotype(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("pedigrees/pedigree_D.ped")
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    for fam_id, family in families.items():
        print(fam_id, family, family.persons)
        for _person_id, person in family.persons.items():
            print(person)
            print(person.has_attr("phenotype"))
            assert person.has_attr("phenotype")


def test_families_loader_phenos(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("pedigrees/pedigree_phenos.ped")
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    for _fam_id, family in families.items():
        for _person_id, person in family.persons.items():
            assert person.has_attr("phenotype")
            assert person.has_attr("pheno2")
            assert person.has_attr("pheno3")

    ped_df = families.ped_df
    assert is_string_dtype(ped_df["pheno3"])
    assert is_string_dtype(ped_df["pheno2"])
    assert is_string_dtype(ped_df["phenotype"])


@pytest.mark.parametrize(
    "pedigree",
    [
        ("sample_nuc_family.ped"),
        ("pedigree_no_role_A.ped"),
        ("pedigree_no_role_B.ped"),
        ("pedigree_no_role_C.ped"),
    ],
)
def test_families_loader_no_role(
    pedigree: str, fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname(f"pedigrees/{pedigree}")
    assert os.path.exists(filename)

    params = {
        "ped_no_role": True,
    }
    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    assert families is not None
    assert isinstance(families, FamiliesData)

    fam = families["f1"]
    assert fam is not None

    persons = fam.get_members_with_roles(["prb"])
    assert len(persons) == 1

    person = persons[0]
    assert person.person_id == "f1.prb"

    persons = fam.get_members_with_roles(["sib"])
    assert len(persons) == 1

    person = persons[0]
    assert person.person_id == "f1.sib"


def test_families_loader_roles_testing(fixture_dirname: Callable) -> None:
    filename = fixture_dirname("pedigrees/pedigree_no_role_C.ped")
    assert os.path.exists(filename)

    params = {
        "ped_no_role": True,
    }
    loader = FamiliesLoader(filename, **params)
    families = loader.load()

    assert families.persons[("f1", "f1.mg_dad")].role == \
        Role.maternal_grandfather
    assert families.persons[("f1", "f1.mg_mom")].role == \
        Role.maternal_grandmother
    assert families.persons[("f1", "f1.pg_dad")].role == \
        Role.paternal_grandfather
    assert families.persons[("f1", "f1.pg_mom")].role == \
        Role.paternal_grandmother


@pytest.mark.parametrize(
    "pedigree",
    [
        ("pedigree_A.ped"),
        ("pedigree_B.ped"),
        ("pedigree_B2.ped"),
        ("pedigree_C.ped"),
    ],
)
def test_families_ped_df(
    pedigree: str, temp_filename: str, fixture_dirname: Callable,
) -> None:
    filename = fixture_dirname(f"pedigrees/{pedigree}")
    assert os.path.exists(filename)

    loader = FamiliesLoader(filename)
    families = loader.load()

    assert families._ped_df is None

    new_df = families.ped_df
    assert new_df is not None

    # assert_frame_equal(ped_df, new_df, check_like=True)
