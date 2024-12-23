import pytest

from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource_id,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)


@pytest.fixture(scope="session")
def gene_models_2013() -> GeneModels:
    gene_models = build_gene_models_from_resource_id(
        "hg19/gene_models/refGene_v201309")
    gene_models.load()
    return gene_models


@pytest.fixture(scope="session")
def genome_2013() -> ReferenceGenome:
    return build_reference_genome_from_resource_id(
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174").open()
