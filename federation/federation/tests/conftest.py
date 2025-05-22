# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap
from typing import cast

import pytest
import pytest_mock
from django.test import Client
from gpf_instance.gpf_instance import (
    WGPFInstance,
    reload_datasets,
)
from utils.testing import (
    _study_1_pheno,
    _t4c8_dataset,
    _t4c8_default_study_config,
    _t4c8_study_1,
    _t4c8_study_2,
    _t4c8_study_4,
    setup_gpf_instance,
    setup_t4c8_grr,
)

from dae.gene_sets.denovo_gene_set_helpers import DenovoGeneSetHelpers
from dae.testing import (
    setup_directories,
)
from federation.remote_extension import load_extension
from federation.rest_api_client import RESTClient
from rest_client.rest_client import GPFConfidentialClient


def setup_remote_t4c8_instance(
    root_path: pathlib.Path,
) -> WGPFInstance:
    t4c8_grr = setup_t4c8_grr(root_path)

    instance_path = root_path / "gpf_instance"

    _t4c8_default_study_config(instance_path)

    setup_directories(
        instance_path, {
            "gpf_instance.yaml": textwrap.dedent("""
                instance_id: t4c8_instance
                annotation:
                  conf_file: annotation.yaml
                reference_genome:
                  resource_id: t4c8_genome
                gene_models:
                  resource_id: t4c8_genes
                gene_scores_db:
                  gene_scores:
                  - "gene_scores/t4c8_score"
                gene_sets_db:
                  gene_set_collections:
                  - gene_sets/main
                default_study_config:
                  conf_file: default_study_configuration.yaml
                genotype_storage:
                  default: duckdb_wgpf_test
                  storages:
                  - id: duckdb_wgpf_test
                    storage_type: duckdb_parquet
                    memory_limit: 16GB
                    base_dir: '%(wd)s/duckdb_storage'
                gpfjs:
                  visible_datasets:
                  - t4c8_dataset
                  - t4c8_study_1
                  - nonexistend_dataset
                remotes:
                  - id: "TEST_REMOTE"
                    host: "localhost"
                    base_url: "api/v3"
                    port: 21010
                    credentials: "ZmVkZXJhdGlvbjpzZWNyZXQ="
            """),
            "annotation.yaml": textwrap.dedent("""
               - position_score: genomic_scores/score_one
            """),
        },
    )

    _study_1_pheno(
        root_path,
        instance_path,
    )

    gpf_instance = setup_gpf_instance(
        instance_path,
        grr=t4c8_grr,
    )

    _t4c8_study_1(root_path, gpf_instance)
    _t4c8_study_2(root_path, gpf_instance)
    _t4c8_dataset(gpf_instance)
    _t4c8_study_4(root_path, gpf_instance)

    gpf_instance.reload()

    for study_id in [
            "t4c8_study_1", "t4c8_study_2", "t4c8_dataset", "t4c8_study_4"]:
        study = gpf_instance.get_genotype_data(study_id)
        assert study is not None, study_id
        DenovoGeneSetHelpers.build_collection(study)

    gpf_instance.reload()

    instance_filename = str(instance_path / "gpf_instance.yaml")
    wgpf_instance = WGPFInstance.build(instance_filename, grr=t4c8_grr)

    load_extension(wgpf_instance)
    return cast(WGPFInstance, wgpf_instance)


@pytest.fixture(scope="session")
def remote_t4c8_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("remote_t4c8_instance")
    return setup_remote_t4c8_instance(root_path)


@pytest.fixture
def remote_t4c8_wgpf_instance(
    remote_t4c8_instance: WGPFInstance,
    db: None,  # noqa: ARG001
    mocker: pytest_mock.MockFixture,
) -> WGPFInstance:
    reload_datasets(remote_t4c8_instance)
    mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=remote_t4c8_instance,
    )
    mocker.patch(
        "datasets_api.permissions.get_wgpf_instance",
        return_value=remote_t4c8_instance,
    )
    mocker.patch(
        "query_base.query_base.get_wgpf_instance",
        return_value=remote_t4c8_instance,
    )

    return remote_t4c8_instance


@pytest.fixture
def remote_config() -> dict[str, str]:
    host = os.environ.get("TEST_REMOTE_HOST", "localhost")
    return {
        "id": "TEST_REMOTE",
        "host": host,
        "base_url": "api/v3",
        "port": "21010",
        "client_id": "federation",
        "client_secret": "secret",
    }


@pytest.fixture
def rest_client(
    admin_client: Client,  # noqa: ARG001
    remote_config: dict[str, str],
    remote_t4c8_wgpf_instance,  # noqa: ARG001
) -> RESTClient:
    client = RESTClient(
        remote_config["id"],
        remote_config["host"],
        remote_config["client_id"],
        remote_config["client_secret"],
        base_url=remote_config["base_url"],
        port=int(remote_config["port"]),
    )

    assert isinstance(client.gpf_rest_client.session,
                      GPFConfidentialClient)
    assert client.gpf_rest_client.session.token is not None, \
        "Failed to get auth token for REST client"

    return client
