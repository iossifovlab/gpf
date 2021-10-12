import logging

import pyarrow as pa

from dae.variants.attributes import VariantType
from dae.annotation.tools.annotator_base import Annotator
from dae.genomic_resources.utils import aggregator_name_to_class

logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(self, resource, liftover=None, override=None):
        super().__init__(liftover, override)
        self.resource = resource
        self._annotation_schema = None

        self.score_types = dict()
        for score in self.resource.get_config().scores:
            self.score_types[score.id] = score.type

        if self.resource.get_config().type_aggregators:
            self.type_aggregators = dict()
            for agg in self.resource.get_config().type_aggregators:
                self.type_aggregators[agg.type] = agg.aggregator

        self.aggregators = dict()
        for attr in self.get_config().attributes:
            self.aggregators[attr.source] = self._get_aggregators(attr)

    def get_default_annotation(self):
        if self.override:
            print("override:", self.override)
            return self.override.attributes
        print("resource:", self.resource.get_default_annotation())
        return self.resource.get_default_annotation().attributes

    def get_config(self):
        if self.override:
            print("override:", self.override)
            return self.override
        print("resource:", self.resource.get_config().default_annotation)

        return self.resource.get_config().default_annotation

    def _get_aggregators(self, attr):
        raise NotImplementedError()

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
            score_id: None for score_id in self.resource.get_default_scores()
        }
        attributes.update(values)

    def _fetch_scores(self, variant, extra_cols=None):
        scores = None
        if variant.variant_type & VariantType.substitution:
            scores = self.resource.fetch_scores(
                variant.chromosome, variant.position,
            )
        elif variant.variant_type & VariantType.indel:
            scores = self.resource.fetch_scores_agg(
                variant.chromosome,
                variant.position,
                variant.position + len(variant.reference),
                self.aggregators
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
        aggregators = dict()
        for attr in self.config.default_annotation.attributes:
            aggr_name = attr.aggregator
            if aggr_name is None:
                score_type = self.score_types[attr.source]
                aggr_name = self.type_aggregators[score_type]
            aggregators[attr.source] = aggregator_name_to_class(
                aggr_name
            )
        scores = self.resource.fetch_scores_agg(
            variant.chromosome,
            variant.position,
            variant.end_position,
            aggregators
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

    def _get_aggregators(self, attr):
        aggr_name = attr.aggregator.position
        if aggr_name is None:
            score_type = self.score_types[attr.source]
            aggr_name = self.type_aggregators[score_type]
        return aggregator_name_to_class(aggr_name)

    def _fetch_substition(self, variant):
        return self.resource.fetch_scores(
            variant.chromosome, variant.position,
            self.resource.get_default_scores()
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
                    self.aggregators,
                )

        if not scores:
            self._scores_not_found(attributes)
            return

        for score in self.resource._config.scores:
            value = scores[score.id]
            attributes[score.id] = value


class NPScoreAnnotator(PositionScoreAnnotator):
    def __init__(self, config, liftover=None, override=None):
        super().__init__(config, liftover, override)

    def _get_aggregators(self, attr):
        aggr_name = attr.aggregator.position
        if aggr_name is None:
            score_type = self.score_types[attr.source]
            aggr_name = self.type_aggregators[score_type]
        pos_aggr = aggregator_name_to_class(aggr_name)

        aggr_name = attr.aggregator.nucleotide
        if aggr_name is None:
            score_type = self.score_types[attr.source]
            aggr_name = self.type_aggregators[score_type]
        nuc_aggr = aggregator_name_to_class(aggr_name)

        return (pos_aggr, nuc_aggr)

    def _fetch_substition(self, variant):
        return self.resource.fetch_scores(
            variant.chromosome, variant.position,
            variant.reference, variant.alternative,
            self.resource.get_default_scores()
        )
