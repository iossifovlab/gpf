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
            print("override:", self.override)
            return self.override.attributes
        print("resource:", self.resource.get_default_annotation())
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
        print(100*"=")
        print(self.non_default_position_aggregators)
        print(100*"=")

    def get_scores(self):
        return [attr.source for attr in self.get_default_annotation()]

    def get_config(self):
        if self.override:
            print("override:", self.override)
            return self.override
        print("resource:", self.resource.get_default_annotation())

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

    def _fetch_scores(self, variant, extra_cols=None):
        scores = None
        print("variant_type:", variant.variant_type)
        if variant.variant_type & VariantType.substitution:
            scores = self.resource.fetch_scores(
                variant.chromosome, variant.position,
                self.get_scores()
            )
        elif variant.variant_type & VariantType.indel:
            scores = self.resource.fetch_scores_agg(
                variant.chromosome,
                variant.position,
                variant.position + len(variant.reference),
                self.get_scores(),
                self.non_default_position_aggregators
            )
        else:
            logger.warning(
                f"unexpected variant type in score annotation: "
                f"{variant}, {variant.variant_type}, "
                f"({variant.variant_type.value})"
            )
            raise Exception
        return scores

    def _annotate_cnv(self, attributes, variant):
        scores = self.resource.fetch_scores_agg(
            variant.chromosome,
            variant.position,
            variant.end_position,
            self.get_scores()
        )

        for score_name in self.score_names:
            column_name = getattr(self.config.columns, score_name)
            attributes[column_name] = scores.get(
                score_name, self.score_file.no_score_value
            )


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, resource, liftover=None, override=None):
        super().__init__(resource, liftover, override)
        # FIXME This should be closed somewhere
        self.resource.open()

    def _fetch_substition(self, variant):
        return self.resource.fetch_scores(
            variant.chromosome, variant.position,
            self.get_scores()
        )

    def _do_annotate(self, attributes, variant, liftover_variants):
        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(attributes)
            return

        if variant.chromosome not in self.resource.get_all_chromosomes():
            self._scores_not_found(attributes)
            return

        if variant.variant_type & VariantType.substitution:
            scores = self._fetch_substition(variant)
        else:
            if variant.variant_type & VariantType.indel:
                first_position = variant.position
                last_position = variant.position + len(variant.reference)
            elif VariantType.is_cnv(variant.variant_type):
                first_position = variant.position
                last_position = variant.end_position
            else:
                logger.warning(
                    f"unexpected variant type in score annotation: "
                    f"{variant}, {variant.variant_type}, "
                    f"({variant.variant_type.value})"
                )
                raise Exception
            if last_position - first_position > 500_000:
                scores = None
            else:
                scores = self.resource.fetch_scores_agg(
                    variant.chromosome,
                    first_position,
                    last_position,
                    self.get_scores(),
                    self.non_default_position_aggregators
                )

        if not scores:
            self._scores_not_found(attributes)
            return

        for score in self.get_scores():
            value = scores[score]
            attributes[score] = value


class NPScoreAnnotator(PositionScoreAnnotator):
    def __init__(self, config, liftover=None, override=None):
        super().__init__(config, liftover, override)

    def _fetch_substition(self, variant):
        return self.resource.fetch_scores(
            variant.chromosome, variant.position,
            variant.reference, variant.alternative,
            self.get_scores()
        )
