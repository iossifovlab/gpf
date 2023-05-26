"""Provides score annotators."""

import logging
import copy

from typing import cast, Any
from dae.annotation.annotation_pipeline import Annotator, AttributeInfo

from dae.genomic_resources.genomic_scores import \
    GenomicScore, build_allele_score_from_resource, \
    build_position_score_from_resource, build_np_score_from_resource, \
    PositionScoreQuery, NPScoreQuery, AlleleScoreQuery, ScoreQuery

from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA
from dae.genomic_resources.repository import GenomicResource

from .annotatable import Annotatable, VCFAllele
from .annotator_base import ATTRIBUTES_SCHEMA, AnnotatorConfigValidator
from .annotation_pipeline import AnnotationPipeline
from cerberus.validator import Validator

logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    """Base class for score annotators."""

    VALIDATION_SCHEMA = {
        "annotator_type": {
            "type": "string",
            "required": True,
            "allowed": ["position_score", "np_score", "allele_score"],
        },
        "input_annotatable": {
            "type": "string",
            "nullable": True,
            "default": None,
        },
        "resource_id": {
            "type": "string",
            "required": True,
        },
        "region_length_cutoff": {
            "type": "integer",
            "nullable": True,
            "default": 500_000,
        },
        "attributes": {
            "type": "list",
            "nullable": True,
            "default": None,
            "schema": None
        }
    }

    def __init__(self, config: dict, score: GenomicScore):

        super().__init__(config)

        self.score = score
        self.score_queries: list[ScoreQuery] = self._collect_score_queries()
        self._annotation_schema = None
        self._region_length_cutoff = self.config.get(
            "region_length_cutoff", 500_000)

    def open(self):
        self.score.open()

    def is_open(self):
        return self.score.is_open()

    def get_all_annotation_attributes(self) -> list[dict]:
        result = []
        for score_id, score in self.score.score_definitions.items():
            result.append({
                "name": score_id,
                "type": score.type,
                "desc": score.desc
            })
        return result

    def get_annotation_config(self) -> list[dict[str, Any]]:
        if self.config.get("attributes"):
            return cast(list[dict[str, Any]], self.config["attributes"])

        if self.score.get_default_annotation():
            attributes = self.score.get_default_annotation()["attributes"]
            logger.debug(
                "using default score annotation for %s: %s",
                self.score.score_id, attributes)
            return cast(list[dict[str, Any]], attributes)
        logger.warning(
            "can't find annotation config for resource: %s",
            self.score.score_id)
        return []

    @property
    def resources(self) -> list[GenomicResource]:
        return [self.score.resource]

    @property
    def attributes(self) -> list[AttributeInfo]:
        """Genomic resources used by the annotator."""
        ret = []
        for attribute_config in self.get_annotation_config():
            name = attribute_config["destination"]
            score = attribute_config.get("source", name)
            score_config = self.score.get_score_config(score)
            if score_config is None:
                message = f"The score {score} is unknown in " + \
                          f"{self.score.resource.get_id()} resource!"
                logger.error(message)
                raise Exception(message)
            hist_url = f"{self.score.resource.get_url()}" + \
                       f"/statistics/histogram_{score}.png"

            desc = attribute_config.get("desc", "") + "\n\n" + \
                score_config.desc + "\n\n" + \
                f"![HISTOGRAM]({hist_url})"
            internal = bool(attribute_config.get("internal", True))
            ret.append(AttributeInfo(name, score, score_config.type,
                                     desc, internal))
        return ret
  
    def _collect_score_queries(self) -> list[ScoreQuery]:
        return []

    def get_scores(self):
        return [attr["source"] for attr in self.get_annotation_config()]

    def _scores_not_found(self, attributes):
        values = {
            attr["destination"]: None for attr in self.get_annotation_config()
        }
        attributes.update(values)

    def close(self):
        self.score.close()


def build_position_score_annotator(pipeline: AnnotationPipeline, config: dict):
    """Construct position score annotator."""
    config = PositionScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "position_score":
        logger.error(
            "wrong usage of build_position_score_annotator with an "
            "annotator config: %s", config)
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config["resource_id"]
    resource = pipeline.repository.get_resource(resource_id)

    score = build_position_score_from_resource(resource)
    return PositionScoreAnnotator(config, score)


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    """Defines position score annotator."""

    def annotator_type(self) -> str:
        return "position_score"

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        aschema = cast(dict, attributes_schema["schema"])
        aschema["position_aggregator"] = AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["position_score"]
        schema["attributes"]["schema"] = attributes_schema

        validator = AnnotatorConfigValidator(schema)
        logger.debug("validating position score config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for position score annotator: %s",
                validator.errors)
            raise ValueError(f"wrong position score config {validator.errors}")

        result = validator.document

        if result.get("attributes") and any(
                "nucleotide_aggregator" in attr
                for attr in result.get("attributes")):
            logger.error(
                "nucleotide aggregator found in position score config: %s",
                result)
            raise ValueError(
                "nucleotide_aggregator is not allowed in position score")
        if result.get("attributes") and any(
                "allele_aggregator" in attr
                for attr in result.get("attributes")):
            logger.error(
                "allele aggregator found in position score config: %s",
                result)
            raise ValueError(
                "allele_aggregator is not allowed in position score")
        return cast(dict, result)

    def _collect_score_queries(self) -> list[ScoreQuery]:
        result: list[ScoreQuery] = []
        for attr in self.get_annotation_config():
            result.append(PositionScoreQuery(
                attr["source"], attr.get("position_aggregator")))
        return result

    def _fetch_substitution_scores(self, allele):
        scores = self.score.fetch_scores(
            allele.chromosome, allele.position,
            self.get_scores()
        )
        return scores

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end):
        scores_agg = self.score.fetch_scores_agg(
            chrom,
            pos_begin,
            pos_end,
            self.score_queries
        )
        return [sagg.get_final() for sagg in scores_agg]

    def annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:
        attributes: dict = {}

        if annotatable is None:
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in \
                self.score.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        length = len(annotatable)
        if annotatable.type == Annotatable.Type.SUBSTITUTION:
            scores = self._fetch_substitution_scores(annotatable)
        else:
            if length > self._region_length_cutoff:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(
                    annotatable.chrom,
                    annotatable.pos, annotatable.pos_end)
        if not scores:
            self._scores_not_found(attributes)
            return attributes

        return dict(zip(
            [attr["destination"] for attr in self.get_annotation_config()],
            scores))


def build_np_score_annotator(pipeline: AnnotationPipeline, config: dict):
    """Construct an NP Score annotator."""
    config = NPScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "np_score":
        logger.error(
            "wrong usage of build_np_score_annotator with an "
            "annotator config: %s", config)
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config["resource_id"]
    resource = pipeline.repository.get_resource(resource_id)

    score = build_np_score_from_resource(resource)
    return NPScoreAnnotator(config, score)


class NPScoreAnnotator(PositionScoreAnnotator):
    """Defines nucleotide-position score annotator."""

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        aschema = cast(dict, attributes_schema["schema"])
        aschema["position_aggregator"] = AGGREGATOR_SCHEMA
        aschema["nucleotide_aggregator"] = AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["np_score"]
        schema["attributes"]["schema"] = attributes_schema

        validator = AnnotatorConfigValidator(schema)
        logger.debug("validating NP score config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for NP score annotator: %s",
                validator.errors)
            raise ValueError(f"wrong NP score config {validator.errors}")

        result = validator.document
        if result.get("attributes") and any(
                "allele_aggregator" in attr
                for attr in result.get("attributes")):
            logger.error(
                "allele aggregator found in NP score config: %s",
                result)
            raise ValueError(
                "allele_aggregator is not allowed in NP score")

        return cast(dict, validator.document)

    def annotator_type(self) -> str:
        return "np_score"

    def _fetch_substitution_scores(self, allele):
        return self.score.fetch_scores(
            allele.chromosome, allele.position,
            allele.reference, allele.alternative,
            self.get_scores()
        )

    def _collect_score_queries(self) -> list[ScoreQuery]:
        result: list[ScoreQuery] = []
        for attr in self.get_annotation_config():
            result.append(NPScoreQuery(
                attr["source"], attr.get("position_aggregator"),
                attr.get("nucleotide_aggregator")))
        return result


def build_allele_score_annotator(pipeline: AnnotationPipeline, config: dict):
    """Construct an Allele Score annotator."""
    config = AlleleScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "allele_score":
        logger.error(
            "wrong usage of build_allele_score_annotator with an "
            "annotator config: %s", config)
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config["resource_id"]
    resource = pipeline.repository.get_resource(resource_id)

    score = build_allele_score_from_resource(resource)
    return AlleleScoreAnnotator(config, score)


class AlleleScoreAnnotator(VariantScoreAnnotatorBase):
    """Defines Allele Score annotator."""

    @classmethod
    def validate_config(cls, config: dict) -> dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["allele_score", ]
        schema["attributes"]["schema"] = attributes_schema

        validator = AnnotatorConfigValidator(schema)
        logger.debug("validating allele score config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for allele score annotator: %s",
                validator.errors)
            raise ValueError(f"wrong allele score config {validator.errors}")

        result: dict = validator.document
        if result.get("attributes"):
            if any("nucleotide_aggregator" in attr
                    for attr in result["attributes"]):
                logger.error(
                    "nucleotide aggregator found in allele score config: %s",
                    result)
                raise ValueError(
                    "nucleotide_aggregator is not allowed in position score")

        return result

    def annotator_type(self) -> str:
        return "allele_score"

    def _collect_score_queries(self) -> list[ScoreQuery]:
        result: list[ScoreQuery] = []
        for attr in self.get_annotation_config():
            result.append(AlleleScoreQuery(
                attr["source"], attr.get("position_aggregator"),
                attr.get("allele_aggregator")))
        return result

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end):
        scores_agg = self.score.fetch_scores_agg(
            chrom,
            pos_begin,
            pos_end,
            self.score_queries
        )
        return [sagg.get_final() for sagg in scores_agg]

    def annotate(
            self, annotatable: Annotatable, context: dict):
        attributes: dict = {}

        if annotatable is None:
            logger.info("annotatable_override is None")
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in \
                self.score.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        if isinstance(annotatable, VCFAllele):
            scores = self.score.fetch_scores(
                annotatable.chromosome,
                annotatable.position,
                annotatable.reference,
                annotatable.alternative,
                self.get_scores()
            )
        else:
            length = len(annotatable)
            if length > self._region_length_cutoff:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(
                    annotatable.chrom,
                    annotatable.pos,
                    annotatable.pos_end)

        logger.debug(
            "allele score found for annotatable_override %s: %s",
            annotatable, scores)

        if scores is None:
            self._scores_not_found(attributes)
            return attributes

        for attr, value in zip(self.get_annotation_config(), scores):
            try:
                if value in ("", " "):
                    attributes[attr["destination"]] = None
                else:
                    attributes[attr["destination"]] = value
            except ValueError as ex:
                logger.error(
                    "problem with: %s: %s - %s",
                    attr, annotatable, value, exc_info=True)
                raise ex

        return attributes
