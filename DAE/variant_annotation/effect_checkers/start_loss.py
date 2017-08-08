from ..effect import EffectFactory
import logging


class StartLossEffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        last_position = request.variant.position + \
            len(request.variant.reference)

        logger.debug("position check %d <= %d-%d <= %d",
                     request.transcript_model.cds[0], request.variant.position,
                     last_position,
                     request.transcript_model.cds[0] + 2)
        try:
            if request.transcript_model.strand == "+":
                if (request.variant.position <=
                    request.transcript_model.cds[0] + 2
                        and request.transcript_model.cds[0] <= last_position):
                    if request.find_start_codon() is None:
                        return EffectFactory.create_effect_with_prot_pos(
                            "noStart", request
                        )
            else:
                if (request.variant.position <= request.transcript_model.cds[1]
                        and request.transcript_model.cds[1] - 2 <=
                        last_position):

                    if request.find_start_codon() is None:
                        return EffectFactory.create_effect_with_prot_pos(
                            "noStart", request
                        )
        except IndexError:
            return
