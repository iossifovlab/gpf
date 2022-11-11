import pathlib
from typing import Any, Dict, Union

import pysam


def convert_to_tab_separated(content: str):
    """Convert a string into tab separated file content.

    Useful for testing purposes.
    If you need to have a space in the file content use '||'.
    """
    result = []
    for line in content.split("\n"):
        line = line.strip("\n\r")
        if not line:
            continue
        if line.startswith("##"):
            result.append(line)
        else:
            result.append("\t".join(line.split()))
    text = "\n".join(result)
    return text.replace("||", " ")


def setup_directories(
        root_dir: pathlib.Path,
        content: Union[str, Dict[str, Any]]) -> None:
    """Set up directory and subdirectory structures using the content."""
    root_dir = pathlib.Path(root_dir)
    root_dir.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        root_dir.write_text(content, encoding="utf8")
    elif isinstance(content, dict):
        for path_name, path_content in content.items():
            setup_directories(root_dir / path_name, path_content)
    else:
        raise ValueError(
            f"unexpected content type: {path_content} for {path_name}")


def setup_pedigree(ped_path, content):
    ped_data = convert_to_tab_separated(content)
    setup_directories(ped_path, ped_data)
    return str(ped_path)


def setup_denovo(denovo_path, content):
    denovo_data = convert_to_tab_separated(content)
    setup_directories(denovo_path, denovo_data)
    return str(denovo_path)


def setup_vcf(out_path: pathlib.Path, content):
    """Set up a VCF file using the content."""
    vcf_data = convert_to_tab_separated(content)
    vcf_path = out_path
    if out_path.suffix == ".gz":
        vcf_path = out_path.with_suffix("")

    setup_directories(vcf_path, vcf_data)

    if out_path.suffix == ".gz":
        vcf_gz_filename = str(vcf_path.parent / f"{vcf_path.name}.gz")
        # pylint: disable=no-member
        pysam.tabix_compress(str(vcf_path), vcf_gz_filename)
        pysam.tabix_index(vcf_gz_filename, preset="vcf")

    return str(out_path)


def setup_dae_transmitted(root_path, summary_content, toomany_content):
    """Set up a DAE transmitted variants file using passed content."""
    summary = convert_to_tab_separated(summary_content)
    toomany = convert_to_tab_separated(toomany_content)

    setup_directories(root_path, {
        "dae_transmitted_data": {
            "tr.txt": summary,
            "tr-TOOMANY.txt": toomany
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr.txt"),
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"))
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt"),
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))

    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)

    return (str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
            str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))


def setup_genome(out_path: pathlib.Path, content):
    """Set up reference genome using the content."""
    if out_path.suffix != ".fa":
        raise ValueError("genome output file is expected to have '.fa' suffix")
    setup_directories(out_path, convert_to_tab_separated(content))

    # pylint: disable=no-member
    pysam.faidx(str(out_path))  # type: ignore

    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.reference_genome import \
        build_reference_genome_from_file
    return build_reference_genome_from_file(str(out_path)).open()


def setup_gene_models(out_path: pathlib.Path, content, fileformat=None):
    """Set up gene models in refflat format using the passed content."""
    setup_directories(out_path, convert_to_tab_separated(content))
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.gene_models import build_gene_models_from_file
    return build_gene_models_from_file(str(out_path), fileformat=fileformat)


def setup_empty_gene_models(out_path: pathlib.Path):
    """Set up empty gene models."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
    """  # noqa
    return setup_gene_models(out_path, content, fileformat="refflat")


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
