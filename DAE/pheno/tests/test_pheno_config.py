import os
import pytest
from pheno.utils.configuration import PhenoConfig


def test_pheno_config_loading(fake_pheno_config):
    assert all([db in ['fake', 'dummy_1', 'dummy_2']
                for db in fake_pheno_config.db_names])


def test_missing_but_specified_files(dummy_pheno_missing_files_conf):
    with pytest.raises(AssertionError):
        PhenoConfig.from_file(dummy_pheno_missing_files_conf)


def test_existing_attributes(fake_pheno_config):
    assert os.path.isfile(fake_pheno_config.get_dbfile('dummy_1'))
    assert os.path.isfile(fake_pheno_config.get_browser_dbfile('dummy_1'))
    assert os.path.isdir(fake_pheno_config.get_browser_images_dir('dummy_1'))
    assert fake_pheno_config.get_browser_images_url('dummy_1') == \
        'static/dummy-images'
    assert fake_pheno_config.get_age('dummy_1') == 'i1:age'
    assert fake_pheno_config.get_nonverbal_iq('dummy_1') == 'i1:iq'


def test_missing_attributes(fake_pheno_config):
    assert fake_pheno_config.get_dbfile('dummy_2') is None
    assert fake_pheno_config.get_browser_dbfile('dummy_2') is None
    assert fake_pheno_config.get_browser_images_dir('dummy_2') is None
    assert fake_pheno_config.get_browser_images_url('dummy_2') is None
    assert fake_pheno_config.get_age('dummy_2') is None
    assert fake_pheno_config.get_nonverbal_iq('dummy_2') is None
