# pylint: disable=W0621,C0114,C0116,W0212,W0613
from types import SimpleNamespace
from typing import cast

import pandas as pd
import pytest

from gpf.gpf_instance import GPFInstance
from gpf.pedigrees.families_data import FamiliesData
from gpf.person_filters import PhenoFilterSet
from gpf.pheno.pheno_data import PhenotypeData
from gpf.variants.attributes import Role


@pytest.fixture
def families(t4c8_instance: GPFInstance) -> FamiliesData:
    return t4c8_instance.get_genotype_data("t4c8_study_1").families


@pytest.fixture
def val1_filter(t4c8_study_1_pheno: PhenotypeData) -> PhenoFilterSet:
    measure = t4c8_study_1_pheno.get_measure("i1.m5")
    return PhenoFilterSet(measure, {"val1"}, t4c8_study_1_pheno)


def test_apply_without_roles_keeps_persons_of_the_families(
    val1_filter: PhenoFilterSet,
    families: FamiliesData,
) -> None:
    result = val1_filter.apply(families)

    assert result == {"dad3", "p3"}


def test_apply_skips_a_person_id_absent_from_the_families(
    val1_filter: PhenoFilterSet,
    families: FamiliesData,
) -> None:
    assert "p4" in set(val1_filter.measure_df["person_id"])
    assert "p4" not in families.persons_by_person_id

    result = val1_filter.apply(families)

    assert "p4" not in result


def test_apply_with_roles_keeps_persons_with_a_listed_role(
    val1_filter: PhenoFilterSet,
    families: FamiliesData,
) -> None:
    result = val1_filter.apply(families, ["prb"])

    assert result == {"p3"}


def test_apply_with_an_empty_roles_list_keeps_nobody(
    val1_filter: PhenoFilterSet,
    families: FamiliesData,
) -> None:
    result = val1_filter.apply(families, [])

    assert result == set()


class _StubPhenotypeData:
    """Return a fixed measure table to the constructor of a filter."""

    def __init__(self, measure_df: pd.DataFrame) -> None:
        self.measure_df = measure_df

    def get_people_measure_values_df(
        self, _measure_ids: list[str],
    ) -> pd.DataFrame:
        return self.measure_df


def _make_filter(
    pheno: PhenotypeData, person_ids: list[str],
) -> PhenoFilterSet:
    measure = pheno.get_measure("i1.m5")
    measure_df = pd.DataFrame({
        "person_id": person_ids,
        "i1.m5": ["val1"] * len(person_ids),
    })
    stub = cast(PhenotypeData, _StubPhenotypeData(measure_df))
    return PhenoFilterSet(measure, {"val1"}, stub)


def _make_families(
    persons_by_person_id: dict[str, list[Role]],
) -> FamiliesData:
    stub = SimpleNamespace(persons_by_person_id={
        person_id: [SimpleNamespace(role=role) for role in roles]
        for person_id, roles in persons_by_person_id.items()
    })
    return cast(FamiliesData, stub)


def test_apply_keeps_a_person_id_when_any_of_its_persons_has_the_role(
    t4c8_study_1_pheno: PhenotypeData,
) -> None:
    pheno_filter = _make_filter(t4c8_study_1_pheno, ["ch1"])
    families = _make_families({"ch1": [Role.sib, Role.prb]})

    result = pheno_filter.apply(families, ["prb"])

    assert result == {"ch1"}


def test_apply_skips_a_person_id_when_none_of_its_persons_has_the_role(
    t4c8_study_1_pheno: PhenotypeData,
) -> None:
    pheno_filter = _make_filter(t4c8_study_1_pheno, ["ch1"])
    families = _make_families({"ch1": [Role.sib, Role.mom]})

    result = pheno_filter.apply(families, ["prb"])

    assert result == set()


def test_apply_collapses_repeated_person_ids_into_one(
    t4c8_study_1_pheno: PhenotypeData,
) -> None:
    pheno_filter = _make_filter(t4c8_study_1_pheno, ["ch1", "ch1", "ch2"])
    families = _make_families({"ch1": [Role.prb], "ch2": [Role.sib]})

    result = pheno_filter.apply(families)

    assert result == {"ch1", "ch2"}


def test_apply_with_a_str_roles_value_does_a_substring_check(
    t4c8_study_1_pheno: PhenotypeData,
) -> None:
    pheno_filter = _make_filter(t4c8_study_1_pheno, ["ch1", "ch2", "ch3"])
    families = _make_families({
        "ch1": [Role.prb], "ch2": [Role.dad], "ch3": [Role.mom],
    })
    roles = cast(list[str], "dadprb")

    result = pheno_filter.apply(families, roles)

    assert result == {"ch1", "ch2"}
