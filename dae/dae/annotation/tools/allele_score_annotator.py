#!/usr/bin/env python
import logging

from dae.variants.attributes import VariantType
from dae.annotation.tools.score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class AlleleScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, resource, genomes_db, liftover=None, override=None):
        super().__init__(resource, genomes_db, liftover, override)
        self.resource.open()

    def _collect_aggregators(self, attr):
        return []

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
        variant_detail = variant.details.cshl_variant

        scores_dict = self.resource.fetch_scores(
            chrom, pos, variant_detail
        )
        if scores_dict is None:
            print("Not found!")
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
                    f"problem with: {score_id}: {chrom}:{pos} - {score_value}"
                )
                logger.error(ex)
                raise ex
