from ..effect import Effect
from ..mutation import GenomicSequence


class StopLossEffectChecker:
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

    @classmethod
    def _in_start_codons(cls, codon, annotator):
        codon = cls.complement(codon[::-1])
        if codon in annotator.code.startCodons:
            return True
        else:
            return False

    @classmethod
    def _in_stop_codons(cls, codon, annotator):
        if codon in annotator.code.stopCodons:
            return True
        else:
            return False

    def get_effect(self, annotator, variant, transcript_model):
        if (transcript_model.cds[1] - 2 <= variant.position
                <= transcript_model.cds[1]):
            ref = GenomicSequence(
                annotator, variant, transcript_model
            )
            ref_codons, alt_codons = ref.get_codons()

            if transcript_model.strand == "+":
                if (self._in_stop_codons(ref_codons[:3], annotator) and
                        not self._in_stop_codons(alt_codons[:3], annotator)):
                    ef = Effect("noEnd", transcript_model)
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
            else:
                if (self._in_start_codons(ref_codons[:3], annotator) and
                        not self._in_start_codons(alt_codons[:3], annotator)):
                    ef = Effect("noStart", transcript_model)
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
