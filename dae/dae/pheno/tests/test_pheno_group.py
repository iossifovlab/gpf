import pytest

from dae.pheno.pheno_db import PhenotypeGroup


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
