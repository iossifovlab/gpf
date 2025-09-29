import logging
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import (
    AnnotationConfigParser,
    AnnotatorInfo,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)
from dae.annotation.annotator_base import AnnotatorBase
from dae.gene_sets.gene_sets_db import (
    GeneSet,
    build_gene_set_collection_from_resource,
)
from dae.genomic_resources import GenomicResource

logger = logging.getLogger(__name__)


def build_gene_set_annotator(
    pipeline: AnnotationPipeline,
    info: AnnotatorInfo,
) -> Annotator:
    """Create a gene set annotator."""
    gene_set_resource_id = info.parameters["resource_id"]
    if not gene_set_resource_id:
        raise ValueError(f"The {info} needs a 'resource_id' parameter.")
    gene_set_resource = pipeline.repository.get_resource(
        gene_set_resource_id)
    if gene_set_resource is None:
        raise ValueError(f"The {gene_set_resource_id} is not available.")

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
        input_gene_list,
    )


class GeneSetAnnotator(AnnotatorBase):
    """Gene set annotator class."""

    def __init__(
        self,
        pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
        gene_set_resource: GenomicResource,
        input_gene_list: str,
    ):
        self.gene_set_resource = gene_set_resource
        self.gene_set_collection = build_gene_set_collection_from_resource(
            self.gene_set_resource)
        self.gene_sets: list[GeneSet] | None = None
        gene_sets_list = self.gene_set_collection \
            .get_gene_sets_list_statistics()
        if gene_sets_list is None:
            logger.info(
                "The gene set collection statistics for %s is empty.",
                self.gene_set_collection.collection_id,
            )
            self.gene_set_collection.load()
            gene_sets_list = [
                {"name": gs.name, "count": gs.count,
                 "desc": gs.desc or gs.name}
                for gs in sorted(
                    self.gene_set_collection.get_all_gene_sets(),
                    key=lambda gs: (-gs.count, gs.name),
                )
            ]

        info.resources += [gene_set_resource]
        attrs = {
            gs["name"]: ("bool", gs["desc"])
            for gs in gene_sets_list[:10]
        }
        attrs["in_sets"] = (
            "object", (
                "List of gene sets of the collection, "
                "which have at least 1 gene from the input gene list"
            ),
        )
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes([
                *attrs.keys(),
            ])

        self.input_gene_list = input_gene_list
        info.documentation = (
            "This annotator uses the"
            f"**{self.gene_set_collection.collection_id}**"
        )
        super().__init__(pipeline, info, attrs)

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return (self.input_gene_list,)

    def open(self) -> Annotator:
        self.gene_set_collection.load()
        self.gene_sets = self.gene_set_collection.get_all_gene_sets()
        super().open()
        return self

    def _do_annotate(
        self,
        annotatable: Annotatable | None,  # noqa: ARG002
        context: dict[str, Any],
    ) -> dict[str, Any]:
        genes = context.get(self.input_gene_list)
        if genes is None:
            return self._empty_result()
        genes_set = set(genes)

        in_sets: list[str] = []
        output: dict[str, Any] = {"in_sets": in_sets}
        if self.gene_sets is None:
            raise ValueError(
                f"The GeneSetAnnotator {self.gene_set_resource} "
                f"is not open.")
        for gs in self.gene_sets:
            output[gs.name] = False
            if genes_set.intersection(set(gs.syms)):
                output[gs.name] = True
                in_sets.append(gs.name)

        return output
