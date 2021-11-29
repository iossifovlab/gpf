#!/usr/bin/env python
import logging

from .annotatable import Annotatable, VCFAllele
from .score_annotator import VariantScoreAnnotatorBase


logger = logging.getLogger(__name__)


class AlleleScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, pipeline, config):
        super().__init__(pipeline, config)
        self.resource.open()

    @property
    def annotator_type(self):
        return "allele_score_annotator"

    def _do_annotate(
            self, attributes, annotatable: Annotatable, liftover_context):

        if not isinstance(annotatable, VCFAllele):
            logger.info(
                f"skip trying to add frequency for CNV variant {annotatable}")
            self._scores_not_found(attributes)
            return

        if self.liftover_id:
            annotatable = liftover_context.get(self.liftover_id)

        if annotatable is None:
            self._scores_not_found(attributes)
            return

        # if self.liftover and liftover_context.get(self.liftover):
        #     allele = liftover_context.get(self.liftover)

        scores_dict = self.resource.fetch_scores(
            annotatable.chromosome,
            annotatable.position,
            annotatable.reference,
            annotatable.alternative
        )
        if scores_dict is None:
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
                    f"problem with: {score_id}: {annotatable} - {score_value}"
                )
                logger.error(ex)
                raise ex
