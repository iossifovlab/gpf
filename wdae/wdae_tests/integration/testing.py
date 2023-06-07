import pathlib

from dae.testing import setup_directories
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import \
    build_gene_models_from_resource


def setup_wgpf_instance(
        out_path: pathlib.Path,
        reference_genome_id=None, gene_models_id=None,
        grr=None):
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(out_path, {"gpf_instance.yaml": ""})
    # pylint: disable=import-outside-toplevel
    from gpf_instance.gpf_instance import WGPFInstance
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

    gpf = WGPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)

    gpf.instance_dir = out_path
    gpf.instance_config = gpf.instance_dir / "gpf_instance.yaml"

    return gpf
