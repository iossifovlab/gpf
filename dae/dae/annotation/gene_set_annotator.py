
import logging
from typing import Any, Optional

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotatorInfo

from dae.gene.gene_sets_db import build_gene_set_collection_from_resource
from dae.genomic_resources import GenomicResource


logger = logging.getLogger(__name__)


def build_gene_set_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo
) -> Annotator:
    """Create a gene set annotator."""
    gene_set_resource_id = info.parameters["resource_id"]
    if not gene_set_resource_id:
        raise ValueError(f"The {info} needs a 'resource_id' parameter.")
    gene_set_resource = pipeline.repository.get_resource(
        gene_set_resource_id)
    if gene_set_resource is None:
        raise ValueError(f"The {gene_set_resource_id} is not available.")

    gene_set_id = info.parameters["gene_set_id"]
    if not gene_set_id:
        raise ValueError(f"The {info} needs a 'gene_set_id' parameter.")

    input_gene_list = info.parameters.get("input_gene_list")
    if input_gene_list is None:
        raise ValueError(f"The {input} must have an 'input_gene_list' "
                         "parameter")
    input_gene_list_info = pipeline.get_attribute_info(input_gene_list)
    if input_gene_list_info is None:
        raise ValueError(f"The {input_gene_list} is not privided by the "
                         "pipeline.")
    if input_gene_list_info.type != "object":
        raise ValueError(f"The {input_gene_list} privided by the pipeline "
                         "is not of type object.")
    return GeneSetAnnotator(
        pipeline,
        info,
        gene_set_resource,
        gene_set_id,
        input_gene_list
    )


class GeneSetAnnotator(Annotator):
    """Gene set annotator class."""

    def __init__(
        self,
        pipeline: Optional[AnnotationPipeline],
        info: AnnotatorInfo,
        gene_set_resource: GenomicResource,
        gene_set_id: str,
        input_gene_list: str
    ):
        self.gene_set_resource = gene_set_resource
        self.gene_set_collection = build_gene_set_collection_from_resource(
            self.gene_set_resource)

        self.gene_set = self.gene_set_collection.get_gene_set(gene_set_id)
        if self.gene_set is None:
            raise ValueError(f"The {gene_set_id} is not in the collection")

        info.resources += [gene_set_resource]

        self.input_gene_list = input_gene_list
        super().__init__(pipeline, info)

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return (self.input_gene_list,)

    def annotate(self, _: Optional[Annotatable],
                 context: dict[str, Any]) \
            -> dict[str, Any]:

        genes = context.get(self.input_gene_list)
        if genes is None:
            return self._empty_result()

        is_in = False
        if len([gene for gene in genes if gene in self.gene_set.syms]) != 0:
            is_in = True

        attributes = {self.gene_set.name: is_in}

        return attributes
