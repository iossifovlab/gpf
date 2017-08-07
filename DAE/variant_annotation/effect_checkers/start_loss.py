from ..effect import Effect
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
                        ef = Effect("noStart", request.transcript_model)
                        start_prot, end_prot = request.get_protein_position()
                        logger.debug("start_prot=%s, end_prot=%s",
                                     start_prot, end_prot)
                        ef.prot_pos = start_prot
                        ef.prot_length = request.get_protein_length()
                        return ef
            else:
                if (request.variant.position <= request.transcript_model.cds[1]
                        and request.transcript_model.cds[1] - 2 <=
                        last_position):

                    if request.find_start_codon() is None:
                        ef = Effect("noStart", request.transcript_model)
                        start_prot, end_prot = request.get_protein_position()
                        logger.debug("start_prot=%s, end_prot=%s",
                                     start_prot, end_prot)
                        ef.prot_pos = start_prot
                        ef.prot_length = request.get_protein_length()
                        return ef
        except IndexError:
            return
