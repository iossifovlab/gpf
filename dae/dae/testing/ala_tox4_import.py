# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

from dae.testing import \
    setup_genome, setup_gene_models, setup_gpf_instance
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage

from dae.gpf_instance import GPFInstance


def ala_tox4_genome(root_path: pathlib.Path) -> ReferenceGenome:
    genome = setup_genome(
        root_path / "ala_tox4_genome" / "chrAll.fa",
        """
          >chr14
          TTGTGTGAAGATGGAGGTAGGCCAGTTTCCCGGAGAGGTGAACAGACATTC"""
        # 0         1    1         2          3        4    5
        # 1     6   1    6         6          7        6    1
        #       ====|M1|E2---------|F3|P4|G5|E6--------|T7|F8
        """CATACAACCATGGTGAAATAGTCCTTCCTGTTACACAAG"""
        #  |H9|T0|T1|M2|V3|K|S =============
        #  5                   7       8   8     9
        #  2                   2       0   4     0
        #

    )
    return genome


# This content follows the 'refflat' gene model format
# Coordinates in refflat gene models are 0-base.
# Regions are half open. Closed at the start and open at the end - [start, end)
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
g4        tx1  chr14 +      5       84    10       71     3         5,25,45    16,37,84
"""  # noqa


def ala_tox4_genes(root_path: pathlib.Path) -> GeneModels:
    genes = setup_gene_models(
        root_path / "ala_tox4_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")
    return genes


def ala_tox4_gpf(
        root_path: pathlib.Path,
        storage: Optional[GenotypeStorage] = None) -> GPFInstance:
    ala_tox4_genome(root_path)
    ala_tox4_genes(root_path)

    local_repo = build_genomic_resource_repository({
        "id": "ala_tox4_local",
        "type": "directory",
        "directory": str(root_path)
    })

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="ala_tox4_genome",
        gene_models_id="ala_tox4_genes",
        grr=local_repo)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
