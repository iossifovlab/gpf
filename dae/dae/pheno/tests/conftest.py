# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from dae.pheno.browser import PhenoBrowser
from dae.pheno.pheno_data import PhenotypeData
from dae.pheno.registry import PhenoRegistry


def relative_to_this_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def fake_pheno_db_dir() -> Path:
    return Path(relative_to_this_folder("fixtures/fake_phenoDB"))


@pytest.fixture(scope="session")
def fake_phenotype_data_config() -> str:
    return relative_to_this_folder("fixtures/fake_phenoDB/main_fake/fake.yaml")


@pytest.fixture(scope="session")
def fake_phenotype_data(fake_pheno_db: PhenoRegistry) -> PhenotypeData:
    return fake_pheno_db.get_phenotype_data("fake")


@pytest.fixture(scope="session")
def fake_phenotype_data_browser_dbfile() -> str:
    return relative_to_this_folder(
        "fixtures/fake_phenoDB/main_fake/browser.db",
    )


@pytest.fixture(scope="session")
def fake_pheno_browser(fake_phenotype_data_browser_dbfile: str) -> PhenoBrowser:
    return PhenoBrowser(fake_phenotype_data_browser_dbfile)


@pytest.fixture
def temp_dbfile() -> Generator[str, None, None]:
    dirname = tempfile.mkdtemp(suffix="_ped", prefix="pheno_db_")

    yield os.path.join(dirname, "test_output.db")

    shutil.rmtree(dirname)


@pytest.fixture(scope="session")
def regressions_conf() -> str:
    return relative_to_this_folder("fixtures/regressions.conf")


@pytest.fixture
def temp_dirname_figures() -> Generator[str, None, None]:
    dirname = tempfile.mkdtemp(suffix="_plots", prefix="figures_")
    yield dirname
    shutil.rmtree(dirname)


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
