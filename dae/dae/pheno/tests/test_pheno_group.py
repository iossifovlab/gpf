# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

from dae.pheno.common import MeasureType
import pandas as pd
import pytest

from dae.pheno.pheno_data import PhenotypeGroup
from dae.pheno.registry import PhenoRegistry
from dae.variants.attributes import Role, Status, Sex


@pytest.fixture(scope="session")
def fake_group(fake_pheno_db: PhenoRegistry) -> PhenotypeGroup:
    fake = fake_pheno_db.get_phenotype_data("fake")
    fake2 = fake_pheno_db.get_phenotype_data("fake2")

    group = PhenotypeGroup("group", [fake, fake2])
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
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


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
    assert len(measures) == 16, measures

    measures = fake_group.get_measures(
        instrument_name="i1", measure_type=MeasureType.continuous)
    assert len(measures) == 7, measures

    measures = fake_group.get_measures(measure_type=MeasureType.ordinal)
    assert len(measures) == 4, measures

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
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


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
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


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
        "person_id": ["f1.p1", "f1.p1"],
        "family_id": ["f1", "f1"],
        "role": [Role.prb, Role.prb],
        "status": [Status.affected, Status.affected],
        "sex": [Sex.M, Sex.M],
        "i1.iq": [86.41, None],
        "i5.iq": [None, 86.41],
    })

    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


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
