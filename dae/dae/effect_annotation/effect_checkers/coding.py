import logging
from typing import Optional

from ..effect import EffectFactory
from .effect_checker import AnnotationEffect, AnnotationRequest, EffectChecker


class CodingEffectChecker(EffectChecker):
    """Coding effect checker class."""

    def get_effect(
        self, request: AnnotationRequest,
    ) -> Optional[AnnotationEffect]:
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", request.transcript_model.is_coding())
        if not request.transcript_model.is_coding():
            all_regs = request.transcript_model.all_regions()
            last_pos = request.variant.corrected_ref_position_last
            for region in all_regs:
                if request.variant.position <= region.stop \
                   and region.start <= last_pos:
                    return EffectFactory.create_effect_with_request(
                        "non-coding", request,
                    )

            return EffectFactory.create_effect_with_request(
                "non-coding-intron", request,
            )
        return None
