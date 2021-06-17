import logging

from dae.variants.attributes import VariantType

from dae.annotation.tools.annotator_base import Annotator
from dae.annotation.tools.reader import ScoreFile


logger = logging.getLogger(__name__)


class VariantScoreAnnotatorBase(Annotator):
    def __init__(self, config, genomes_db, liftover=None):
        super().__init__(config, genomes_db, liftover=None)
        self.score_file = ScoreFile(self.config)

    @property
    def output_columns(self):
        return [
            attr.dest for attr in self.config.default_annotation.attributes
        ]

    def _scores_not_found(self, aline):
        values = {score.id: None for score in self.score_file.config.scores}
        aline.update(values)

    def _fetch_scores(self, variant, extra_cols=None):
        scores = None
        if variant.variant_type & VariantType.substitution:
            scores = self.score_file.fetch_scores(
                variant.chromosome, variant.position, variant.position,
                extra_cols
            )
        elif variant.variant_type & VariantType.indel:
            scores = self.score_file.fetch_scores(
                variant.chromosome,
                variant.position,
                variant.position + len(variant.reference),
                extra_cols,
            )
        else:
            logger.warning(
                f"unexpected variant type in score annotation: "
                f"{variant}, {variant.variant_type}, "
                f"({variant.variant_type.value})"
            )
        return scores

    def _annotate_cnv(self, aline, variant):
        scores = self.score_file.fetch_highest_scores(
            variant.chromosome,
            variant.position,
            variant.end_position,
        )

        for score_name in self.score_names:
            column_name = getattr(self.config.columns, score_name)
            aline[column_name] = scores.get(
                score_name, self.score_file.no_score_value
            )


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db, liftover=None):
        super().__init__(config, genomes_db, liftover=None)

    @staticmethod
    def required_columns():
        return ("chrom", "pos_begin", "pos_end")

    def _convert_score(self, score):
        if score == "NA":
            return self.score_file.no_score_value
        else:
            return float(score)

    def _do_annotate(self, attributes, variant, liftover_variants):
        if VariantType.is_cnv(variant.variant_type):
            logger.info(
                f"skip trying to add position score for CNV variant {variant}")
            self._scores_not_found(attributes)
            return

        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(attributes)
            return

        scores = self._fetch_scores(variant)

        logger.debug(
            f"{self.score_file.filename} looking for score of {variant}")
        if not scores:
            logger.debug(
                f"{self.score_file.filename} score not found"
            )
            self._scores_not_found(attributes)
            return

        counts = scores["COUNT"]
        total_count = sum(counts)

        for score in self.score_file.config.scores:
            values = list(
                map(lambda x: self._convert_score(x), scores[score.id])
            )
            assert len(values) > 0
            if len(values) == 1:
                attributes[score.id] = values[0]
            else:
                values = list(filter(None, values))
                total_sum = sum(
                    [c * v for (c, v) in zip(counts, values)]
                )
                attributes[score.id] = \
                    (total_sum / total_count) if total_sum \
                    else self.score_file.no_score_value
                logger.debug(
                    f"attributes[{score.id}]={attributes[score.id]}")


class NPScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db, liftover=None):
        super().__init__(config, genomes_db, liftover=None)

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

    def _do_annotate(self, aline, variant, liftover_variants):
        if VariantType.is_cnv(variant.variant_type):
            logger.info(
                f"skip trying to add NP position score for CNV variant "
                f"{variant}")
            self._scores_not_found(aline)
            return

        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(aline)
            return

        scores = self._fetch_scores(
            variant, ["chrom", "pos_begin", "reference", "alternative"]
        )
        if not scores:
            self._scores_not_found(aline)
            return
        scores_df = self.score_file.scores_to_dataframe(scores)

        if variant.variant_type & VariantType.substitution:
            aline.update(self._aggregate_substitution(variant, scores_df))
        elif variant.variant_type & VariantType.indel:
            aline.update(self._aggregate_indel(variant, scores_df))
        else:
            logger.warning(
                f"unexpected variant type: {variant}, {variant.variant_type}"
            )
            self._scores_not_found(aline)
