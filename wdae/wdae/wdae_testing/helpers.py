
import pathlib
from typing import Optional

from gpf_instance.gpf_instance import WGPFInstance  # , reset_wgpf_instance

from dae.testing import setup_directories
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource, ReferenceGenome
from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource, GeneModels
from dae.genomic_resources.repository import GenomicResourceRepo


def setup_wgpf_instance(
    out_path: pathlib.Path,
    reference_genome: Optional[ReferenceGenome] = None,
    reference_genome_id: Optional[str] = None,
    gene_models: Optional[GeneModels] = None,
    gene_models_id: Optional[str] = None,
    grr: Optional[GenomicResourceRepo] = None
) -> WGPFInstance:
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(out_path, {"gpf_instance.yaml": ""})
    if reference_genome is None:
        if reference_genome_id is not None:
            assert grr is not None
            res = grr.get_resource(reference_genome_id)
            reference_genome = build_reference_genome_from_resource(res)
            reference_genome.open()
    if gene_models is None:
        if gene_models_id is not None:
            assert grr is not None
            res = grr.get_resource(gene_models_id)
            gene_models = build_gene_models_from_resource(res)
            gene_models.load()

    gpf = WGPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)

    gpf.instance_dir = out_path  # type: ignore
    gpf.instance_config = out_path / "gpf_instance.yaml"  # type: ignore

    return gpf
