"""Module containing the gene score annotator."""

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
from dae.gene_scores.gene_scores import build_gene_score_from_resource
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.aggregators import (
    build_aggregator,
    validate_aggregator,
)

logger = logging.getLogger(__name__)


def build_gene_score_annotator(pipeline: AnnotationPipeline,
                               info: AnnotatorInfo) -> Annotator:
    """Create a gene score annotator."""
    gene_score_resource_id = info.parameters["resource_id"]
    if not gene_score_resource_id:
        raise ValueError(f"The {info} needs a 'resource_id' parameter.")
    gene_score_resource = pipeline.repository.get_resource(
        gene_score_resource_id)
    if gene_score_resource is None:
        raise ValueError(f"The {gene_score_resource_id} is not available.")

    input_gene_list = info.parameters.get("input_gene_list")
    if input_gene_list is None:
        raise ValueError(f"The {input} must have an 'input_gene_list' "
                         "parameter")
    input_gene_list_info = pipeline.get_attribute_info(input_gene_list)
    if input_gene_list_info is None:
        raise ValueError(f"The {input_gene_list} is not provided by the "
                         "pipeline.")
    if input_gene_list_info.type != "object":
        raise ValueError(f"The {input_gene_list} provided by the pipeline "
                         "is not of type object.")
    return GeneScoreAnnotator(pipeline, info,
                              gene_score_resource, input_gene_list)


class GeneScoreAnnotator(Annotator):
    """Gene score annotator class."""

    DEFAULT_AGGREGATOR_TYPE = "dict"

    def __init__(self, pipeline: AnnotationPipeline | None,
                 info: AnnotatorInfo,
                 gene_score_resource: GenomicResource, input_gene_list: str):

        self.gene_score_resource = gene_score_resource
        self.score = build_gene_score_from_resource(
            self.gene_score_resource)

        info.resources += [gene_score_resource]
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                self.score.get_all_scores(),
            )

        self.aggregators: list[str] = []

        for attribute_config in info.attributes:
            score_def = self.score.score_definitions.get(
                attribute_config.source,
            )
            if score_def is None:
                message = (
                    f"The gene score {attribute_config.source} is "
                    f"unknown in {gene_score_resource.get_id()} "
                    "resource!"
                )
                raise ValueError(message)
            attribute_config.type = "float"
            attribute_config.description = score_def.desc

            aggregator_type = \
                attribute_config.parameters.get("gene_aggregator")
            if aggregator_type is None:
                aggregator_type = self.DEFAULT_AGGREGATOR_TYPE
            else:
                validate_aggregator(aggregator_type)

            self.aggregators.append(aggregator_type)

            aggregator_doc = f"**gene_aggregator**: {aggregator_type}"

            if aggregator_type == "dict":
                aggregator_doc = f"{aggregator_doc} [default]"
            attribute_config._documentation = (  # noqa: SLF001
                f"{attribute_config.documentation}\n\n"
                f"{aggregator_doc}"
            )

        self.input_gene_list = input_gene_list
        super().__init__(pipeline, info)

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return (self.input_gene_list,)

    def annotate(
        self,
        annotatable: Annotatable | None,  # noqa: ARG002
        context: dict[str, Any],
    ) -> dict[str, Any]:
        genes = context.get(self.input_gene_list)
        if genes is None:
            return self._empty_result()

        attributes = {}
        for attr, aggregator_type in zip(
            self.attributes, self.aggregators, strict=True,
        ):
            attributes[attr.name] = self.aggregate_gene_values(
                attr.source, genes, aggregator_type,
            )
        return attributes

    def aggregate_gene_values(
            self, score_id: str,
            gene_symbols: list[str],
            aggregator_type: str) -> Any:
        """Aggregate gene score values."""
        aggregator = build_aggregator(aggregator_type)

        for symbol in gene_symbols:
            aggregator.add(
                self.score.get_gene_value(score_id, symbol),
                key=symbol,
            )

        return aggregator.get_final()
