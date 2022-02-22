
def test_pheno_factory_simple(fake_pheno_db):
    assert fake_pheno_db.config is not None


def test_check_pheno_db(fake_pheno_db):
    assert fake_pheno_db.has_phenotype_data("fake")


def test_get_pheno_db(fake_pheno_db):
    pheno_data = fake_pheno_db.get_phenotype_data("fake")
    assert pheno_data is not None
    assert pheno_data.families is not None
    assert pheno_data.instruments is not None


def test_get_pheno_db_names(fake_pheno_db):
    names = fake_pheno_db.get_phenotype_data_ids()
    assert names is not None
    assert len(names) == 5
