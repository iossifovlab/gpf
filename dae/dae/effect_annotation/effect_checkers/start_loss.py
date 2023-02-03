from ..effect import EffectFactory


class StartLossEffectChecker:
    def get_effect(self, request):
        if request.is_start_codon_affected():
            return EffectFactory.create_effect_with_prot_pos(
                "noStart", request
            )
