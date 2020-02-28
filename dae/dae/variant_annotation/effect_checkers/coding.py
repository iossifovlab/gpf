from ..effect import EffectFactory
import logging


class CodingEffectChecker(object):
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", request.transcript_model.is_coding())
        if not request.transcript_model.is_coding():
            all_regs = request.transcript_model.all_regions()
            last_pos = request.variant.corrected_ref_position_last
            for r in all_regs:
                if request.variant.position <= r.stop and r.start <= last_pos:
                    return EffectFactory.create_effect_with_request(
                        "non-coding", request
                    )

            return EffectFactory.create_effect_with_request(
                "non-coding-intron", request
            )
