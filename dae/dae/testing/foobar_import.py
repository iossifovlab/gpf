# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing import setup_gene_models, setup_genome, setup_gpf_instance

# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
g1        tx1  foo   +      3       17    3        17     2         3,13       6,17
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      3       20    3        15     1         3          17
"""  # noqa


def foobar_genes(root_path: pathlib.Path) -> GeneModels:
    genes = setup_gene_models(
        root_path / "foobar_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")
    return genes


def foobar_genome(root_path: pathlib.Path) -> ReferenceGenome:
    genome = setup_genome(
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
    return genome


def foobar_gpf(
        root_path: pathlib.Path,
        storage: Optional[GenotypeStorage] = None) -> GPFInstance:
    setup_genome(
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
    setup_gene_models(
        root_path / "foobar_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")
    local_repo = build_genomic_resource_repository({
        "id": "foobar_local",
        "type": "directory",
        "directory": str(root_path),
    })

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="foobar_genome",
        gene_models_id="foobar_genes",
        grr=local_repo)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
