# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import json

import pytest
import pytest_mock
import pytest_django

from django.test.client import Client

from gpf_instance.gpf_instance import WGPFInstance, reset_wgpf_instance
from wdae_testing.helpers import setup_wgpf_instance

from dae.testing import setup_pedigree, setup_vcf, vcf_study, alla_gpf


@pytest.fixture(scope="module")
def alla_wgpf(
    tmp_path_factory: pytest.TempPathFactory,
    module_mocker: pytest_mock.MockFixture
) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("alla_wgpf_instance")
    gpf = alla_gpf(root_path)

    wgpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome_id=gpf.reference_genome.resource_id,
        gene_models_id=gpf.gene_models.resource_id,
        grr=gpf.grr
    )
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT  QUAL FILTER INFO FORMAT m1  d1  p1
        chrA   1   .  A   T    .    .      .    GT     0/1 0/0 0/1
        """)

    vcf_study(
        root_path,
        "study", ped_path, [vcf_path],
        wgpf)

    module_mocker.patch(
        "gpf_instance.gpf_instance.get_wgpf_instance",
        return_value=wgpf)
    reset_wgpf_instance(wgpf)

    return wgpf


def test_empty_wgpf_instance_study(
    alla_wgpf: WGPFInstance,
    admin_client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    response = admin_client.get("/api/v3/datasets/studies")
    assert response.status_code == 200

    response_data = json.loads(response.content)
    assert response_data is not None
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "study"


def test_default_permission_denied_prompt(
    alla_wgpf: WGPFInstance,
    user_client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    response = user_client.get("/api/v3/datasets/denied_prompt")

    assert response
    assert response.status_code == 200
    response_data = json.loads(response.content)

    assert response_data["data"] == (
        "The Genotype and Phenotype in Families (GPF) data is accessible by "
        + "registered users. Contact the system administrator of the "
        + "GPF system to get an account in the system and get permission "
        + "to access the data."
    )
