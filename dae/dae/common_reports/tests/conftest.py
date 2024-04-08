# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from typing import Callable, List

import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.person_sets import PersonSet, PersonSetCollection
from dae.studies.study import GenotypeData
from dae.variants.family_variant import FamilyVariant


def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


@pytest.fixture(scope="session")
def local_gpf_instance(
    gpf_instance: Callable[[str], GPFInstance]
) -> GPFInstance:
    return gpf_instance(
        os.path.join(fixtures_dir(), "gpf_instance.yaml"))


@pytest.fixture(scope="session")
def study1(local_gpf_instance: GPFInstance) -> GenotypeData:
    study = local_gpf_instance.get_genotype_data("Study1")
    assert study is not None
    return study


@pytest.fixture(scope="session")
def study2(local_gpf_instance: GPFInstance) -> GenotypeData:
    return local_gpf_instance.get_genotype_data("Study2")


@pytest.fixture(scope="session")
def study4(local_gpf_instance: GPFInstance) -> GenotypeData:
    return local_gpf_instance.get_genotype_data("Study4")


@pytest.fixture(scope="session")
def genotype_data_group1(local_gpf_instance: GPFInstance) -> GenotypeData:
    return local_gpf_instance.get_genotype_data("Dataset1")


@pytest.fixture(scope="session")
def denovo_variants_ds1(
    genotype_data_group1: GenotypeData
) -> List[FamilyVariant]:
    denovo_variants = list(
        genotype_data_group1.query_variants(
            limit=None, inheritance="denovo",
        ))

    assert len(denovo_variants) == 8
    return denovo_variants


@pytest.fixture
def phenotype_role_collection(
    study1: GenotypeData
) -> PersonSetCollection:
    collection = study1.get_person_set_collection("phenotype")
    assert collection is not None
    return collection


@pytest.fixture
def phenotype_role_sets(
    phenotype_role_collection: PersonSetCollection
) -> List[PersonSet]:
    person_sets = []
    for person_set in phenotype_role_collection.person_sets.values():
        if len(person_set.persons) > 0:
            person_sets.append(person_set)
    return person_sets
