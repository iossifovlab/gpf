from typing import Optional
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels


class AnnotationPipelineContext:
    def get_reference_genome(self) -> Optional[ReferenceGenome]:
        return None

    def get_gene_models(self) -> Optional[GeneModels]:
        return None
