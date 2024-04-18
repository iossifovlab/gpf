# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance import GPFInstance
from dae.testing import setup_gene_models, setup_genome, setup_gpf_instance


def t4c8_genome(root_path: pathlib.Path) -> ReferenceGenome:
    genome = setup_genome(
        root_path / "t4c8_genome" / "chrAll.fa",
        """
           >chr1
           TTGTGTGAAGATGGAGGTAGGCCAGTTTCCCGGAGAGGTGAACAGACATTC"""
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
        """GGGGTCTGCCATCTTGGGAAAGAACTCCTGTTGGCCTACCTGTGCCTCAAANN""",
        #  |P |D<|A<|M<|==============------------=========
        #  1 1  1  1  11             1            1       2    2
        #  5 6  6  6  67             8            9       0    1
        #  8 0  3  6  90             3            6       4    0
    )
    return genome


# This content follows the 'refflat' gene model format
# Coordinates in refflat gene models are 0-base.
# Regions are half open. Closed at the start and open at the end - [start, end)
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts  exonEnds 
t4        tx1  chr1  +      5       84    10       71     3         5,25,45     16,37,84
c8        tx1  chr1  -      100     204   112      169    3         100,145,195 133,183,204
"""  # noqa


def t4c8_genes(root_path: pathlib.Path) -> GeneModels:
    genes = setup_gene_models(
        root_path / "t4c8_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")
    return genes


def t4c8_gpf(
        root_path: pathlib.Path,
        storage: Optional[GenotypeStorage] = None) -> GPFInstance:
    t4c8_genome(root_path)
    t4c8_genes(root_path)

    local_repo = build_genomic_resource_repository({
        "id": "t4c8_local",
        "type": "directory",
        "directory": str(root_path),
    })

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=local_repo)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
