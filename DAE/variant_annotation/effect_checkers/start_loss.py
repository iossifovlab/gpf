from ..effect import Effect
from ..mutation import GenomicSequenceFactory
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

    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)

        last_position = variant.position + len(variant.reference)

        logger.debug("position check %d <= %d-%d <= %d",
                     transcript_model.cds[0], variant.position,
                     last_position, transcript_model.cds[0] + 2)

        if (variant.position <= transcript_model.cds[0] + 2
                and transcript_model.cds[0] <= last_position):
            ref = GenomicSequenceFactory.create_genomic_sequence(
                annotator, variant, transcript_model
            )
            try:
                if transcript_model.strand == "+":
                    if not ref.find_start_codon():
                        ef = Effect("noStart", transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
                    return

                ref_codons, alt_codons = ref.get_codons()

                logger.debug("effected codons: %s->%s",
                             ref_codons[:3], alt_codons[:3])

                if transcript_model.strand == "-":
                    if (self._in_stop_codons(ref_codons[:3], annotator) and
                            not self._in_stop_codons(alt_codons[:3],
                                                     annotator)):
                        ef = Effect("noEnd", transcript_model)
                        ef.prot_pos = 1
                        ef.prot_length = 100
                        return ef
            except IndexError:
                return
