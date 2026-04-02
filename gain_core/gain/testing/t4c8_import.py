# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

from gain.genomic_resources.cli import cli_manage
from gain.genomic_resources.gene_models import GeneModels
from gain.genomic_resources.reference_genome import ReferenceGenome
from gain.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from gain.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from gain.genomic_resources.testing import (
    setup_directories,
    setup_gene_models,
    setup_genome,
)

GENOME_CONTENT = (
    ">chr1\n"
    """TTGTGTGAAGATGGAGGTAGGCCAGTTTCCCGGAGAGGTGAACAGACATTC"""
    #  0         1    1         2          3        4    5
    #  1     6   1    6         6          7        6    1
    #        ====|M1|E2---------|F3|P4|G5|E6--------|T7|F8
    """CATACAACCATGGTGAAATAGTCCTTCCTGTTACACAAG"""
    #  |H9|T0|T1|M2|V3|K|S =============
    #  5                   7       8   8     9
    #  2                   2       0   4     0
    #
    """NNNNNNNNAT"""
    #  9        1
    #  1        0
    #           0
    """AAGGATGGGGCTTCAGTCATCAGCGTGATGACCCTAGGATCTCACCTTTTTCCCATT"""
    #  ============|S<|D |D |A |H |H<|G<|-----------|K |K |G |N<
    #  1        1  1 1            1  1 1            1        1 1
    #  0        1  1 1            2  3 3            4        5 5
    #  1        0  3 5            8 01 3            6        5 7
    """GGGGTCTGCCATCTTGGGAAAGAACTCCTGTTGGCCTACCTGTGCCTCAAANN"""
    #  |P |D<|A<|M<|==============------------=========
    #  1 1  1  1  11             1            1       2    2
    #  5 6  6  6  67             8            9       0    1
    #  8 0  3  6  90             3            6       4    0
)


# This content follows the 'refflat' gene model format
# Coordinates in refflat gene models are 0-base.
# Regions are half open. Closed at the start and open at the end - [start, end)
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts  exonEnds
t4        tx1  chr1  +      5       84    10       71     3         5,25,45     16,37,84
c8        tx1  chr1  -      100     204   112      169    3         100,145,195 133,183,204
"""  # noqa


def t4c8_genome(root_path: pathlib.Path) -> ReferenceGenome:
    return setup_genome(
        root_path / "t4c8_genome" / "chrAll.fa", GENOME_CONTENT)


def t4c8_genes(root_path: pathlib.Path) -> GeneModels:
    return setup_gene_models(
        root_path / "t4c8_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")


def t4c8_grr(
    root_path: pathlib.Path,
) -> GenomicResourceRepo:
    t4c8_genome(root_path)
    t4c8_genes(root_path)

    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(root_path),
    })


def setup_t4c8_grr(
    root_path: pathlib.Path,
) -> GenomicResourceRepo:
    """Setup a genomic resource repository for t4c8 test instance."""
    repo_path = root_path
    t4c8_genome(repo_path)
    t4c8_genes(repo_path)

    setup_directories(
        repo_path / "gene_scores" / "t4c8_score",
        {
            GR_CONF_FILE_NAME:
            """
                type: gene_score
                filename: t4c8_gene_score.csv
                scores:
                - id: t4c8_score
                  desc: t4c8 gene score
                  histogram:
                    type: number
                    number_of_bins: 3
                    x_log_scale: false
                    y_log_scale: false
                """,
            "t4c8_gene_score.csv": textwrap.dedent("""
                gene,t4c8_score
                t4,10.123456789
                c8,20.0
            """),
        },
    )

    setup_directories(
        repo_path / "genomic_scores" / "score_one",
        {
            GR_CONF_FILE_NAME: textwrap.dedent("""
                type: position_score
                table:
                  filename: data.txt
                scores:
                - id: score_one
                  type: float
                  name: score
            """),
            "data.txt": textwrap.dedent("""
                chrom\tpos_begin\tscore
                chr1\t4\t0.01
                chr1\t54\t0.02
                chr1\t90\t0.03
                chr1\t100\t0.04
                chr1\t119\t0.05
                chr1\t122\t0.06
            """),
        },
    )

    cli_manage([
        "repo-repair", "-R", str(repo_path), "-j", "1"])

    return build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(repo_path),
    })
