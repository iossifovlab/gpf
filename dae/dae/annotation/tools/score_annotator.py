import logging

import pyarrow as pa

from dae.variants.attributes import VariantType
from dae.annotation.tools.annotator_base import Annotator
from dae.genomic_resources.score_resources import GenomicScoresResource

# from dae.genomic_resources.utils import aggregator_name_to_class


def aggregator_name_to_class(agg_name):
    # TODO IVAN
    raise Exception("THIS IS A STUB BY IVAN UNTILL I UNDERSTAND AND RESTORE")


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(self, resource, liftover=None, override=None):
        super().__init__(liftover, override)
        self.resource = resource

        assert isinstance(resource, GenomicScoresResource), \
            resource.resource_id
        self._annotation_schema = None

        self.score_types = dict()
        for score in self.resource.get_all_scores():
            print(score)

            self.score_types[score.id] = score.type

        self.non_default_position_aggregators = None
        self.non_default_nucleotide_aggregators = None
        self._collect_non_default_aggregators()

    def get_default_annotation(self):
        if self.override:
            return self.override.attributes
        return self.resource.get_default_annotation().attributes

    def _collect_non_default_aggregators(self):
        non_default_position_aggregators = {}
        non_default_nucleotide_aggregators = {}
        for attr in self.get_default_annotation():
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
        return [attr.source for attr in self.get_default_annotation()]

    def get_config(self):
        if self.override:
            return self.override
        return self.resource.get_default_annotation()

    @property
    def annotation_schema(self) -> pa.Schema:
        if self._annotation_schema is None:
            fields = []
            for attribute in self.get_config().attributes:
                prop_name = attribute.dest
                score_config = self.resource.get_score_config(attribute.source)
                prop_type = self.TYPES.get(score_config.type)
                assert prop_type is not None, score_config
                fields.append(pa.field(prop_name, prop_type, nullable=True))
            self._annotation_schema = pa.schema(fields)
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

    def _fetch_substitution_scores(self, variant):
        scores = self.resource.fetch_scores(
            variant.chromosome, variant.position,
            self.get_scores()
        )
        return scores

    def _fetch_aggregated_scores(self, variant, pos_begin, pos_end):
        scores_agg = self.resource.fetch_scores_agg(
            variant.chromosome,
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

    def _do_annotate_allele(self, attributes, allele, liftover_context):
        if self.liftover:
            allele = liftover_context.get(self.liftover)

        if allele is None:
            self._scores_not_found(attributes)
            return

        if allele.chromosome not in self.resource.get_all_chromosomes():
            self._scores_not_found(attributes)
            return

        if allele.variant_type & VariantType.substitution:
            scores = self._fetch_substitution_scores(allele)
        else:
            if allele.variant_type & VariantType.indel:
                pos_begin = allele.position
                pos_end = allele.position + len(allele.reference)
            elif VariantType.is_cnv(allele.variant_type):
                pos_begin = allele.position
                pos_end = allele.end_position
            else:
                message = f"unexpected variant type in score annotation: " \
                    f"{allele}, {allele.variant_type}, " \
                    f"({allele.variant_type.value})"
                logger.warning(message)
                raise ValueError(message)

            if pos_end - pos_begin > 500_000:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(
                    allele, pos_begin, pos_end)
        if not scores:
            self._scores_not_found(attributes)
            return

        for score in self.get_scores():
            value = scores[score]
            attributes[score] = value


class NPScoreAnnotator(PositionScoreAnnotator):
    def __init__(self, config, liftover=None, override=None):
        super().__init__(config, liftover, override)

    def _fetch_substitution_scores(self, allele):
        return self.resource.fetch_scores(
            allele.chromosome, allele.position,
            allele.reference, allele.alternative,
            self.get_scores()
        )

    def _fetch_aggregated_scores(self, allele, pos_begin, pos_end):
        scores_agg = self.resource.fetch_scores_agg(
            allele.chromosome,
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
