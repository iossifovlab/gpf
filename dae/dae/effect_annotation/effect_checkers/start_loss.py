from ..effect import EffectFactory
import logging


class StartLossEffectChecker(object):
    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        last_position = request.variant.position + len(
            request.variant.reference
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
                "noStart", request
            )
