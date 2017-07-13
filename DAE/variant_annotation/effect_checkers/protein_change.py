from ..effect import Effect
import sys
from ..mutation import Mutation, MutatedGenomicSequence, TranscriptModelWrapper
from ..mutation import GenomicSequence


class ProteinChangeEffectChecker:
    def cod2aa(self, annotator, codon):
        codon = codon.upper()
        if len(codon) != 3:
            return("?")

        for i in codon:
            if i not in ['A', 'C', 'T', 'G', 'N']:
                print("Codon can only contain: A, G, C, T, N letters, \
                      this codon is: " + codon)
                sys.exit(-21)
            if i == "N":
                return("?")

        for key in annotator.code.CodonsAaKeys:
            if codon in annotator.code.CodonsAa[key]:
                return(key)

        return(None)

    def mutationType(self, aaref, aaalt):

        if aaref == aaalt and aaref != "?":
            return("synonymous")
        if aaalt == 'End':
            return("nonsense")
        if aaref == "?" or aaalt == "?":
            return("coding_unknown")

        return("missense")

    def get_effect(self, annotator, variant, transcript_model):
        coding_regions = transcript_model.CDS_regions()
        ref_length = len(variant.reference)
        alt_length = len(variant.alternate)
        length = abs(alt_length - ref_length)

        if length != 0:
            return None

        mutation = Mutation(variant.position, variant.reference,
                            variant.alternate)

        ref_sequence = GenomicSequence(annotator.reference_genome)
        alt_sequence = MutatedGenomicSequence(annotator.reference_genome,
                                              mutation)

        ref_model = TranscriptModelWrapper(transcript_model,
                                           ref_sequence)
        alt_model = TranscriptModelWrapper(transcript_model,
                                           alt_sequence)

        for j in coding_regions:
            if (variant.position <= j.stop or variant.position >= j.start):
                if length == 0:
                    codon = ref_model.get_codon_for_pos(
                        transcript_model.chr, variant.position
                    )
                    mutated_codon = alt_model.get_codon_for_pos(
                        transcript_model.chr, variant.position
                    )
                    refAA = self.cod2aa(annotator, codon)
                    altAA = self.cod2aa(annotator, mutated_codon)

                    ef = Effect(self.mutationType(refAA, altAA),
                                transcript_model)
                    ef.aa_change = refAA + "->" + altAA
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
