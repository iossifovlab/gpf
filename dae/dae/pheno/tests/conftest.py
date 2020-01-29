import pytest

import os
import pandas as pd
import tempfile
import shutil
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema

from dae.pheno.prepare.ped2individuals import SPARKCsvPedigreeReader
from dae.pheno.prepare.individuals2ped import InternalCsvIndividualsReader
from dae.pheno.common import default_config
from dae.pheno.utils.config import PhenoConfigParser
from dae.pheno.pheno_db import PhenoDb


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


@pytest.fixture(scope='session')
def fake_dae_conf():
    return GPFConfigParser.load_config(
        relative_to_this_folder('fixtures/DAE.conf'), dae_conf_schema
    )


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
def fake_pheno_db(fake_dae_conf):
    return PhenoDb(fake_dae_conf)


@pytest.fixture(scope='session')
def fake_phenotype_data_config():
    return relative_to_this_folder('fixtures/fake_phenoDB/main_fake/fake.conf')


@pytest.fixture(scope='session')
def fake_phenotype_data(fake_pheno_db):
    data = fake_pheno_db.get_phenotype_data('fake')
    return data


@pytest.fixture(scope='session')
def dummy_pheno_missing_files_conf():
    return relative_to_this_folder('fixtures/dummy_pheno_missing_files.conf')


@pytest.fixture(scope='session')
def fake_pheno_config(fake_dae_conf):
    return PhenoConfigParser.read_directory_configurations(
        fake_dae_conf.phenotype_data.dir)


@pytest.fixture(scope='session')
def fake_background_filename():
    return relative_to_this_folder('fixtures/background.csv')


@pytest.fixture(scope='session')
def fake_background_df(fake_background_filename):
    df = pd.read_csv(fake_background_filename, low_memory=False,
                     encoding="utf-8")
    return df


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
