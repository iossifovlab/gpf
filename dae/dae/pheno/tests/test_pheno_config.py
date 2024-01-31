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
