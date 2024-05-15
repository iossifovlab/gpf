# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from dae.pheno.registry import PhenoRegistry


def test_check_pheno_db(fake_pheno_db: PhenoRegistry) -> None:
    assert fake_pheno_db.has_phenotype_data("fake")


def test_get_pheno_db(fake_pheno_db: PhenoRegistry) -> None:
    pheno_data = fake_pheno_db.get_phenotype_data("fake")
    assert pheno_data is not None
    assert pheno_data.instruments is not None


def test_get_pheno_db_names(fake_pheno_db: PhenoRegistry) -> None:
    names = fake_pheno_db.get_phenotype_data_ids()
    assert names is not None
    assert len(names) == 1
