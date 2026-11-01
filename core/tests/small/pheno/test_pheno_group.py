# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

from typing import Any

import pandas as pd
import pytest

from gpf.pheno.common import MeasureType
from gpf.pheno.pheno_data import (
    PhenotypeGroup,
    PhenotypeStudy,
    RestrictedPhenotypeGroup,
)
from gpf.pheno.registry import PhenoRegistry
from gpf.variants.attributes import Role, Sex, Status


@pytest.fixture(scope="session")
def fake_group(fake_pheno_db: PhenoRegistry) -> PhenotypeGroup:
    fake = fake_pheno_db.get_phenotype_data("fake")
    fake2 = fake_pheno_db.get_phenotype_data("fake2")

    group = PhenotypeGroup("group", {}, [fake, fake2])
    assert group is not None
    return group


def test_pheno_group_families(fake_group: PhenotypeGroup) -> None:
    assert fake_group is not None
    assert len(fake_group.children) == 2


def test_pheno_group_instruments_and_measures(
    fake_group: PhenotypeGroup,
) -> None:
    assert "i1" in fake_group.instruments, fake_group.instruments
    assert "i2" in fake_group.instruments, fake_group.instruments

    assert "i1.age" in fake_group.measures
    assert "i5.iq" in fake_group.measures

    assert fake_group.has_measure("i1.iq")
    assert fake_group.has_measure("i5.iq")

    mes1 = fake_group.get_measure("i1.iq")
    assert mes1.measure_id == "i1.iq"

    mes2 = fake_group.get_measure("i5.iq")
    assert mes2.measure_id == "i5.iq"


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_get_people_measure_values_df(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    df = fake_group.get_people_measure_values_df(
        ["i1.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "family_id": ["f1"],
        "role": [Role.prb],
        "status": [Status.affected],
        "sex": [Sex.M],
        "i1.iq": [86.41],
    })
    pd.testing.assert_frame_equal(
        df, expected, atol=1e-2, check_dtype=False,
    )


def test_pheno_group_get_people_measure_values_df_mixed_measures_join(
    fake_group: PhenotypeGroup,
) -> None:
    df = fake_group.get_people_measure_values_df(["i1.iq", "i5.iq"])

    assert len(df) == 195

    assert "i1.iq" in df
    assert "i5.iq" in df


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_get_people_measure_values(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    res = fake_group.get_people_measure_values(
        ["i1.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    out = next(res)

    assert out["person_id"] == "f1.p1"
    assert out["i1.iq"] == pytest.approx(86.41, abs=1e-2)


def test_pheno_group_get_measures(fake_group: PhenotypeGroup) -> None:
    # Total measures are 30
    measures = fake_group.get_measures(measure_type=MeasureType.continuous)
    assert len(measures) == 14, measures

    measures = fake_group.get_measures(
        instrument_name="i1", measure_type=MeasureType.continuous)
    assert len(measures) == 7, measures

    measures = fake_group.get_measures(measure_type=MeasureType.ordinal)
    assert len(measures) == 6, measures

    measures = fake_group.get_measures(
        instrument_name="i1", measure_type=MeasureType.ordinal)
    assert len(measures) == 2, measures


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_i1_get_values_df(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    df = fake_group.get_people_measure_values_df(
        ["i1.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "family_id": ["f1"],
        "role": [Role.prb],
        "status": [Status.affected],
        "sex": [Sex.M],
        "i1.iq": [86.41],
    })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2, check_dtype=False)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_i2_get_values_df(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    df = fake_group.get_people_measure_values_df(
        ["i5.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "family_id": ["f1"],
        "role": [Role.prb],
        "status": [Status.affected],
        "sex": [Sex.M],
        "i5.iq": [86.41],
    })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2, check_dtype=False)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_i1_i2_get_values_df(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    df = fake_group.get_people_measure_values_df(
        ["i1.iq", "i5.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "family_id": ["f1"],
        "role": [Role.prb],
        "status": [Status.affected],
        "sex": [Sex.M],
        "i1.iq": [86.41],
        "i5.iq": [86.41],
    })

    pd.testing.assert_frame_equal(df, expected, atol=1e-2, check_dtype=False)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, ["f1.p1"]),
        ([Role.prb], ["f1"], None),
        ([Role.prb, Role.sib], ["f1"], ["f1.p1"]),
        ([Role.prb], ["f1", "f2"], ["f1.p1"]),
    ],
)
def test_pheno_group_i1_i2_get_values(
    fake_group: PhenotypeGroup,
    roles: list[Role] | None,
    family_ids: list[str] | None,
    person_ids: list[str] | None,
) -> None:
    res = fake_group.get_people_measure_values(
        ["i1.iq", "i5.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    out = next(res)
    assert out["person_id"] == "f1.p1"
    assert out["i1.iq"] == pytest.approx(86.41, abs=1e-2)
    out = next(res)
    assert out["person_id"] == "f1.p1"
    assert out["i5.iq"] == pytest.approx(86.41, abs=1e-2)


def test_restricted_pheno_group_searches_only_its_leaves(
    fake_pheno_db: PhenoRegistry,
) -> None:
    group = fake_pheno_db.get_phenotype_data("fake_group")
    assert isinstance(group, PhenotypeGroup)
    fake2 = fake_pheno_db.get_phenotype_data("fake2")
    assert isinstance(fake2, PhenotypeStudy)

    restricted = RestrictedPhenotypeGroup(group, [fake2])

    assert restricted.pheno_id == "fake_group"
    assert sorted(
        m["measure"]["measure_id"]
        for m in restricted.search_measures(None, None)
    ) == sorted(fake2.measures)
    assert restricted.count_measures(None, None) == len(fake2.measures)
    assert sorted(restricted.measures) == sorted(fake2.measures)


def test_restricted_pheno_group_leaves_the_full_group_unchanged(
    fake_pheno_db: PhenoRegistry,
) -> None:
    group = fake_pheno_db.get_phenotype_data("fake_group")
    assert isinstance(group, PhenotypeGroup)
    fake2 = fake_pheno_db.get_phenotype_data("fake2")
    assert isinstance(fake2, PhenotypeStudy)
    parents = set(fake2.parents)

    RestrictedPhenotypeGroup(group, [fake2])

    assert [child.pheno_id for child in group.children] == [
        "fake", "fake_subgroup"]
    assert len(group.measures) == 27
    assert fake2.parents == parents


@pytest.mark.parametrize("kwargs", [
    {"page": 2},
    {"sort_by": "measure"},
    {"order_by": "desc"},
])
def test_restricted_pheno_group_refuses_to_page_or_sort_searches(
    fake_pheno_db: PhenoRegistry,
    kwargs: dict[str, Any],
) -> None:
    group = fake_pheno_db.get_phenotype_data("fake_group")
    assert isinstance(group, PhenotypeGroup)
    restricted = RestrictedPhenotypeGroup(group, group.get_leaves())

    with pytest.raises(NotImplementedError):
        list(restricted.search_measures(None, None, **kwargs))


def test_restricted_pheno_group_refuses_to_page_counts(
    fake_pheno_db: PhenoRegistry,
) -> None:
    group = fake_pheno_db.get_phenotype_data("fake_group")
    assert isinstance(group, PhenotypeGroup)
    restricted = RestrictedPhenotypeGroup(group, group.get_leaves())

    with pytest.raises(NotImplementedError):
        restricted.count_measures(None, None, page=2)
