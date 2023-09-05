import logging
from typing import Optional

from ..effect import EffectFactory
from .effect_checker import EffectChecker, AnnotationEffect, AnnotationRequest

logger = logging.getLogger(__name__)


class IntronicEffectChecker(EffectChecker):
    """Intonic effect checker class."""

    def __init__(self, splice_site_length: int = 2):
        self.splice_site_length = splice_site_length

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:

        coding_regions = request.cds_regions()
        prev = coding_regions[0].stop

        last_position = request.variant.corrected_ref_position_last

        intron_regions_before_coding = 0
        for exon in request.transcript_model.exons:
            logger.debug(
                "reg %d-%d cds:%d",
                exon.start,
                exon.stop,
                request.transcript_model.cds[0],
            )
            if request.transcript_model.cds[0] <= exon.stop:
                break
            intron_regions_before_coding += 1

        for i, j in enumerate(coding_regions):
            logger.debug(
                "pos: %d-%d checking intronic region %d-%d",
                request.variant.position,
                last_position,
                prev,
                j.start,
            )
            if prev < request.variant.position and last_position < j.start:
                return EffectFactory.create_intronic_effect(
                    "intron",
                    request,
                    prev,
                    j.start,
                    intron_regions_before_coding + i,
                )
            prev = j.stop

        return None
