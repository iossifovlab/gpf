# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path

import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from studies.study_wrapper import (
    StudyWrapper,
    StudyWrapperBase,
)


@pytest.fixture(scope="session")
def local_dir() -> Path:
    return Path(__file__).parents[4].joinpath("data/data-hg19-local")


@pytest.fixture(scope="session")
def local_gpf_instance(local_dir: Path) -> GPFInstance:
    return GPFInstance.build(local_dir / "gpf_instance.yaml")


@pytest.fixture(scope="session")
def iossifov_2014_local(
        local_gpf_instance: GPFInstance) -> StudyWrapperBase:

    data_study = local_gpf_instance.get_genotype_data("iossifov_2014")

    return StudyWrapper(
        data_study,
        local_gpf_instance._pheno_registry,  # noqa: SLF001
        local_gpf_instance.gene_scores_db,
        local_gpf_instance,
    )


@pytest.fixture()
def iossifov_2014_wrappers(
    iossifov_2014_local: StudyWrapperBase,
) -> dict[str, StudyWrapperBase]:
    return {
        "local": iossifov_2014_local,
    }
