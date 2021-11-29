import logging

from typing import Optional
from box import Box

from .schema import Schema
from .annotatable import Annotatable
from .annotator_base import Annotator
from dae.genomic_resources.score_resources import GenomicScoresResource


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):

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

    def __init__(self, config: Box, resource):

        super().__init__(config)

        self.resource = resource
        self.liftover_id = self.config.get("liftover_id")

        assert isinstance(resource, GenomicScoresResource), \
            resource.resource_id
        self._annotation_schema = None

        self.non_default_position_aggregators = {}
        self.non_default_nucleotide_aggregators = {}
        self._collect_non_default_aggregators()

    def get_annotation_config(self):
        if self.config.get("attributes"):
            return self.config.attributes
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
                    self.annotator_type,
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

    @property
    def annotator_type(self):
        return "position_score"

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

    @property
    def annotator_type(self):
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
