# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import textwrap
import requests

import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models
from ..testing import setup_wgpf_instance


@pytest.fixture
def wgpf_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("eager_loading_wgpf_instance")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        """),
    })
    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )
    return gpf


def test_eager_loading(mocker, wgpf_fixture, wdae_django_server):

    mocker.patch.object(
        wgpf_fixture,
        "get_all_genotype_data",
        return_value=[]
    )
    mocker.patch.object(
        wgpf_fixture,
        "load",
        return_value=wgpf_fixture
    )

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        assert server.url.startswith("http://localhost")
        assert wgpf_fixture.load.called
        assert wgpf_fixture.get_all_genotype_data.called


def test_no_eager_loading(mocker, wgpf_fixture, wdae_django_server):

    mocker.patch.object(
        wgpf_fixture,
        "get_all_genotype_data",
        return_value=[]
    )
    mocker.patch.object(
        wgpf_fixture,
        "load",
        return_value=wgpf_fixture
    )

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_false_settings") as server:

        assert server.url.startswith("http://localhost")
        assert not wgpf_fixture.load.called
        assert not wgpf_fixture.get_all_genotype_data.called


@pytest.mark.skip
def test_example_request(mocker, wgpf_fixture, wdae_django_server):

    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        response = requests.get(f"{server.url}/api/v3/datasets")

        assert response.status_code == 200
        assert "data" in response.json()
        data = response.json()["data"]
        assert len(data) == 0
