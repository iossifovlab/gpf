# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import textwrap
import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models
from ..testing import setup_wgpf_instance


@pytest.fixture
def wgpf_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("wgpf_command")

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