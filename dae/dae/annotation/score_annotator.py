"""Provides score annotators."""

import logging
import copy

from typing import Dict, List, cast, Any

from dae.genomic_resources.genomic_scores import \
    build_allele_score_from_resource, build_position_score_from_resource, \
    build_np_score_from_resource
from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA

from .annotatable import Annotatable, VCFAllele
from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
from .annotation_pipeline import AnnotationPipeline


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
        "attributes": {
            "type": "list",
            "nullable": True,
            "default": None,
            "schema": None
        }
    }

    def __init__(self, config: Dict, score):

        super().__init__(config)

        self.score = score
        self._annotation_schema = None

        self.non_default_position_aggregators: dict = {}
        self.non_default_nucleotide_aggregators: dict = {}
        self._collect_non_default_aggregators()

    def open(self):
        self.score.open()

    def is_open(self):
        return self.score.is_open()

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = []
        for score in self.score.score_columns.values():
            result.append({
                "name": score.score_id,
                "type": score.type,
                "desc": score.desc
            })
        return result

    def get_annotation_config(self) -> List[Dict[str, Any]]:
        if self.config.get("attributes"):
            return cast(List[Dict[str, Any]], self.config["attributes"])

        if self.score.get_default_annotation():
            attributes = self.score.get_default_annotation()["attributes"]
            logger.debug(
                "using default score annotation for %s: %s",
                self.score.score_id(), attributes)
            return cast(List[Dict[str, Any]], attributes)
        logger.warning(
            "can't find annotation config for resource: %s",
            self.score.score_id())
        return []

    def _collect_non_default_aggregators(self):
        non_default_position_aggregators = {}
        non_default_nucleotide_aggregators = {}
        for attr in self.get_annotation_config():
            if attr.get("position_aggregator") is not None:
                non_default_position_aggregators[attr["source"]] = \
                    attr.get("position_aggregator")
            if attr.get("nucleotide_aggregator") is not None:
                non_default_nucleotide_aggregators[attr["source"]] = \
                    attr.get("nucleotide_aggregator")

        if non_default_position_aggregators:
            self.non_default_position_aggregators = \
                non_default_position_aggregators
        if non_default_nucleotide_aggregators:
            self.non_default_nucleotide_aggregators = \
                non_default_nucleotide_aggregators

    def get_scores(self):
        return [attr["source"] for attr in self.get_annotation_config()]

    def _scores_not_found(self, attributes):
        values = {
            score_id: None for score_id in self.get_scores()
        }
        attributes.update(values)

    def close(self):
        self.score.close()


def build_position_score_annotator(pipeline: AnnotationPipeline, config: Dict):
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

    def __init__(self, config: dict, resource):
        super().__init__(config, resource)

    def annotator_type(self) -> str:
        return "position_score"

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        aschema = cast(dict, attributes_schema["schema"])
        aschema["position_aggregator"] = AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["position_score"]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
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
        return cast(Dict, validator.document)

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
            self.get_scores(),
            self.non_default_position_aggregators
        )
        scores = {
            sc_name: sc_agg.get_final()
            for sc_name, sc_agg in scores_agg.items()
        }
        return scores

    def _do_annotate(
            self, annotatable: Annotatable, context):
        attributes: dict = {}

        if annotatable is None:
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in self.score.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        length = len(annotatable)
        if annotatable.type == Annotatable.Type.SUBSTITUTION:
            scores = self._fetch_substitution_scores(annotatable)
        else:
            if length > 500_000:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(
                    annotatable.chrom,
                    annotatable.pos, annotatable.pos_end)
        if not scores:
            self._scores_not_found(attributes)
            return attributes

        for score in self.get_scores():
            value = scores[score]
            attributes[score] = value
        return attributes


def build_np_score_annotator(pipeline: AnnotationPipeline, config: Dict):
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
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        aschema = cast(dict, attributes_schema["schema"])
        aschema["position_aggregator"] = AGGREGATOR_SCHEMA
        aschema["nucleotide_aggregator"] = AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["np_score"]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
        logger.debug("validating NP score config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for NP score annotator: %s",
                validator.errors)
            raise ValueError(f"wrong NP score config {validator.errors}")

        return cast(Dict, validator.document)

    def annotator_type(self) -> str:
        return "np_score"

    def _fetch_substitution_scores(self, allele):
        return self.score.fetch_scores(
            allele.chromosome, allele.position,
            allele.reference, allele.alternative,
            self.get_scores()
        )

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end):
        scores_agg = self.score.fetch_scores_agg(
            chrom,
            pos_begin,
            pos_end,
            self.get_scores(),
            self.non_default_position_aggregators,
            self.non_default_nucleotide_aggregators
        )
        if scores_agg is None:
            return None

        scores = {
            sc_name: sc_agg.get_final()
            for sc_name, sc_agg in scores_agg.items()
        }
        return scores


def build_allele_score_annotator(pipeline: AnnotationPipeline, config: Dict):
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

    def __init__(self, config: dict, score):
        super().__init__(config, score)

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = ["allele_score", "vcf_info"]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
        logger.debug("validating allele score config: %s", config)
        if not validator.validate(config):
            logger.error(
                "wrong config format for allele score annotator: %s",
                validator.errors)
            raise ValueError(f"wrong allele score config {validator.errors}")

        result: Dict = validator.document
        if result.get("attributes"):
            if any("nucleotide_aggregator" in attr
                    for attr in result["attributes"]):
                logger.error(
                    "nucleotide aggregator found in position score config: %s",
                    result)
                raise ValueError(
                    "nucleotide_aggregator is not allowed in position score")
            if any("position_aggregator" in attr
                    for attr in result["attributes"]):
                logger.error(
                    "position aggregator found in position score config: %s",
                    result)
                raise ValueError(
                    "position_aggregator is not allowed in position score")

        return result

    def annotator_type(self) -> str:
        return "allele_score"

    def _do_annotate(
            self, annotatable: Annotatable, context: Dict):
        attributes: dict = {}

        if not isinstance(annotatable, VCFAllele):
            logger.info(
                "skip trying to add frequency for CNV variant %s", annotatable)
            self._scores_not_found(attributes)
            return attributes

        if annotatable is None:
            logger.info("annotatable is None")
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in self.score.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        scores_dict = self.score.fetch_scores(
            annotatable.chromosome,
            annotatable.position,
            annotatable.reference,
            annotatable.alternative,
            self.get_scores()
        )
        logger.debug(
            "allele score found for annotatable %s: %s",
            annotatable, scores_dict)

        if scores_dict is None:
            self._scores_not_found(attributes)
            return attributes

        for score_id, score_value in scores_dict.items():
            try:
                if score_value in ("", " "):
                    attributes[score_id] = None
                else:
                    attributes[score_id] = score_value
            except ValueError as ex:
                logger.error(
                    "problem with: %s: %s - %s",
                    score_id, annotatable, score_value)
                logger.error(ex)
                raise ex

        return attributes
