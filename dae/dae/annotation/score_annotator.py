import logging

from .schema import Schema
from .annotatable import Annotatable
from .annotator_base import Annotator
from dae.genomic_resources.score_resources import GenomicScoresResource


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(
            self, resource: GenomicScoresResource,
            liftover=None, override=None):

        super().__init__(liftover, override)
        self.resource = resource

        assert isinstance(resource, GenomicScoresResource), \
            resource.resource_id
        self._annotation_schema = None

        self.score_types = dict()
        for score in self.resource.get_all_scores():
            self.score_types[score.id] = score.type

        self.non_default_position_aggregators = None
        self.non_default_nucleotide_aggregators = None
        self._collect_non_default_aggregators()

    def get_annotation_config(self):
        if self.override:
            return self.override.attributes
        if self.resource.get_default_annotation():
            return self.resource.get_default_annotation().attributes
        return {}

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
                prop_name = attribute.dest
                score_config = self.resource.get_score_config(attribute.source)
                py_type = score_config.type
                pa_type = self.TYPES.get(score_config.type)
                assert py_type is not None, score_config
                schema.create_field(
                    prop_name, py_type, pa_type,
                    self.annotator_type, self.resource.resource_id,
                    attribute.source)

            self._annotation_schema = schema
        return self._annotation_schema

    def _scores_not_found(self, attributes):
        values = {
            score_id: None for score_id in self.get_scores()
        }
        attributes.update(values)


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, resource, liftover=None, override=None):
        super().__init__(resource, liftover, override)
        # FIXME This should be closed somewhere
        self.resource.open()

    @property
    def annotator_type(self):
        return "position_score_annotator"

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
        if self.liftover:
            annotatable = liftover_context.get(self.liftover)

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
                    annotatable.pos_begin, annotatable.pos_end)
        if not scores:
            self._scores_not_found(attributes)
            return

        for score in self.get_scores():
            value = scores[score]
            attributes[score] = value


class NPScoreAnnotator(PositionScoreAnnotator):
    def __init__(self, config, liftover=None, override=None):
        super().__init__(config, liftover, override)

    @property
    def annotator_type(self):
        return "np_score_annotator"

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
