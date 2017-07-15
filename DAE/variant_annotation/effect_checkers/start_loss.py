from ..effect import Effect
from ..mutation import GenomicSequence


class StartLossEffectChecker:
    def _in_start_codons(self, codon, annotator):
        if codon in annotator.code.startCodons:
            return True
        else:
            return False

    def get_effect(self, annotator, variant, transcript_model):
        if (transcript_model.cds[0] <= variant.position
                <= transcript_model.cds[0] + 3):
            ref = GenomicSequence(
                annotator, variant, transcript_model
            )
            ref_codons, alt_codons = ref.get_codons()

            if (self._in_start_codons(ref_codons[:3], annotator) and
                    not self._in_start_codons(alt_codons[:3], annotator)):
                ef = Effect("noStart", transcript_model)
                ef.prot_pos = 1
                ef.prot_length = 100
                return ef
