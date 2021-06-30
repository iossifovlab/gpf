#!/usr/bin/env python
import logging

from dae.variants.attributes import VariantType
from dae.annotation.tools.score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class FrequencyAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db, liftover=None, override=None):
        super().__init__(config, genomes_db, liftover, override)

    @staticmethod
    def required_columns():
        return ("chrom", "pos_begin", "pos_end", "variant")

    def _do_annotate(self, attributes, variant, liftover_variants):
        if VariantType.is_cnv(variant.variant_type):
            logger.info(
                f"skip trying to add frequency for CNV variant {variant}")
            self._scores_not_found(attributes)
            return

        if self.liftover:
            variant = liftover_variants.get(self.liftover)

        if variant is None:
            self._scores_not_found(attributes)
            return

        if self.liftover and liftover_variants.get(self.liftover):
            variant = liftover_variants.get(self.liftover)

        chrom = variant.chromosome
        pos = variant.details.cshl_position
        scores = self.score_file.fetch_scores(chrom, pos, pos, ["variant"])
        if not scores:
            self._scores_not_found(attributes)
            return
        variant_detail = variant.details.cshl_variant

        variant_occurrences = scores["variant"].count(variant_detail)

        if variant_occurrences == 0:
            self._scores_not_found(attributes)
            return

        if variant_occurrences > 1:
            logger.warning(
                f"WARNING {self.score_file.filename}: "
                f"multiple variant occurrences of {chrom}:{pos} {variant}"
            )

        variant_index = scores["variant"].index(variant_detail)
        for score_id in self.score_file.score_ids:
            val = scores[score_id][variant_index]
            try:
                if val in ("", " "):
                    attributes[score_id] = None
                else:
                    attributes[score_id] = float(val)
            except ValueError as ex:
                logger.error(
                    f"problem with: {score_id}: {chrom}:{pos} - {val}"
                )
                logger.error(ex)
                raise ex
