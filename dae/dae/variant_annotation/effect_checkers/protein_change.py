from ..effect import EffectFactory


class ProteinChangeEffectChecker(object):
    def mutation_type(self, aaref, aaalt):
        assert len(aaref) == len(aaalt)

        if "End" in aaalt and "End" not in aaref:
            return "nonsense"

        for ref, alt in zip(aaref, aaalt):
            if ref == "?" or alt == "?":
                return "coding_unknown"
            if ref != alt:
                return "missense"
        return "synonymous"

    def get_effect(self, request):
        coding_regions = request.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        if length != 0:
            return None

        for j in coding_regions:
            if j.start <= request.variant.position <= j.stop:
                if length == 0:
                    ref_aa, alt_aa = request.get_amino_acids()
                    return EffectFactory.create_effect_with_aa_change(
                        self.mutation_type(ref_aa, alt_aa), request
                    )
