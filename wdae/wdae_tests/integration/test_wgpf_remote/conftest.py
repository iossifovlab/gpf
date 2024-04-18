# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

import contextlib
import textwrap
import time
from collections.abc import Generator
from typing import Callable, ContextManager

import pytest
from gpf_instance.gpf_instance import WGPFInstance

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import (
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from wdae_tests.integration.testing import LiveServer, setup_wgpf_instance


@pytest.fixture()
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


@pytest.fixture()
def remote_wgpf_instance(
    alla_wgpf: WGPFInstance,
    wdae_django_server: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> Callable[[], ContextManager[LiveServer]]:

    @contextlib.contextmanager
    def builder() -> Generator[LiveServer, None, None]:
        with wdae_django_server(
                alla_wgpf,
                "wdae_tests.integration.test_wdae_remote."
                "remote_settings") as server:
            time.sleep(0.5)
            yield server

    return builder
