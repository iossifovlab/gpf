from ..effect import EffectFactory


class FrameShiftEffectChecker:
    def create_effect(self, request, change_length):
        if change_length > 0:
            if change_length % 3 == 0:
                if self.check_if_new_stop(request):
                    effect_name = "no-frame-shift-newStop"
                else:
                    effect_name = "no-frame-shift"
                effect = EffectFactory.create_effect_with_aa_change(
                    effect_name, request
                )
            else:
                effect_name = "frame-shift"
                effect = EffectFactory.create_effect_with_aa_change(
                    effect_name, request
                )
            return effect
        return None

    def check_if_new_stop(self, request):
        ref_aa, alt_aa = request.get_amino_acids()
        for aa in ref_aa:
            if aa == "End":
                return False
        for aa in alt_aa:
            if aa == "End":
                return True
        return False

    def check_stop_codon(self, request):
        try:
            ref_aa, alt_aa = request.get_amino_acids()
            if "End" not in ref_aa:
                return None

            ref_index = ref_aa.index("End")
            alt_index = alt_aa.index("End")

            if ref_index != alt_index:
                diff = abs(ref_index - alt_index) * 3
                return self.create_effect(request, diff)
        except ValueError:
            pass
        except IndexError:
            pass
        return None

    def get_effect(self, request):
        coding_regions = request.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        if request.is_stop_codon_affected():
            return self.check_stop_codon(request)

        for j in coding_regions:
            start = j.start
            stop = j.stop

            if len(request.variant.reference) == 0:
                stop += 1

            if start <= request.variant.position <= stop:
                return self.create_effect(request, length)
