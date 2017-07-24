from ..effect import Effect
import logging


class CodingEffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", request.transcript_model.is_coding())
        if not request.transcript_model.is_coding():
            all_regs = request.transcript_model.all_regions()
            last_pos = request.variant.position + \
                len(request.variant.reference)
            for r in all_regs:
                if (request.variant.position <= r.stop
                        and r.start < last_pos):
                    return Effect("non-coding", request.transcript_model)

            return Effect("non-coding-intron", request.transcript_model)
