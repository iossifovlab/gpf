# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import os
import tempfile
import shutil

import pytest

import pandas as pd
from box import Box
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.phenotype_data import pheno_conf_schema

from dae.pheno.common import default_config
from dae.pheno.pheno_db import PhenoDb, PhenotypeData, get_pheno_db_dir


def relative_to_this_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def family_roles_file() -> str:
    return relative_to_this_folder(
        "fixtures/pedigree_data/various_families/roles/family.csv"
    )


@pytest.fixture(scope="session")
def family_roles(csv_individuals_reader, family_roles_file):
    return csv_individuals_reader.read_filename(family_roles_file)


@pytest.fixture(scope="session")
def family_pedigree_file() -> str:
    return relative_to_this_folder(
        "fixtures/pedigree_data/various_families/pedigrees/family.ped"
    )


@pytest.fixture(scope="session")
def family_pedigree(csv_pedigree_reader, family_pedigree_file):
    return csv_pedigree_reader.read_filename(family_pedigree_file)


@pytest.fixture(scope="session")
def fake_dae_conf() -> Box:
    return GPFConfigParser.load_config(
        relative_to_this_folder("fixtures/DAE.conf"), dae_conf_schema
    )


@pytest.fixture(scope="session")
def fake_pheno_db_dir(fake_dae_conf: Box) -> str:
    return get_pheno_db_dir(fake_dae_conf)


@pytest.fixture(scope="session")
def fake_ped_file() -> str:
    return relative_to_this_folder("fixtures/pedigree_data/fake_pheno.ped")


@pytest.fixture(scope="session")
def fake_instrument_filename() -> str:
    return relative_to_this_folder("fixtures/instruments/i1.csv")


@pytest.fixture(scope="session")
def fi1_df(fake_instrument_filename: str) -> pd.DataFrame:
    df = pd.read_csv(
        fake_instrument_filename, low_memory=False, encoding="utf-8"
    )
    return df


@pytest.fixture(scope="session")
def fake_pheno_db(fake_pheno_db_dir: str) -> PhenoDb:
    return PhenoDb(fake_pheno_db_dir)


@pytest.fixture(scope="session")
def fake_phenotype_data_config() -> str:
    return relative_to_this_folder("fixtures/fake_phenoDB/main_fake/fake.conf")


@pytest.fixture(scope="session")
def fake_phenotype_data(fake_pheno_db: PhenoDb) -> PhenotypeData:
    data = fake_pheno_db.get_phenotype_data("fake")
    return data


@pytest.fixture(scope="session")
def fake_phenotype_data_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/main_fake/fake.db"
    )


@pytest.fixture(scope="session")
def fake_phenotype_data_browser_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/main_fake/fake_browser.db"
    )


@pytest.fixture(scope="session")
def dummy_pheno_missing_files_conf() -> str:
    return relative_to_this_folder("fixtures/dummy_pheno_missing_files.conf")


@pytest.fixture(scope="session")
def fake_pheno_config(fake_dae_conf: str) -> Box:
    return GPFConfigParser.load_directory_configs(
        fake_dae_conf.phenotype_data.dir, pheno_conf_schema
    )


@pytest.fixture(scope="session")
def fake_background_filename() -> str:
    return relative_to_this_folder("fixtures/background.csv")


@pytest.fixture(scope="session")
def fake_background_df(fake_background_filename: str) -> pd.DataFrame:
    df = pd.read_csv(
        fake_background_filename, low_memory=False, encoding="utf-8"
    )
    return df


@pytest.fixture
def test_config(temp_dbfile: str): Box:
    config = default_config()
    config.db.filename = temp_dbfile
    return Box(config.to_dict())


@pytest.fixture
def temp_dbfile(request) -> str:
    dirname = tempfile.mkdtemp(suffix="_ped", prefix="pheno_db_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)

    output = os.path.join(dirname, "test_output.db")
    return output


@pytest.fixture
def valid_descriptions() -> str:
    return relative_to_this_folder("fixtures/descriptions_valid.tsv")


@pytest.fixture
def invalid_descriptions() -> str:
    return relative_to_this_folder("fixtures/descriptions_invalid.tsv")


@pytest.fixture
def output_dir(request) -> str:
    tmpdir = tempfile.mkdtemp(prefix="pheno_browser")

    def fin():
        shutil.rmtree(tmpdir)

    request.addfinalizer(fin)
    return tmpdir


@pytest.fixture(scope="session")
def regressions_conf() -> str:
    return relative_to_this_folder("fixtures/regressions.conf")


@pytest.fixture
def temp_dirname_figures(request) -> str:
    dirname = tempfile.mkdtemp(suffix="_plots", prefix="figures_")

    def fin():
        shutil.rmtree(dirname)

    request.addfinalizer(fin)
    return dirname
