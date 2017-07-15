from ..effect import Effect
from ..mutation import GenomicSequenceFactory
import logging


class ProteinChangeEffectChecker:
    def mutation_type(self, aaref, aaalt):
        if len(aaref) != len(aaalt):
            if "End" in aaalt:
                return "nonsense"
            else:
                return "missense"

        for ref, alt in zip(aaref, aaalt):
            if ref == "?" or alt == "?":
                return "coding_unknown"
            if ref != alt and alt == "End":
                return "nonsense"
            if ref != alt:
                return "missense"
        return "synonymous"

    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)

        coding_regions = transcript_model.CDS_regions()
        ref_length = len(variant.reference)
        alt_length = len(variant.alternate)
        length = abs(alt_length - ref_length)

        if length != 0:
            return None

        for j in coding_regions:
            if (j.start <= variant.position <= j.stop):
                if length == 0:
                    ref = GenomicSequenceFactory.create_genomic_sequence(
                        annotator, variant, transcript_model
                    )

                    ref_aa, alt_aa = ref.get_amino_acids()
                    logger.debug("ref aa=%s, alt aa=%s", ref_aa, alt_aa)

                    ef = Effect(self.mutation_type(ref_aa, alt_aa),
                                transcript_model)
                    ef.aa_change = "{}->{}".format(
                        ",".join(ref_aa),
                        ",".join(alt_aa)
                    )
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
