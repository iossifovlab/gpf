# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path
from remote.rest_api_client import RESTClient

import pytest
from studies.study_wrapper import RemoteStudyWrapper, StudyWrapper, \
    StudyWrapperBase
from studies.remote_study import RemoteGenotypeData
from dae.gpf_instance.gpf_instance import GPFInstance


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
        local_gpf_instance._pheno_db,
        local_gpf_instance.gene_scores_db
    )


@pytest.fixture(scope="function")
def iossifov_2014_remote(rest_client: RESTClient) -> StudyWrapperBase:
    return RemoteStudyWrapper(
        RemoteGenotypeData("iossifov_2014", rest_client)
    )


@pytest.fixture(scope="function")
def iossifov_2014_wrappers(
    iossifov_2014_local: StudyWrapperBase,
    iossifov_2014_remote: StudyWrapperBase
) -> dict[str, StudyWrapperBase]:
    return {
        "local": iossifov_2014_local,
        "remote": iossifov_2014_remote
    }
