# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

import pytest

from dae.person_sets import PersonSet, PersonSetCollection
from dae.studies.study import GenotypeData
from dae.variants.family_variant import FamilyVariant


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


@pytest.fixture(scope="session")
def t4c8_dataset_denovo(
    t4c8_dataset: GenotypeData,
) -> list[FamilyVariant]:
    denovo_variants = list(
        t4c8_dataset.query_variants(
            inheritance="denovo",
        ))

    assert len(denovo_variants) == 7
    return denovo_variants


@pytest.fixture
def phenotype_role_collection(
    t4c8_dataset: GenotypeData,
) -> PersonSetCollection:
    collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert collection is not None
    return collection


@pytest.fixture
def phenotype_role_sets(
    phenotype_role_collection: PersonSetCollection,
) -> list[PersonSet]:
    return [
        person_set
        for person_set in phenotype_role_collection.person_sets.values()
        if len(person_set.persons) > 0
    ]
