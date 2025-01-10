# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import duckdb
import pandas as pd
import pytest
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.configuration.schemas.phenotype_data import pheno_conf_schema
from dae.pheno.common import default_config
from dae.pheno.pheno_data import PhenotypeData, get_pheno_db_dir
from dae.pheno.registry import PhenoRegistry


def relative_to_this_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def family_roles_file() -> str:
    return relative_to_this_folder(
        "fixtures/pedigree_data/various_families/roles/family.csv",
    )


@pytest.fixture(scope="session")
def family_roles(csv_individuals_reader, family_roles_file):
    return csv_individuals_reader.read_filename(family_roles_file)


@pytest.fixture(scope="session")
def family_pedigree_file() -> str:
    return relative_to_this_folder(
        "fixtures/pedigree_data/various_families/pedigrees/family.ped",
    )


@pytest.fixture(scope="session")
def family_pedigree(csv_pedigree_reader, family_pedigree_file):
    return csv_pedigree_reader.read_filename(family_pedigree_file)


@pytest.fixture(scope="session")
def fake_dae_conf() -> Box:
    return GPFConfigParser.load_config(
        relative_to_this_folder("fixtures/DAE.conf"), dae_conf_schema,
    )


@pytest.fixture(scope="session")
def fake_pheno_db_dir(fake_dae_conf: Box) -> str:
    return get_pheno_db_dir(fake_dae_conf)


@pytest.fixture
def clean_pheno_db_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    root_path = tmp_path_factory.mktemp("clean_pheno")
    destination = os.path.join(root_path, "clean_fake")
    clean_study = relative_to_this_folder("fixtures/clean_fake")
    shutil.copytree(clean_study, destination)
    return str(root_path)


@pytest.fixture(scope="session")
def fake_ped_file() -> str:
    return relative_to_this_folder("fixtures/pedigree_data/fake_pheno.ped")


@pytest.fixture(scope="session")
def fake_instrument_filename() -> str:
    return relative_to_this_folder("fixtures/instruments/i1.csv")


@pytest.fixture(scope="session")
def fi1_df(fake_instrument_filename: str) -> pd.DataFrame:
    return pd.read_csv(
        fake_instrument_filename, low_memory=False, encoding="utf-8",
    )


@pytest.fixture(scope="session")
def fi1_db(
        fi1_df: pd.DataFrame,  # noqa: ARG001
) -> Generator[tuple[duckdb.DuckDBPyConnection, str], None, None]:
    connection = duckdb.connect(":memory:")
    connection.sql("CREATE TABLE fi1_data AS FROM (SELECT * FROM fi1_df)")
    yield connection, "fi1_data"
    connection.sql("DROP TABLE fi1_data")


@pytest.fixture(scope="session")
def fake_pheno_db(fake_pheno_db_dir: str) -> PhenoRegistry:
    return PhenoRegistry.from_directory(fake_pheno_db_dir)


@pytest.fixture(scope="session")
def fake_phenotype_data_config() -> str:
    return relative_to_this_folder("fixtures/fake_phenoDB/main_fake/fake.yaml")


@pytest.fixture(scope="session")
def fake_phenotype_data(fake_pheno_db: PhenoRegistry) -> PhenotypeData:
    return fake_pheno_db.get_phenotype_data("fake")


@pytest.fixture(scope="session")
def fake_phenotype_data_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/main_fake/fake.db",
    )


@pytest.fixture(scope="session")
def fake_phenotype_data_i1_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/fake_i1/fake_i1.db",
    )


@pytest.fixture(scope="session")
def fake_phenotype_data_browser_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/main_fake/browser.db",
    )


@pytest.fixture(scope="session")
def dummy_pheno_missing_files_conf() -> str:
    return relative_to_this_folder("fixtures/dummy_pheno_missing_files.conf")


@pytest.fixture(scope="session")
def fake_pheno_config(fake_dae_conf: Box) -> Box:
    return GPFConfigParser.load_directory_configs(
        fake_dae_conf.phenotype_data.dir, pheno_conf_schema,
    )


@pytest.fixture(scope="session")
def fake_background_filename() -> str:
    return relative_to_this_folder("fixtures/background.csv")


@pytest.fixture(scope="session")
def fake_background_df(fake_background_filename: str) -> pd.DataFrame:
    return pd.read_csv(
        fake_background_filename, low_memory=False, encoding="utf-8",
    )


@pytest.fixture(scope="session")
def fake_background_db(
    fake_background_df: pd.DataFrame,  # noqa: ARG001
) -> Generator[tuple[duckdb.DuckDBPyConnection, str], None, None]:
    connection = duckdb.connect(":memory:")
    connection.sql(
        "CREATE TABLE fake_background_data AS FROM "
        "(SELECT * FROM fake_background_df)",
    )
    yield connection, "fake_background_data"
    connection.sql("DROP TABLE fake_background_data")


@pytest.fixture
def test_config(temp_dbfile: str) -> Box:
    config = default_config()
    config.db.filename = temp_dbfile
    return Box(config.to_dict())


@pytest.fixture
def temp_dbfile() -> Generator[str, None, None]:
    dirname = tempfile.mkdtemp(suffix="_ped", prefix="pheno_db_")

    yield os.path.join(dirname, "test_output.db")

    shutil.rmtree(dirname)


@pytest.fixture
def valid_descriptions() -> str:
    return relative_to_this_folder("fixtures/descriptions_valid.tsv")


@pytest.fixture
def invalid_descriptions() -> str:
    return relative_to_this_folder("fixtures/descriptions_invalid.tsv")


@pytest.fixture(scope="session")
def regressions_conf() -> str:
    return relative_to_this_folder("fixtures/regressions.conf")


@pytest.fixture
def temp_dirname_figures() -> Generator[str, None, None]:
    dirname = tempfile.mkdtemp(suffix="_plots", prefix="figures_")
    yield dirname
    shutil.rmtree(dirname)


@pytest.fixture
def fake_phenodb_file_copy(
    tmp_path: Path,
    fake_phenotype_data_i1_dbfile: str,
) -> str:
    temp_dbfile = str(tmp_path / "phenodb.db")
    shutil.copy(
        fake_phenotype_data_i1_dbfile,
        temp_dbfile,
    )
    return temp_dbfile


@pytest.fixture
def fake_browserdb_file_copy(
    tmp_path: Path,
    fake_phenotype_data_browser_dbfile,
) -> str:
    temp_dbfile = str(tmp_path / "browser.db")
    shutil.copy(
        fake_phenotype_data_browser_dbfile,
        temp_dbfile,
    )
    return temp_dbfile
