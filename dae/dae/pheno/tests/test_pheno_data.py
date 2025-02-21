# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest

from dae.pedigrees.family import Person
from dae.pheno.pheno_data import PhenotypeStudy


@pytest.fixture(scope="session")
def pheno_study(fake_phenotype_data: PhenotypeStudy) -> PhenotypeStudy:
    return fake_phenotype_data


def test_data_get_persons(pheno_study: PhenotypeStudy):
    persons = pheno_study.get_persons()
    assert persons is not None
    assert len(persons) == 195
    assert "f1.p1" in persons
    assert isinstance(persons["f1.p1"], Person)


def test_study_families(pheno_study: PhenotypeStudy):
    families = pheno_study.families
    assert families is not None
    assert len(families) == 39
    assert len(families.persons) == 195


def test_study_person_sets(pheno_study: PhenotypeStudy):
    person_set_collections = pheno_study.person_set_collections

    assert len(person_set_collections) == 1
    assert "phenotype" in person_set_collections

    assert len(person_set_collections["phenotype"].person_sets) == 2
    assert "autism" in person_set_collections["phenotype"].person_sets
    assert "unaffected" in person_set_collections["phenotype"].person_sets

    assert len(person_set_collections["phenotype"].person_sets["autism"]) == 66
    assert len(person_set_collections["phenotype"].person_sets["unaffected"]) == 129  # noqa: E501


def test_study_common_report(pheno_study: PhenotypeStudy):
    common_report = pheno_study.get_common_report()
    assert common_report is not None
    assert common_report.people_report is not None
    assert common_report.families_report is not None
    assert common_report.families_report.families_counters is not None
