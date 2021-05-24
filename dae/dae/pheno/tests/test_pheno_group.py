import pytest
import pandas as pd

from dae.pheno.pheno_db import PhenotypeGroup
from dae.variants.attributes import Role, Status, Sex


@pytest.fixture(scope="session")
def fake_group(fake_pheno_db):
    fake = fake_pheno_db.get_phenotype_data("fake")
    fake2 = fake_pheno_db.get_phenotype_data("fake2")

    group = PhenotypeGroup("group", [fake, fake2])
    assert group is not None
    return group


def test_pheno_group_families(fake_group):
    assert fake_group is not None
    assert len(fake_group.phenotype_data) == 2

    assert all(
        fake_group.families.ped_df ==
        fake_group.phenotype_data[0].families.ped_df)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_get_persons_df(fake_group, roles, family_ids, person_ids):
    fake = fake_group.phenotype_data[0]
    ped_df = fake.get_persons_df(
        roles=roles,
        family_ids=family_ids,
        person_ids=person_ids)
    print(ped_df)

    ped_df = fake_group.get_persons_df(
        roles=roles,
        family_ids=family_ids,
        person_ids=person_ids)
    print(ped_df)
    assert len(ped_df) == 1
    assert all(ped_df["person_id"] == "f1.p1"), ped_df


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_get_persons(fake_group, roles, family_ids, person_ids):

    persons = fake_group.get_persons(
        roles=roles,
        family_ids=family_ids,
        person_ids=person_ids)
    print(persons)
    assert len(persons) == 1
    assert "f1.p1" in persons
    p = persons["f1.p1"]
    assert p is not None
    assert p.person_id == "f1.p1"


def test_pheno_group_instruments_and_measures(fake_group):
    assert "i1" in fake_group.instruments, fake_group.instruments
    assert "i2" in fake_group.instruments, fake_group.instruments

    assert "i1.age" in fake_group.measures
    assert "i2.iq" in fake_group.measures

    assert fake_group.has_measure("i1.iq")
    assert fake_group.has_measure("i2.iq")

    m1 = fake_group.get_measure("i1.iq")
    assert m1.measure_id == "i1.iq"

    m2 = fake_group.get_measure("i2.iq")
    assert m2.measure_id == "i2.iq"


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_get_measure_values_df(
        fake_group, roles, family_ids, person_ids):
    df = fake_group.get_measure_values_df(
        "i1.iq", person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(df)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "i1.iq": [86.41]
        })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, None),
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_get_measure_values(
        fake_group, roles, family_ids, person_ids):
    res = fake_group.get_measure_values(
        "i1.iq", person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(res)

    assert "f1.p1" in res

    assert res["f1.p1"] == pytest.approx(86.41, abs=1e-2)


def test_pheno_group_get_measures(fake_group):

    measures = fake_group.get_measures(measure_type="continuous")
    print(measures)

    assert len(measures) == 14, measures

    measures = fake_group.get_measures(
        instrument_name="i1", measure_type="continuous")
    print(measures)

    assert len(measures) == 7, measures

    measures = fake_group.get_measures(measure_type="ordinal")
    print(measures)

    assert len(measures) == 4, measures

    measures = fake_group.get_measures(
        instrument_name="i1", measure_type="ordinal")
    print(measures)

    assert len(measures) == 2, measures


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_i1_get_values_df(
        fake_group, roles, family_ids, person_ids):

    df = fake_group.get_values_df(
        ["i1.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(df)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "i1.iq": [86.41]
        })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_i2_get_values_df(
        fake_group, roles, family_ids, person_ids):

    df = fake_group.get_values_df(
        ["i2.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(df)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "i2.iq": [86.41]
        })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_i1_i2_get_values_df(
        fake_group, roles, family_ids, person_ids):

    df = fake_group.get_values_df(
        ["i1.iq", "i2.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(df)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "i1.iq": [86.41],
        "i2.iq": [86.41]
        })
    pd.testing.assert_frame_equal(df, expected, atol=1e-2)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_i1_i2_get_values(
        fake_group, roles, family_ids, person_ids):

    res = fake_group.get_values(
        ["i1.iq", "i2.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)
    print(res)

    assert "f1.p1" in res

    assert res["f1.p1"]["i1.iq"] == pytest.approx(86.41, abs=1e-2)
    assert res["f1.p1"]["i2.iq"] == pytest.approx(86.41, abs=1e-2)


@pytest.mark.parametrize(
    "roles,family_ids,person_ids",
    [
        (None, None, {"f1.p1"}),
        ({Role.prb}, {"f1"}, None),
        ({Role.prb, Role.sib}, {"f1"}, {"f1.p1"}),
        ({Role.prb}, {"f1", "f2"}, {"f1.p1"}),
    ],
)
def test_pheno_group_i1_i2_get_person_values_df(
        fake_group, roles, family_ids, person_ids):

    df = fake_group.get_persons_values_df(
        ["i1.iq", "i2.iq"], person_ids=person_ids,
        family_ids=family_ids, roles=roles)

    expected = pd.DataFrame({
        "person_id": ["f1.p1"],
        "family_id": ["f1"],
        "role": [Role.prb],
        "sex": [Sex.M],
        "status": [Status.affected],
        "i1.iq": [86.41],
        "i2.iq": [86.41]
        })
    expected = expected.set_index("person_id")

    pd.testing.assert_frame_equal(
        df, expected, atol=1e-2,
        check_index_type=False,
        check_names=False,
    )
