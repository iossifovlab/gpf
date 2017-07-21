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
    def _in_stop_codons(cls, codon, annotator):
        codon = cls.complement(codon[::-1])
        if codon in annotator.code.stopCodons:
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

        if (request.variant.position <= request.transcript_model.cds[0] + 2
                and request.transcript_model.cds[0] <= last_position):
            try:
                if request.transcript_model.strand == "+":
                    if not request.find_start_codon():
                        ef = Effect("noStart", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
                    return

                ref_codons, alt_codons = request.get_codons()

                logger.debug("effected codons: %s->%s",
                             ref_codons[:3], alt_codons[:3])

                if request.transcript_model.strand == "-":
                    if (self._in_stop_codons(ref_codons[:3],
                                             request.annotator) and
                            not self._in_stop_codons(alt_codons[:3],
                                                     request.annotator)):
                        ef = Effect("noEnd", request.transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
            except IndexError:
                return
