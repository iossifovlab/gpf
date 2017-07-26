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
                    seq = request.annotator.reference_genome.getSequence(
                        request.transcript_model.chr,
                        request.transcript_model.cds[0],
                        request.transcript_model.cds[0] + 2
                    )

                    if request.find_start_codon([seq]) is None:
                        ef = Effect("noStart", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
            else:
                if (request.variant.position <= request.transcript_model.cds[1]
                        and request.transcript_model.cds[1] - 2 <=
                        last_position):

                    ref_codons, alt_codons = request.get_codons()

                    seq = request.annotator.reference_genome.getSequence(
                        request.transcript_model.chr,
                        request.transcript_model.cds[1] - 2,
                        request.transcript_model.cds[1]
                    )

                    if request.find_start_codon([seq]) is None:
                        ef = Effect("noStart", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
        except IndexError:
            return
