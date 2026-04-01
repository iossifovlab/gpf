# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

from gain.genomic_resources.gene_models import GeneModels
from gain.genomic_resources.reference_genome import ReferenceGenome
from gain.genomic_resources.testing import (
    setup_gene_models,
    setup_genome,
)

# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       17    3        17     2         3,13       6,17
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      3       20    3        15     1         3          17
"""  # noqa


def foobar_genes(root_path: pathlib.Path) -> GeneModels:
    return setup_gene_models(
        root_path / "foobar_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")


def foobar_genome(root_path: pathlib.Path) -> ReferenceGenome:
    return setup_genome(
        root_path / "foobar_genome" / "chrAll.fa",
        """
            >foo
            NNACCCAAAC
            GGGCCTTCCN
            NNNA
            >bar
            NNGGGCCTTC
            CACGACCCAA
            NN
        """,
    )
