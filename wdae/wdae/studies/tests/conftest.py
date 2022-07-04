# pylint: disable=W0621,C0114,C0116,W0212,W0613
from pathlib import Path

import pytest
from studies.study_wrapper import RemoteStudyWrapper, StudyWrapper
from studies.remote_study import RemoteGenotypeData
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="session")
def local_dir():
    return Path(__file__).parents[4].joinpath("data/data-hg19-local")


@pytest.fixture(scope="session")
def local_gpf_instance(local_dir):
    return GPFInstance(work_dir=local_dir)


@pytest.fixture(scope="session")
def iossifov_2014_local(
        local_gpf_instance):

    data_study = local_gpf_instance.get_genotype_data("iossifov_2014")

    return StudyWrapper(
        data_study,
        local_gpf_instance._pheno_db,
        local_gpf_instance.gene_scores_db
    )


@pytest.fixture(scope="function")
def iossifov_2014_remote(rest_client):
    return RemoteStudyWrapper(
        RemoteGenotypeData("iossifov_2014", rest_client)
    )


@pytest.fixture(scope="function")
def iossifov_2014_wrappers(iossifov_2014_local, iossifov_2014_remote):
    return {
        "local": iossifov_2014_local,
        "remote": iossifov_2014_remote
    }
