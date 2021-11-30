import logging
import copy

from typing import Optional, Dict, List
from box import Box

from .schema import Schema
from .annotatable import Annotatable, VCFAllele
from .annotator_base import Annotator, ATTRIBUTES_SCHEMA
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
        "id": {
            "type": "string",
            "required": False,
        },
        "resource_id": {
            "type": "string",
            "required": True,
        },
        "liftover_id": {
            "type": "string",
            "nullable": True,
            "default": None
        },
        "attributes": {
            "type": "list",
            "nullable": True,
            "default": None,
            "schema": None
        }
    }

    class ScoreSource(Schema.Source):
        def __init__(
                self, annotator_type: str, resource_id: str,
                score_id: str,
                position_aggregator: Optional[None] = None,
                nucleotide_aggregator: Optional[None] = None):
            super().__init__(annotator_type, resource_id)
            self.score_id = score_id
            self.position_aggregator = position_aggregator
            self.nucleotide_aggregator = nucleotide_aggregator

        def __repr__(self):
            repr = [super().__repr__(), ]
            if self.position_aggregator:
                repr.append(f"pos_aggr({self.position_aggregator})")
            if self.nucleotide_aggregator:
                repr.append(f"nuc_aggre({self.nucleotide_aggregator})")
            return "; ".join(repr)

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
                "source": score.id,
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

    @property
    def annotation_schema(self) -> Schema:
        if self._annotation_schema is None:
            schema = Schema()
            for attribute in self.get_annotation_config():
                prop_name = attribute.destination
                score_config = self.resource.get_score_config(attribute.source)
                py_type = score_config.type
                assert py_type is not None, score_config
                score_id = attribute.source
                source = self.ScoreSource(
                    self.annotator_type(),
                    self.resource.resource_id,
                    score_id,
                    self.non_default_position_aggregators.get(score_id),
                    self.non_default_position_aggregators.get(score_id))

                schema.create_field(prop_name, py_type, source)

            self._annotation_schema = schema
        return self._annotation_schema

    def _scores_not_found(self, attributes):
        values = {
            score_id: None for score_id in self.get_scores()
        }
        attributes.update(values)


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
            self, attributes, annotatable: Annotatable, liftover_context):
        if self.liftover_id:
            annotatable = liftover_context.get(self.liftover_id)

        if annotatable is None:
            self._scores_not_found(attributes)
            return

        if annotatable.chromosome not in self.resource.get_all_chromosomes():
            self._scores_not_found(attributes)
            return

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
            return

        for score in self.get_scores():
            value = scores[score]
            attributes[score] = value


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
        scores = {
            sc_name: sc_agg.get_final()
            for sc_name, sc_agg in scores_agg.items()
        }
        return scores


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
        return validator.document

    @staticmethod
    def annotator_type():
        return "allele_score"

    def _do_annotate(
            self, attributes, annotatable: Annotatable, liftover_context):

        if not isinstance(annotatable, VCFAllele):
            logger.info(
                f"skip trying to add frequency for CNV variant {annotatable}")
            self._scores_not_found(attributes)
            return

        if self.liftover_id:
            annotatable = liftover_context.get(self.liftover_id)

        if annotatable is None:
            self._scores_not_found(attributes)
            return

        # if self.liftover and liftover_context.get(self.liftover):
        #     allele = liftover_context.get(self.liftover)

        scores_dict = self.resource.fetch_scores(
            annotatable.chromosome,
            annotatable.position,
            annotatable.reference,
            annotatable.alternative
        )
        if scores_dict is None:
            self._scores_not_found(attributes)
            return

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
