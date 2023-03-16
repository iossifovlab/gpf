import pathlib

from dae.testing import setup_directories


def setup_wgpf_instance(
        out_path: pathlib.Path,
        reference_genome=None, gene_models=None,
        grr=None):
    """Set up a GPF instance using prebuild genome, gene models, etc."""
    if not (out_path / "gpf_instance.yaml").exists():
        setup_directories(out_path, {"gpf_instance.yaml": ""})
    # pylint: disable=import-outside-toplevel
    from gpf_instance.gpf_instance import WGPFInstance
    gpf = WGPFInstance.build(
        out_path / "gpf_instance.yaml",
        reference_genome=reference_genome, gene_models=gene_models,
        grr=grr)

    gpf.instance_dir = out_path
    gpf.instance_config = gpf.instance_dir / "gpf_instance.yaml"

    return gpf
