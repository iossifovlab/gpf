from .gene_codes import NuclearCode
from .effect_checkers.example import ExampleEffectChecker
from .effect_checkers.promoter import PromoterEffectChecker


class VariantAnnotator:
    def __init__(self, reference_genome, gene_models, code):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = 10
        self.effects_checkers = [PromoterEffectChecker(),
                                 ExampleEffectChecker()]

    def get_effect_for_transcript(self, variant, transcript_model):
        for effect_checker in self.effects_checkers:
            effect = effect_checker.get_effect(self, variant, transcript_model)
            if effect is not None:
                return effect
        return None

    def annotate(self, variant):
        effects = []
        for key in self.gene_models._utrModels[variant.chromosome]:
            if (variant.position <= key[1] + self.promoter_len
                    and variant.position_last >= key[0] - self.promoter_len):
                for tm in self.gene_models._utrModels[variant.chromosome][key]:
                    effect = self.get_effect_for_transcript(variant, tm)
                    if effect is not None:
                        effects.append(effect)
        return effects


class Variant:
    def __init__(self, chromosome, position, reference, alternate):
        self.chromosome = chromosome
        self.position = position
        self.position_last = position
        self.reference = reference
        self.alternate = alternate


def annotate_variant(gm, refG, chr=None, position=None, loc=None,
                     var=None, ref=None, alt=None, length=None, seq=None,
                     typ=None, promoter_len=0):
    annotator = VariantAnnotator(refG, gm, NuclearCode())
    variant = Variant(chr, position, ref, alt)
    return annotator.annotate(variant)
