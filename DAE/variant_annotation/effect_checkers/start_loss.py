from ..effect import Effect
import logging


class StartLossEffectChecker:
    @staticmethod
    def complement(nts):
        nts = nts.upper()
        reversed = ''
        for nt in nts:
            if nt == "A":
                reversed += "T"
            elif nt == "T":
                reversed += "A"
            elif nt == "G":
                reversed += "C"
            elif nt == "C":
                reversed += "G"
            elif nt == "N":
                reversed += "N"
            else:
                print("Invalid nucleotide: " + str(nt) + " in " + str(nts))
        return(reversed)

    @staticmethod
    def _in_start_codons(codon, annotator):
        if codon in annotator.code.startCodons:
            return True
        else:
            return False

    @classmethod
    def _in_start_codons_complement(cls, codon, annotator):
        codon = cls.complement(codon[::-1])
        if codon in annotator.code.startCodons:
            return True
        else:
            return False

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

                    if (not self._in_start_codons(seq, request.annotator)):
                        return
                    if request.find_start_codon() is None:
                        ef = Effect("noStart", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
            else:
                if (request.variant.position <= request.transcript_model.cds[1]
                        and request.transcript_model.cds[1] - 2 <=
                        last_position):

                    ref_codons, alt_codons = request.get_codons()

                    logger.debug("effected codons: %s->%s",
                                 ref_codons[:3], alt_codons[:3])

                    if (self._in_start_codons_complement(
                        ref_codons[:3], request.annotator) and
                        not self._in_start_codons_complement(
                                alt_codons[:3], request.annotator)):
                        ef = Effect("noStart", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
        except IndexError:
            return
