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


def alla_genome(root_path: pathlib.Path) -> ReferenceGenome:
    return setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {100 * "A"}
        >chr2
        {100 * "A"}
        >chr3
        {100 * "A"}
        >chr4
        {100 * "A"}
        >chrX
        {100 * "A"}
        """,
    )


def alla_grr(root_path: pathlib.Path) -> GenomicResourceRepo:
    alla_genome(root_path)
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    return build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })
