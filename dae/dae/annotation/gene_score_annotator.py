"""Module containing the gene score annotator."""

import logging
import copy

from typing import cast, Any
from dae.gene.gene_scores import GeneScore
from dae.genomic_resources import GenomicResource
from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA
from dae.genomic_resources.aggregators import build_aggregator

from .annotator_base import AnnotatorBase, ATTRIBUTES_SCHEMA, AnnotatorConfigValidator
from .annotatable import Annotatable

logger = logging.getLogger(__name__)


def build_gene_score_annotator(pipeline, config):
    """Construct a gene score annotator."""
    config = GeneScoreAnnotator.validate_config(config)

    assert config["annotator_type"] == "gene_score_annotator"

    gene_score_resource = pipeline.repository.get_resource(
        config["resource_id"]
    )
    if gene_score_resource is None:
        raise ValueError(
            f"can't create gene score annotator; "
            f"can't find score {config['resource_id']}")

    return GeneScoreAnnotator(config, gene_score_resource)


class GeneScoreAnnotator(AnnotatorBase):
    """Annotator that annotates variants by using gene score resources."""

    DEFAULT_AGGREGATOR_TYPE = "dict"

    def __init__(self, config: dict, resource: GenomicResource):
        super().__init__(config)

        self.resource = resource
        resource_scores = GeneScore.load_gene_scores_from_resource(
            resource
        )
        self.gene_scores = {gs.score_id: gs for gs in resource_scores}

        self._annotation_schema = None

    def annotator_type(self) -> str:
        return "gene_score_annotator"

    def get_all_annotation_attributes(self) -> list[dict]:
        result = []
        for gene_score in self.gene_scores.values():
            result.append({
                "name": gene_score.score_id,
                "type": "object",
                "desc": gene_score.desc
            })
        return result

    def get_annotation_config(self) -> list[dict]:
        attributes: list[dict] = self.config.get("attributes", [])

        return attributes

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        attr_schema = cast(dict[str, Any], copy.deepcopy(ATTRIBUTES_SCHEMA))
        aggr_schema = copy.deepcopy(AGGREGATOR_SCHEMA)
        attr_schema["schema"]["gene_aggregator"] = aggr_schema

        schema = {
            "annotator_type": {
                "type": "string",
                "required": True,
                "allowed": ["gene_score_annotator"]
            },
            "input_annotatable": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
            "resource_id": {"type": "string"},
            "input_gene_list": {"type": "string"},
            "attributes": {
                "type": "list",
                "schema": attr_schema
            }
        }

        validator = AnnotatorConfigValidator(schema)
        validator.allow_unknown = True

        logger.debug("validating gene score annotator config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for gene score annotator: %s",
                validator.errors
            )
            raise ValueError(
                f"wrong gene score annotator config {validator.errors}")
        return cast(dict, validator.document)

    @property
    def resources(self) -> list[GenomicResource]:
        return [self.resource]

    def aggregate_gene_values(
            self, gene_score, gene_symbols, aggregator_type=None):
        """Aggregate values for given symbols with given aggregator type."""
        if aggregator_type is None:
            aggregator_type = self.DEFAULT_AGGREGATOR_TYPE
        aggregator = build_aggregator(aggregator_type)

        for symbol in gene_symbols:
            aggregator.add(gene_score.get_gene_value(symbol), key=symbol)

        return aggregator.get_final()

    def _not_found(self):
        attributes: dict = {}
        for attr in self.config["attributes"]:
            src = attr["source"]
            attributes[src] = None
        return attributes

    def _do_annotate(self, annotatable: Annotatable, _context: dict):
        attributes: dict = {}

        input_gene_list = self.config["input_gene_list"]
        genes = _context.get(input_gene_list)
        if genes is None:
            return self._not_found()

        assert genes is not None
        for attr in self.config["attributes"]:
            src = attr["source"]
            aggregator_type = attr.get("gene_aggregator")
            gene_score = self.gene_scores[src]

            attributes[src] = self.aggregate_gene_values(
                gene_score, genes, aggregator_type
            )

        return attributes

    def close(self):
        pass

    def open(self):  # FIXME:
        return self

    def is_open(self):  # FIXME:
        return True
