import logging

from ..effect import EffectFactory
from .effect_checker import AnnotationEffect, AnnotationRequest, EffectChecker

logger = logging.getLogger(__name__)


class StartLossEffectChecker(EffectChecker):
    """Start loss effect checker class."""

    def get_effect(
        self, request: AnnotationRequest,
    ) -> AnnotationEffect | None:
        assert request.variant.reference is not None
        last_position = request.variant.position + len(
            request.variant.reference,
        )

        logger.debug(
            "position check %d <= %d-%d <= %d",
            request.transcript_model.cds[0],
            request.variant.position,
            last_position,
            request.transcript_model.cds[0] + 2,
        )
        if request.is_start_codon_affected():
            return EffectFactory.create_effect_with_prot_pos(
                "noStart", request,
            )
        return None
