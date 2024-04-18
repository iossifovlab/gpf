# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import textwrap

import pytest
from gpf_instance.gpf_instance import WGPFInstance

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import setup_directories, setup_empty_gene_models, setup_genome
from wdae_tests.integration.testing import setup_wgpf_instance


@pytest.fixture()
def wgpf_fixture(tmp_path_factory: pytest.TempPathFactory) -> WGPFInstance:
    root_path = tmp_path_factory.mktemp("wgpf_command")

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
