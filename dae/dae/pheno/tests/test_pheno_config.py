import os


def test_pheno_config_loading(fake_pheno_config):
    assert all(
        [
            db.phenotype_data.name in ("fake", "fake2", "dummy_1", "dummy_2")
            for db in fake_pheno_config
        ]
    )


def test_existing_attributes(fake_pheno_db):
    dummy_1 = fake_pheno_db.get_dbconfig("dummy_1")
    assert os.path.isfile(dummy_1.dbfile), print
    assert os.path.isfile(dummy_1.browser_dbfile)
    assert os.path.isdir(dummy_1.browser_images_dir)
    assert dummy_1.browser_images_url == "static/dummy-images"


def test_missing_attributes(fake_pheno_db):
    dummy_2 = fake_pheno_db.get_dbconfig("dummy_2")
    assert dummy_2.dbfile is None
    assert dummy_2.browser_dbfile is None
    assert dummy_2.browser_images_dir is None
    assert dummy_2.browser_images_url is None
