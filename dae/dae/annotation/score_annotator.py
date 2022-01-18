import logging
import copy

from typing import Dict, List
from box import Box

from .annotatable import Annotatable, VCFAllele
from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
from .annotation_pipeline import AnnotationPipeline

from dae.genomic_resources.score_resources import GenomicScoresResource
from dae.genomic_resources.aggregators import AGGREGATOR_SCHEMA

logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):

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

    def __init__(self, config: Dict, resource):

        super().__init__(config)

        self.resource = resource
        self.liftover_id = self.config.get("liftover_id")

        assert isinstance(resource, GenomicScoresResource), \
            resource.resource_id
        self._annotation_schema = None

        self.non_default_position_aggregators = {}
        self.non_default_nucleotide_aggregators = {}
        self._collect_non_default_aggregators()

    def get_all_annotation_attributes(self) -> List[Dict]:
        result = []
        for score in self.resource.scores.values():
            result.append({
                "name": score.id,
                "type": score.type,
                "desc": score.desc
            })
        return result

    def get_annotation_config(self) -> List[Dict]:
        attributes = self.config.get("attributes")
        if attributes:
            return attributes
        if self.resource.get_default_annotation():
            attributes = self.resource.get_default_annotation().attributes
            logger.info(
                f"using default annotation for {self.resource.resource_id}: "
                f"{attributes}")
            return attributes
        logger.warning(
            f"can't find annotation config for resource: "
            f"{self.resource.resource_id}")
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
        return [attr.source for attr in self.get_annotation_config()]

    def _scores_not_found(self, attributes):
        values = {
            score_id: None for score_id in self.get_scores()
        }
        attributes.update(values)


def build_position_score_annotator(pipeline: AnnotationPipeline, config: Dict):
    config = PositionScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "position_score":
        logger.error(
            f"wrong usage of build_position_score_annotator with an "
            f"annotator config: {config}")
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config.get("resource_id")
    resource = pipeline.repository.get_resource(resource_id)
    if resource is None:
        logger.error(
            f"can't find resource {resource_id} in "
            f"genomic resource repository {pipeline.repository.repo_id}")
        raise ValueError(f"can't find resource {resource_id}")

    return PositionScoreAnnotator(config, resource)


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config: Box, resource):
        super().__init__(config, resource)
        # FIXME This should be closed somewhere
        self.resource.open()

    @staticmethod
    def annotator_type():
        return "position_score"

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        attributes_schema["schema"]["position_aggregator"] = \
            AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = [cls.annotator_type()]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
        logger.debug(f"validating position score config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for position score annotator: "
                f"{validator.errors}")
            raise ValueError(f"wrong position score config {validator.errors}")

        result = validator.document
        if result.attributes and any([
                "nucleotide_aggregator" in attr
                for attr in result.attributes]):
            logger.error(
                f"nucleotide aggregator found in position score config: "
                f"{result}")
            raise ValueError(
                "nucleotide_aggregator is not allowed in position score")
        return validator.document

    def _fetch_substitution_scores(self, variant):
        scores = self.resource.fetch_scores(
            variant.chromosome, variant.position,
            self.get_scores()
        )
        return scores

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end):
        scores_agg = self.resource.fetch_scores_agg(
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
        attributes = {}

        if annotatable is None:
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in self.resource.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        length = len(annotatable)
        if annotatable.type == Annotatable.Type.substitution:
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
    config = NPScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "np_score":
        logger.error(
            f"wrong usage of build_np_score_annotator with an "
            f"annotator config: {config}")
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config.get("resource_id")
    resource = pipeline.repository.get_resource(resource_id)
    if resource is None:
        logger.error(
            f"can't find resource {resource_id} in "
            f"genomic resource repository {pipeline.repository.repo_id}")
        raise ValueError(f"can't find resource {resource_id}")

    return NPScoreAnnotator(config, resource)


class NPScoreAnnotator(PositionScoreAnnotator):
    def __init__(self, config: Box, resource):
        super().__init__(config, resource)
        self.resource.open()

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)
        attributes_schema["schema"]["position_aggregator"] = \
            AGGREGATOR_SCHEMA
        attributes_schema["schema"]["nucleotide_aggregator"] = \
            AGGREGATOR_SCHEMA

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = [cls.annotator_type()]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
        logger.debug(f"validating NP score config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for NP score annotator: "
                f"{validator.errors}")
            raise ValueError(f"wrong NP score config {validator.errors}")

        return validator.document

    @staticmethod
    def annotator_type():
        return "np_score"

    def _fetch_substitution_scores(self, allele):
        return self.resource.fetch_scores(
            allele.chromosome, allele.position,
            allele.reference, allele.alternative,
            self.get_scores()
        )

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end):
        scores_agg = self.resource.fetch_scores_agg(
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
    config = AlleleScoreAnnotator.validate_config(config)

    if config.get("annotator_type") != "allele_score":
        logger.error(
            f"wrong usage of build_allele_score_annotator with an "
            f"annotator config: {config}")
        raise ValueError(f"wrong annotator type: {config}")

    resource_id = config.get("resource_id")
    resource = pipeline.repository.get_resource(resource_id)
    if resource is None:
        logger.error(
            f"can't find resource {resource_id} in "
            f"genomic resource repository {pipeline.repository.repo_id}")
        raise ValueError(f"can't find resource {resource_id}")

    return AlleleScoreAnnotator(config, resource)


class AlleleScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config: Box, resource):
        super().__init__(config, resource)
        resource.open()

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        attributes_schema = copy.deepcopy(ATTRIBUTES_SCHEMA)

        schema = copy.deepcopy(cls.VALIDATION_SCHEMA)
        schema["annotator_type"]["allowed"] = [cls.annotator_type()]
        schema["attributes"]["schema"] = attributes_schema

        validator = cls.ConfigValidator(schema)
        logger.debug(f"validating allele score config: {config}")
        if not validator.validate(config):
            logger.error(
                f"wrong config format for allele score annotator: "
                f"{validator.errors}")
            raise ValueError(f"wrong allele score config {validator.errors}")

        result = validator.document
        if result.attributes:
            if any(["nucleotide_aggregator" in attr
                    for attr in result.attributes]):
                logger.error(
                    f"nucleotide aggregator found in position score config: "
                    f"{result}")
                raise ValueError(
                    "nucleotide_aggregator is not allowed in position score")
            if any(["position_aggregator" in attr
                    for attr in result.attributes]):
                logger.error(
                    f"position aggregator found in position score config: "
                    f"{result}")
                raise ValueError(
                    "position_aggregator is not allowed in position score")

        return result

    @staticmethod
    def annotator_type():
        return "allele_score"

    def _do_annotate(
            self, annotatable: Annotatable, context: Dict):

        attributes = {}

        if not isinstance(annotatable, VCFAllele):
            logger.info(
                f"skip trying to add frequency for CNV variant {annotatable}")
            self._scores_not_found(attributes)
            return attributes

        if annotatable is None:
            self._scores_not_found(attributes)
            return attributes

        if annotatable.chromosome not in self.resource.get_all_chromosomes():
            self._scores_not_found(attributes)
            return attributes

        scores_dict = self.resource.fetch_scores(
            annotatable.chromosome,
            annotatable.position,
            annotatable.reference,
            annotatable.alternative
        )
        logger.debug(
            f"allele score found for annotatable {annotatable}: "
            f"{scores_dict}")

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
                    f"problem with: {score_id}: {annotatable} - {score_value}"
                )
                logger.error(ex)
                raise ex

        return attributes
