# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import textwrap
import requests

import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models, setup_gpf_instance


@pytest.fixture
def gpf_fixture(tmp_path_factory):
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
    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )
    return gpf


def test_eager_loading(mocker, gpf_fixture, wdae_django_setup):

    mocker.patch.object(
        gpf_fixture,
        "get_all_genotype_data",
        return_value=[]
    )
    mocker.patch.object(
        gpf_fixture,
        "load",
        return_value=gpf_fixture
    )

    with wdae_django_setup(
            gpf_fixture,
            "tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        assert server.url.startswith("http://localhost")
        assert gpf_fixture.load.called
        assert gpf_fixture.get_all_genotype_data.called


def test_no_eager_loading(mocker, gpf_fixture, wdae_django_setup):

    mocker.patch.object(
        gpf_fixture,
        "get_all_genotype_data",
        return_value=[]
    )
    mocker.patch.object(
        gpf_fixture,
        "load",
        return_value=gpf_fixture
    )

    with wdae_django_setup(
            gpf_fixture,
            "tests.integration.test_wdae_config."
            "eager_loading_false_settings") as server:

        assert server.url.startswith("http://localhost")
        assert not gpf_fixture.load.called
        assert not gpf_fixture.get_all_genotype_data.called


def test_example_request(mocker, gpf_fixture, wdae_django_setup):

    with wdae_django_setup(
            gpf_fixture,
            "tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:

        assert server.url.startswith("http://localhost")
        response = requests.get(f"{server.url}/api/v3/datasets")

        assert response.status_code == 200
        assert "data" in response.json()
        data = response.json()["data"]
        assert len(data) == 0
