# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
import os
from box import Box

from dae.pheno.registry import PhenoRegistry


def test_pheno_config_loading(fake_pheno_config: list[Box]) -> None:
    assert all(
        db.phenotype_data.name in (
            "fake_group", "fake", "fake2", "dummy_1", "dummy_2"
        )
        for db in fake_pheno_config
    )


@pytest.mark.xfail(reason="Old API")
def test_existing_attributes(fake_pheno_db: PhenoRegistry) -> None:
    dummy_1 = fake_pheno_db.get_dbconfig("dummy_1")
    assert os.path.isfile(dummy_1["dbfile"]), print
    assert os.path.isfile(dummy_1["browser_dbfile"])
    assert dummy_1.get("browser_images_url") == "static/dummy-images"


@pytest.mark.xfail(reason="Old API")
def test_missing_attributes(fake_pheno_db: PhenoRegistry) -> None:
    dummy_2 = fake_pheno_db.get_dbconfig("dummy_2")
    assert dummy_2["dbfile"] is None
    assert dummy_2["browser_dbfile"] is None
    assert dummy_2["browser_images_url"] is None
