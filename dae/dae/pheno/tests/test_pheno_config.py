import os
import pytest
from dae.pheno.utils.config import PhenoConfigParser


def test_pheno_config_loading(fake_pheno_config):
    assert all([db in ['fake', 'dummy_1', 'dummy_2']
                for db in list(fake_pheno_config.keys())])


def test_missing_but_specified_files(dummy_pheno_missing_files_conf):
    with pytest.raises(AssertionError):
        PhenoConfigParser.read_file_configuration(
            dummy_pheno_missing_files_conf,
            os.path.dirname(dummy_pheno_missing_files_conf)
        )


def test_existing_attributes(fake_pheno_config):
    assert os.path.isfile(fake_pheno_config['dummy_1'].dbfile)
    assert os.path.isfile(fake_pheno_config['dummy_1'].browser_dbfile)
    assert os.path.isdir(fake_pheno_config['dummy_1'].browser_images_dir)
    assert fake_pheno_config['dummy_1'].browser_images_url == \
        'static/dummy-images'


def test_missing_attributes(fake_pheno_config):
    assert fake_pheno_config['dummy_2'].dbfile is None
    assert fake_pheno_config['dummy_2'].browser_dbfile is None
    assert fake_pheno_config['dummy_2'].browser_images_dir is None
    assert fake_pheno_config['dummy_2'].browser_images_url is None
