#!/usr/bin/env python
import logging

from dae.variants.core import Allele
from dae.annotation.tools.score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class AlleleScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, resource, liftover=None, override=None):
        super().__init__(resource, liftover, override)
        self.resource.open()

    @property
    def annotator_type(self):
        return "allele_score_annotator"

    def _do_annotate_allele(self, attributes, allele, liftover_context):
        if allele.allele_type & Allele.Type.cnv:
            logger.info(
                f"skip trying to add frequency for CNV variant {allele}")
            self._scores_not_found(attributes)
            return

        if self.liftover:
            allele = liftover_context.get(self.liftover)

        if allele is None:
            self._scores_not_found(attributes)
            return

        # if self.liftover and liftover_context.get(self.liftover):
        #     allele = liftover_context.get(self.liftover)

        scores_dict = self.resource.fetch_scores(
            allele.chromosome,
            allele.position,
            allele.reference,
            allele.alternative
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
                    f"problem with: {score_id}: {allele} - {score_value}"
                )
                logger.error(ex)
                raise ex
