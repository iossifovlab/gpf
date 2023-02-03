from ..effect import EffectFactory


class StopLossEffectChecker:
    def get_effect(self, request):
        if request.is_stop_codon_affected():
            try:
                ref_aa, alt_aa = request.get_amino_acids()

                if len(ref_aa) == len(alt_aa):
                    if alt_aa[ref_aa.index("End")] == "End":
                        return

            except IndexError:
                pass
            except ValueError:
                pass

            return EffectFactory.create_effect_with_prot_pos("noEnd", request)
