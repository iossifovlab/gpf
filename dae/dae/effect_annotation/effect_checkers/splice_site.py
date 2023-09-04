import logging
from typing import Optional

from ..effect import EffectFactory
from .effect_checker import EffectChecker, AnnotationEffect, AnnotationRequest

logger = logging.getLogger(__name__)


class SpliceSiteEffectChecker(EffectChecker):
    """Splice site effect checker class."""

    def __init__(self, splice_site_length: int = 2):
        self.splice_site_length = splice_site_length

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        coding_regions = request.transcript_model.exons
        last_position = request.variant.position + len(
            request.variant.reference
        )
        prev = None

        for i, j in enumerate(coding_regions):
            if prev is None:
                prev = j.stop
                continue

            logger.debug(
                "pos: %d-%d checking intronic region %d-%d %d",
                request.variant.position,
                last_position,
                prev,
                j.start,
                j.stop,
            )

            if (
                request.variant.position < prev + self.splice_site_length + 1
                and prev + 1 < last_position
            ):
                return EffectFactory.create_intronic_effect(
                    "splice-site", request, prev, j.start, i
                )

            if (
                request.variant.position < j.start
                and j.start - self.splice_site_length < last_position
            ):
                return EffectFactory.create_intronic_effect(
                    "splice-site", request, prev, j.start, i
                )
            prev = j.stop

        return None
