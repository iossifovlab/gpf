# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import textwrap
import requests

import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models, setup_pedigree, setup_vcf, vcf_study
from ..testing import setup_wgpf_instance


@pytest.fixture
def alla_wgpf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("alla_wgpf_instance")

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


def test_empty_wgpf_instance_study(alla_wgpf, wdae_django_server):

    with wdae_django_server(
            alla_wgpf,
            "tests.integration.test_wgpf_instance."
            "wgpf_settings") as server:

        assert server.url.startswith("http://localhost")
        response = requests.get(f"{server.url}/api/v3/datasets")

        assert response.status_code == 200
        assert "data" in response.json()
        data = response.json()["data"]
        assert len(data) == 1