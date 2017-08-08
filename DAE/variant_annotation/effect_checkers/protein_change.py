from ..effect import EffectFactory
import logging


class ProteinChangeEffectChecker:
    def mutation_type(self, aaref, aaalt):
        if "End" in aaalt and "End" not in aaref:
            return "nonsense"

        if len(aaref) != len(aaalt):
            return "missense"

        for ref, alt in zip(aaref, aaalt):
            if ref == "?" or alt == "?":
                return "coding_unknown"
            if ref != alt:
                return "missense"
        return "synonymous"

    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        coding_regions = request.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        if length != 0:
            return None

        for j in coding_regions:
            if (j.start <= request.variant.position <= j.stop):
                if length == 0:
                    ref_aa, alt_aa = request.get_amino_acids()
                    return EffectFactory.create_effect_with_aa_change(
                        self.mutation_type(ref_aa, alt_aa), request
                    )
