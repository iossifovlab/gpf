import pytest

from dae.pheno.pheno_db import PhenotypeGroup
from dae.variants.attributes import Role


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
