import pathlib
from dae.genomic_resources.testing import setup_directories


def setup_gpf_instance(
        out_path: pathlib.Path,
        reference_genome=None, gene_models=None,
        grr=None):
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(out_path, {"gpf_instance.yaml": ""})
    # pylint: disable=import-outside-toplevel
    from dae.gpf_instance import GPFInstance
    return GPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)
