import logging
from ..effect import EffectFactory


class CodingEffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", request.transcript_model.is_coding())
        if not request.transcript_model.is_coding():
            all_regs = request.transcript_model.all_regions()
            last_pos = request.variant.corrected_ref_position_last
            for region in all_regs:
                if request.variant.position <= region.stop \
                   and region.start <= last_pos:
                    return EffectFactory.create_effect_with_request(
                        "non-coding", request
                    )

            return EffectFactory.create_effect_with_request(
                "non-coding-intron", request
            )
