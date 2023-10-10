# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from typing import Callable, cast

from box import Box

import pytest

from dae.genotype_storage.genotype_storage_registry import \
    GenotypeStorageRegistry
from dae.pheno.pheno_db import PhenoDb
from dae.gene.gene_scores import GeneScoresDb
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.studies.variants_db import VariantsDb


@pytest.fixture(scope="session")
def fixtures_dir(global_dae_fixtures_dir: str) -> str:
    return global_dae_fixtures_dir


@pytest.fixture(scope="session")
def studies_dir(fixtures_dir: str) -> str:
    return os.path.abspath(os.path.join(fixtures_dir, "studies"))


@pytest.fixture(scope="session")
def genotype_data_groups_dir(fixtures_dir: str) -> str:
    return os.path.abspath(os.path.join(fixtures_dir, "datasets"))


@pytest.fixture(scope="session")
def local_gpf_instance(
    gpf_instance: Callable[[str], GPFInstance], fixtures_dir: str
) -> GPFInstance:
    return gpf_instance(os.path.join(fixtures_dir, "gpf_instance.yaml"))


@pytest.fixture(scope="session")
def dae_config_fixture(local_gpf_instance: GPFInstance) -> Box:
    return cast(Box, local_gpf_instance.dae_config)


@pytest.fixture(scope="session")
def variants_db_fixture(local_gpf_instance: GPFInstance) -> VariantsDb:
    return cast(VariantsDb, local_gpf_instance._variants_db)


@pytest.fixture(scope="session")
def pheno_db(local_gpf_instance: GPFInstance) -> PhenoDb:
    return cast(PhenoDb, local_gpf_instance._pheno_db)


@pytest.fixture(scope="session")
def gene_scores_db(local_gpf_instance: GPFInstance) -> GeneScoresDb:
    return cast(GeneScoresDb, local_gpf_instance.gene_scores_db)


@pytest.fixture(scope="session")
def genotype_storage_factory(
    local_gpf_instance: GPFInstance
) -> GenotypeStorageRegistry:
    return cast(GenotypeStorageRegistry, local_gpf_instance.genotype_storages)


@pytest.fixture(scope="session")
def genotype_data_study_configs(
    variants_db_fixture: VariantsDb
) -> dict[str, Box]:
    return cast(dict[str, Box], variants_db_fixture._load_study_configs())


@pytest.fixture(scope="session")
def quads_f1_config(variants_db_fixture: VariantsDb) -> GenotypeData:
    return cast(
        GenotypeData,
        variants_db_fixture.get_genotype_study_config("quads_f1"))


@pytest.fixture(scope="session")
def genotype_data_group_configs(
    variants_db_fixture: VariantsDb
) -> dict[str, Box]:
    return cast(dict[str, Box], variants_db_fixture._load_group_configs())


@pytest.fixture(scope="session")
def quads_composite_genotype_data_group_config(
    variants_db_fixture: VariantsDb
) -> Box:
    return cast(
        Box,
        variants_db_fixture.get_genotype_group_config("quads_composite_ds"))


@pytest.fixture(scope="session")
def composite_dataset_config(
    variants_db_fixture: VariantsDb
) -> Box:
    return cast(
        Box,
        variants_db_fixture.get_genotype_group_config("composite_dataset_ds"))
