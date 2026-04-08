# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

from gain.genomic_resources.reference_genome import ReferenceGenome
from gain.genomic_resources.repository import GenomicResourceRepo
from gain.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from gain.genomic_resources.testing import (
    setup_empty_gene_models,
    setup_genome,
)


def acgt_genome(root_path: pathlib.Path) -> ReferenceGenome:
    return setup_genome(
        root_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """,
    )


def acgt_grr(root_path: pathlib.Path) -> GenomicResourceRepo:
    acgt_genome(root_path)
    setup_empty_gene_models(
        root_path / "acgt_gpf" / "empty_gene_models" / "empty_genes.txt")
    return build_genomic_resource_repository({
        "id": "acgt_local",
        "type": "directory",
        "directory": str(root_path / "acgt_gpf"),
    })
