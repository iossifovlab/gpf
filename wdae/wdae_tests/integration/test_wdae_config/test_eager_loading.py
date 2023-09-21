# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import os
import textwrap
import requests
from typing import Callable, ContextManager

import pytest
import pytest_mock

from oauth2_provider.models import get_application_model
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


from gpf_instance.gpf_instance import WGPFInstance

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models, setup_pedigree, setup_vcf
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from remote.rest_api_client import RESTClient
from users_api.models import WdaeUser

from wdae_tests.integration.testing import setup_wgpf_instance, \
    LiveServer



@pytest.fixture
def wgpf_fixture(tmp_path_factory: pytest.TempPathFactory) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("eager_loading_wgpf_instance")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        """),
    })
    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf")
    })

    setup_directories(root_path /  "gpf_instance" / "studies" / "test_study", {
        "test_study.yaml": textwrap.dedent("""
        id: test_study
        conf_dir: .
        has_denovo: False
        has_cnv: False
        genotype_storage:
          id: internal
          files:
            pedigree:
              path: test_study.ped
            variants:
            - path: test_study.vcf
              format: vcf
        """),
    })
    setup_pedigree(
        root_path / "gpf_instance" / "studies" / "test_study" / "test_study.ped",
        """
familyId personId dadId momId sex status role
f1       mom1     0     0     2   1      mom
f1       dad1     0     0     1   1      dad
f1       prb1     dad1  mom1  1   2      prb
f1       sib1     dad1  mom1  2   2      sib
        """)
    setup_vcf(
        root_path / "gpf_instance" / "studies" / "test_study" / "test_study.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
##contig=<ID=chr2>
##contig=<ID=chr3>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 prb1 sib1
chr1   1   .  A   C   .    .      .    GT     0/1  0/0  0/1  0/0
chr2   1   .  A   C   .    .      .    GT     0/0  0/1  0/1  0/0
chr3   1   .  A   C   .    .      .    GT     0/0  0/1  0/0  0/1
        """)  # noqa

    gpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo
    )
    return gpf


@pytest.fixture()
def admin(db):
    user_model = get_user_model()
    new_user = user_model.objects.create(
        email="admin@example.com",
        name="Admin",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    new_user.set_password("secret")
    new_user.save()

    admin_group, _ = Group.objects.get_or_create(name=WdaeUser.SUPERUSER_GROUP)
    new_user.groups.add(admin_group)

    return new_user


def test_rest_client_on_remote(wdae_django_server, wgpf_fixture, admin):
    with wdae_django_server(
            wgpf_fixture,
            "wdae_tests.integration.test_wdae_config."
            "eager_loading_true_settings") as server:
        User = get_user_model()
        Application = get_application_model()
        user = User.objects.get(id=1)  # Get admin user, should be the first one

        new_application = Application(**{
            "name": "remote federation testing app",
            "user_id": user.id,
            "client_type": "confidential",
            "authorization_grant_type": "client-credentials",
            "client_id": "federation",
            "client_secret": "secret"
        })

        new_application.full_clean()
        new_application.save()
        client = RESTClient("test", server.thread.host, "ZmVkZXJhdGlvbjpzZWNyZXQ=", base_url="api/v3", port=server.thread.port)
        datasets = client.get_datasets()
        assert datasets is not None
        assert len(datasets["data"]) == 1
        print(datasets)
        assert datasets["data"][0]["id"] == "test_study"


def test_eager_loading(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]]
) -> None:

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
        assert wgpf_fixture.load.called  # type: ignore
        assert wgpf_fixture.get_all_genotype_data.called  # type: ignore


def test_no_eager_loading(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]]
) -> None:

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
        assert not wgpf_fixture.load.called  # type: ignore
        assert not wgpf_fixture.get_all_genotype_data.called  # type: ignore


def test_example_request(
    mocker: pytest_mock.MockerFixture,
    wgpf_fixture: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]]
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
