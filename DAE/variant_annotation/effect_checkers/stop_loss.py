from ..effect import Effect
import logging


class StopLossEffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        logger.debug("position check %d <= %d-%d <= %d",
                     request.transcript_model.cds[1] - 2,
                     request.variant.position,
                     last_position,
                     request.transcript_model.cds[0])

        try:
            ref_aa, alt_aa = request.get_amino_acids()
            ref_contains_stop = any(aa == "End" for aa in ref_aa)
            alt_contains_stop = any(aa == "End" for aa in alt_aa)

            logger.debug("ref aa=%s, alt aa=%s", ref_aa, alt_aa)

            if ref_contains_stop and not alt_contains_stop:
                ef = Effect("noEnd", request.transcript_model)
                start_prot, end_prot = request.get_protein_position()
                logger.debug("start_prot=%s, end_prot=%s",
                             start_prot, end_prot)
                if start_prot == end_prot:
                    ef.prot_pos = start_prot
                else:
                    ef.prot_pos = [prot
                                   for prot in range(start_prot,
                                                     end_prot + 1)]
                ef.prot_length = request.get_protein_length()
                return ef
        except IndexError:
            return
