# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import textwrap
from typing import Callable, ContextManager

import pytest
import pytest_mock
import requests
from gpf_instance.gpf_instance import WGPFInstance

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import setup_directories, setup_empty_gene_models, setup_genome
from wdae_tests.integration.testing import LiveServer, setup_wgpf_instance


@pytest.fixture()
def wgpf_fixture(tmp_path_factory: pytest.TempPathFactory) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("eager_loading_wgpf_instance")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
            instance_id: test
        """),
    })
    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })

    gpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )
    return gpf


def test_eager_loading(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> None:

    mocker.patch.object(
        wgpf_fixture,
        "get_all_genotype_data",
        return_value=[],
    )
    mocker.patch.object(
        wgpf_fixture,
        "load",
        return_value=wgpf_fixture,
    )

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        assert server.url.startswith("http://localhost")
        assert wgpf_fixture.load.called  # type: ignore
        assert wgpf_fixture.get_all_genotype_data.called  # type: ignore


def test_no_eager_loading(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> None:

    mocker.patch.object(
        wgpf_fixture,
        "get_all_genotype_data",
        return_value=[],
    )
    mocker.patch.object(
        wgpf_fixture,
        "load",
        return_value=wgpf_fixture,
    )

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_false_settings") as server:

        assert server.url.startswith("http://localhost")
        assert not wgpf_fixture.load.called  # type: ignore
        assert not wgpf_fixture.get_all_genotype_data.called  # type: ignore


def test_example_request(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> None:

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        response = requests.get(
            f"{server.url}/api/v3/datasets", timeout=5.0)

        assert response.status_code == 200
        assert "data" in response.json()
        data = response.json()["data"]
        assert len(data) == 0
