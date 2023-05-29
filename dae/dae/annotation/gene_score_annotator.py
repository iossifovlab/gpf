"""Module containing the gene score annotator."""

import logging
from typing import Any, Optional

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_factory import AnnotationConfigParser
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotatorInfo

from dae.gene.gene_scores import GeneScore
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.aggregators import build_aggregator
from dae.genomic_resources.aggregators import verify_aggregator


logger = logging.getLogger(__name__)


def build_gene_score_annotator(pipeline: AnnotationPipeline,
                               info: AnnotatorInfo) -> Annotator:

    gene_score_resource_id = info.parameters["resource_id"]
    if not gene_score_resource_id:
        raise ValueError(f"The {info} needs a 'resrouce_id' parameter.")
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
        raise ValueError(f"The {input_gene_list} is not privided by the "
                         "pipeline.")
    if input_gene_list_info.type != "object":
        raise ValueError(f"The {input_gene_list} privided by the pipeline "
                         "is not of type object.")
    return GeneScoreAnnotator(pipeline, info,
                              gene_score_resource, input_gene_list)


class GeneScoreAnnotator(Annotator):

    DEFAULT_AGGREGATOR_TYPE = "dict"

    def __init__(self, pipeline: Optional[AnnotationPipeline],
                 info: AnnotatorInfo,
                 gene_score_resource: GenomicResource, input_gene_list: str):

        self.gene_score_resource = gene_score_resource
        self.gene_scores_list = GeneScore.load_gene_scores_from_resource(
            self.gene_score_resource)
        self.gene_scores = {gs.score_id: gs for gs in self.gene_scores_list}

        info.resources += [gene_score_resource]
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                [gs_conf.score_id for gs_conf in self.gene_scores.values()])

        self.aggregators: list[str] = []

        for attribute_config in info.attributes:
            score_config = self.gene_scores.get(attribute_config.source)
            if score_config is None:
                message = f"The gene score {attribute_config.source} is " + \
                          f"unknown in {gene_score_resource.get_id()} " + \
                          "resource!"
                raise ValueError(message)
            attribute_config.type = "object"
            attribute_config.description = score_config.desc

            aggregator_type = \
                attribute_config.parameters.get("gene_aggregator")
            if aggregator_type is None:
                aggregator_type = self.DEFAULT_AGGREGATOR_TYPE
            else:
                verify_aggregator(aggregator_type)

            self.aggregators.append(aggregator_type)

        self.input_gene_list = input_gene_list
        super().__init__(pipeline, info)

    def annotate(self, _: Optional[Annotatable],
                 context: dict[str, Any]) \
            -> dict[str, Any]:

        genes = context.get(self.input_gene_list)
        if genes is None:
            return self._empty_result()

        attributes = {}
        for attr, aggregator_type in zip(self.attributes, self.aggregators):
            gene_score = self.gene_scores[attr.source]

            attributes[attr.name] = self.aggregate_gene_values(
                gene_score, genes, aggregator_type
            )
        return attributes

    def aggregate_gene_values(
            self, gene_score, gene_symbols: list[str], aggregator_type: str):
        aggregator = build_aggregator(aggregator_type)

        for symbol in gene_symbols:
            aggregator.add(gene_score.get_gene_value(symbol), key=symbol)

        return aggregator.get_final()
