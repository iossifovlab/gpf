import logging

from dae.variants.attributes import VariantType

from dae.annotation.tools.annotator_base import Annotator

from dae.genomic_resources.utils import aggregator_name_to_class


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(self, resource, genomes_db, liftover=None, override=None):
        super().__init__(resource, genomes_db, liftover, override)

        self.score_types = dict()
        for score in self.resource._config.scores:
            self.score_types[score.id] = score.type

        if self.resource._config.type_aggregators:
            self.type_aggregators = dict()
            for agg in self.resource._config.type_aggregators:
                self.type_aggregators[agg.type] = agg.aggregator

        self.aggregators = dict()
        for attr in self.config.attributes:
            self.aggregators[attr.source] = self._collect_aggregators(attr)

    def _collect_aggregators(self, attr):
        raise NotImplementedError()

    @property
    def output_columns(self):
        return [
            attr.dest for attr in self.config.attributes
        ]

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
            scores = self.resource.fetch_scores(
                variant.chromosome,
                variant.position,
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
    def __init__(self, resource, genomes_db, liftover=None, override=None):
        super().__init__(resource, genomes_db, liftover, override)
        # FIXME This should be closed somewhere
        self.resource.open()

    def _collect_aggregators(self, attr):
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

        if variant.variant_type & VariantType.substitution:
            scores = self._fetch_substition(variant)
        else:
            if variant.variant_type & VariantType.indel:
                first_position = variant.position-1
                last_position = variant.position + len(variant.reference)
            elif variant.is_cnv():
                first_position = variant.position
                last_position = variant.end_position
            else:
                logger.warning(
                    f"unexpected variant type in score annotation: "
                    f"{variant}, {variant.variant_type}, "
                    f"({variant.variant_type.value})"
                )
                raise Exception
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
    def __init__(self, config, genomes_db, liftover=None, override=None):
        super().__init__(config, genomes_db, liftover, override)

    def _collect_aggregators(self, attr):
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
