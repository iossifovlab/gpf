import pathlib
import textwrap

from dae.genomic_resources.gene_models.gene_models import (
    build_gene_models_from_resource,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import setup_directories
from dae.gpf_instance import GPFInstance


def setup_gpf_instance(
    out_path: pathlib.Path,
    reference_genome_id: str | None = None,
    gene_models_id: str | None = None,
    grr: GenomicResourceRepo | None = None,
) -> GPFInstance:
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(
            out_path, {
            "gpf_instance.yaml": textwrap.dedent(f"""
                instance_id: "test_instance"
                reference_genome:
                  resource_id: {reference_genome_id}
                gene_models:
                  resource_id: {gene_models_id}
            """),
        },
        )
    # pylint: disable=import-outside-toplevel
    reference_genome = None
    if reference_genome_id is not None:
        assert grr is not None
        res = grr.get_resource(reference_genome_id)
        reference_genome = build_reference_genome_from_resource(res)
        reference_genome.open()
    gene_models = None
    if gene_models_id is not None:
        assert grr is not None
        res = grr.get_resource(gene_models_id)
        gene_models = build_gene_models_from_resource(res)
        gene_models.load()

    return GPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)
