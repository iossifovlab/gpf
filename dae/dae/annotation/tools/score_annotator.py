import logging

from dae.variants.attributes import VariantType

from dae.annotation.tools.annotator_base import Annotator

from dae.genomic_resources.utils import aggregator_name_to_class


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(
            self, config, genomes_db, resource_db,
            liftover=None, override=None):
        super().__init__(config, genomes_db, resource_db, liftover, override)

        resource = self.resource_db.get_resource(config.resource)
        self._resource = resource

        self.score_types = dict()
        for score in self.resource._config.scores:
            self.score_types[score.id] = score.type

        self.type_aggregators = dict()
        for agg in self.resource._config.type_aggregators:
            self.type_aggregators[agg.type] = agg.aggregator

    @property
    def resource(self):
        raise NotImplementedError

    @property
    def output_columns(self):
        return [
            attr.dest for attr in self.config.default_annotation.attributes
        ]

    def _scores_not_found(self, attributes):
        values = {score.id: None for score in self.score_file.config.scores}
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
    def __init__(
            self, config, genomes_db, resource_db,
            liftover=None, override=None):
        super().__init__(config, genomes_db, resource_db, liftover, override)

    @property
    def resource(self):
        return self._resource

    def _do_annotate(self, attributes, variant, liftover_variants):
        self._resource.open()
        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(attributes)
            return

        if variant.variant_type & VariantType.substitution:
            scores = self.resource.fetch_scores(
                variant.chromosome, variant.position,
                self.resource.get_default_scores()
            )
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
            aggregators = dict()
            for attr in self.resource._config.default_annotation.attributes:
                aggr_name = attr.aggregator.position
                if aggr_name is None:
                    score_type = self.score_types[attr.source]
                    aggr_name = self.type_aggregators[score_type]
                aggregators[attr.source] = aggregator_name_to_class(
                    aggr_name
                )
            scores = self.resource.fetch_scores_agg(
                variant.chromosome,
                first_position,
                last_position,
                aggregators
            )

        if not scores:
            self._scores_not_found(attributes)
            return

        for score in self.resource._config.scores:
            value = scores[score.id]
            attributes[score.id] = value
        self._resource.close()


class NPScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db, liftover=None, override=None):
        super().__init__(config, genomes_db, liftover, override)

    @staticmethod
    def required_columns():
        return ("chrom", "pos_begin", "pos_end", "reference", "alternative")

    def _aggregate_substitution(self, variant, scores_df):
        assert variant.variant_type == VariantType.substitution

        res = {}
        matched = (scores_df["reference"] == variant.reference) & (
                scores_df["alternative"] == variant.alternative
        )
        matched_df = scores_df[matched]
        if len(matched_df) == 0:
            self._scores_not_found(res)
        else:
            for score_id in self.score_file.score_ids:
                res[score_id] = matched_df[score_id].mean()
        return res

    def _aggregate_indel(self, variant, scores_df):
        assert VariantType.indel & variant.variant_type, variant

        aggregate = {sn: "max" for sn in self.score_file.score_ids}

        aggregate["COUNT"] = "max"
        group_df = scores_df.groupby(by=["chrom", "pos_begin"]).agg(aggregate)
        count = group_df["COUNT"].sum()
        res = {}
        for score_id in self.score_file.score_ids:
            total_df = group_df[score_id] * group_df["COUNT"]
            res[score_id] = total_df.sum() / count

        return res

    def _do_annotate(self, attributes, variant, liftover_variants):
        if VariantType.is_cnv(variant.variant_type):
            logger.info(
                f"skip trying to add NP position score for CNV variant "
                f"{variant}")
            self._scores_not_found(attributes)
            return

        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(attributes)
            return

        scores = self._fetch_scores(
            variant, ["chrom", "pos_begin", "reference", "alternative"]
        )
        if not scores:
            self._scores_not_found(attributes)
            return
        scores_df = self.score_file.scores_to_dataframe(scores)

        if variant.variant_type & VariantType.substitution:
            attributes.update(self._aggregate_substitution(variant, scores_df))
        elif variant.variant_type & VariantType.indel:
            attributes.update(self._aggregate_indel(variant, scores_df))
        else:
            logger.warning(
                f"unexpected variant type: {variant}, {variant.variant_type}"
            )
            self._scores_not_found(attributes)
