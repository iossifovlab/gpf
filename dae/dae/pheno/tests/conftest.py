'''
Created on Nov 21, 2016

@author: lubo
'''
from __future__ import unicode_literals
import pytest
import os
import pandas as pd
from dae.pheno.prepare.ped2individuals import SPARKCsvPedigreeReader
from dae.pheno.prepare.individuals2ped import InternalCsvIndividualsReader
import tempfile
import shutil
from dae.pheno.common import default_config
from dae.pheno.utils.configuration import PhenoConfig
from box import Box

from dae.configuration.configuration import DAEConfig


def relative_to_this_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def csv_individuals_reader():
    return InternalCsvIndividualsReader()


@pytest.fixture(scope='session')
def family_roles_file():
    return relative_to_this_folder(
        'fixtures/pedigree_data/various_families/roles/family.csv')


@pytest.fixture(scope='session')
def family_roles(
        csv_individuals_reader, family_roles_file):
    return csv_individuals_reader.read_filename(family_roles_file)


@pytest.fixture(scope='session')
def csv_pedigree_reader():
    return SPARKCsvPedigreeReader()


@pytest.fixture(scope='session')
def family_pedigree_file():
    return relative_to_this_folder(
        'fixtures/pedigree_data/various_families/pedigrees/family.ped')


@pytest.fixture(scope='session')
def family_pedigree(csv_pedigree_reader, family_pedigree_file):
    return csv_pedigree_reader.read_filename(family_pedigree_file)


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def fake_dae_conf():
    return DAEConfig.make_config(fixtures_dir())


@pytest.fixture(scope='session')
def fake_ped_file():
    return relative_to_this_folder(
        'fixtures/pedigree_data/fake_pheno.ped')


@pytest.fixture(scope='session')
def fake_instrument_filename():
    return relative_to_this_folder('fixtures/instruments/i1.csv')


@pytest.fixture(scope='session')
def fi1_df(fake_instrument_filename):
    df = pd.read_csv(fake_instrument_filename, low_memory=False,
                     encoding="utf-8")
    return df


@pytest.fixture(scope='session')
def fake_pheno_factory(fake_dae_conf):
    from dae.pheno.pheno_factory import PhenoFactory
    return PhenoFactory(fake_dae_conf)


@pytest.fixture(scope='session')
def fphdb_config():
    return relative_to_this_folder('fixtures/fake_phenoDB/main_fake/fake.conf')


@pytest.fixture(scope='session')
def fphdb(fake_pheno_factory):
    db = fake_pheno_factory.get_pheno_db('fake')
    return db


@pytest.fixture(scope='session')
def dummy_pheno_missing_files_conf():
    return relative_to_this_folder('fixtures/dummy_pheno_missing_files.conf')


@pytest.fixture(scope='session')
def fake_pheno_config(fake_dae_conf):
    return PhenoConfig.from_dae_config(fake_dae_conf)


@pytest.fixture(scope='session')
def fake_background_filename():
    return relative_to_this_folder('fixtures/background.csv')


@pytest.fixture(scope='session')
def fake_background_df(fake_background_filename):
    df = pd.read_csv(fake_background_filename, low_memory=False,
                     encoding="utf-8")
    return df


@pytest.fixture(scope='session')
def sample_nuc_family():
    return relative_to_this_folder(
        'fixtures/pedigree_data/sample_nuc_family.ped')


@pytest.fixture
def test_config(temp_dbfile):
    config = default_config()
    config.db.filename = temp_dbfile
    return Box(config.to_dict())


@pytest.fixture
def temp_dbfile(request):
    dirname = tempfile.mkdtemp(suffix='_ped', prefix='pheno_db_')

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)

    output = os.path.join(
        dirname,
        'test_output.db'
    )
    return output


@pytest.fixture
def valid_descriptions():
    return relative_to_this_folder('fixtures/descriptions_valid.tsv')


@pytest.fixture
def invalid_descriptions():
    return relative_to_this_folder('fixtures/descriptions_invalid.tsv')
