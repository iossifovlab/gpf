# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import os
import textwrap
import json

import pytest
import pytest_django

from django.test.client import Client

from gpf_instance.gpf_instance import WGPFInstance
from wdae_testing.helpers import setup_wgpf_instance

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models, setup_pedigree, setup_vcf, vcf_study
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository


@pytest.fixture
def alla_wgpf(tmp_path_factory: pytest.TempPathFactory) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("alla_wgpf_instance")

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

    gpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo
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
        gpf)

    return gpf


def test_empty_wgpf_instance_study(
    alla_wgpf: WGPFInstance,
    admin_client: Client,
    settings: pytest_django.fixtures.SettingsWrapper
) -> None:
    settings.GPF_INSTANCE_CONFIG = os.path.join(
        alla_wgpf.dae_dir, "gpf_instance.yaml")

    response = admin_client.get("/api/v3/datasets/studies")
    assert response.status_code == 200

    response_data = json.loads(response.content)
    assert response_data is not None
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "study"


def test_default_permission_denied_prompt(
    alla_wgpf: WGPFInstance,
    user_client: Client,
    settings: pytest_django.fixtures.SettingsWrapper
) -> None:
    settings.GPF_INSTANCE_CONFIG = os.path.join(
        alla_wgpf.dae_dir, "gpf_instance.yaml")

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
