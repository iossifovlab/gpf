from .gene_codes import NuclearCode
from .effect_checkers.example import ExampleEffectChecker
from .effect_checkers.promoter import PromoterEffectChecker
from .effect_checkers.frame_shift import FrameShiftEffectChecker
import re


class Variant:
    def __init__(self, chr=None, position=None, loc=None, var=None, ref=None,
                 alt=None, length=None, seq=None, typ=None):
        self.set_position(chr, position, loc)
        self.set_ref_alt(var, ref, alt, length, seq, typ)

        self.position_last = self.position

    def set_position(self, chromosome, position, loc):
        if position is not None:
            assert(chromosome is not None)
            assert(loc is None)
            self.chromosome = chromosome
            self.position = position

        if loc is not None:
            assert(chromosome is None)
            assert(position is None)
            loc_arr = loc.split(":")
            self.chromosome = loc_arr[0]
            self.position = int(loc_arr[1])

        assert(self.chromosome is not None)
        assert(self.position is not None)

    def set_ref_alt(self, var, ref, alt, length, seq, typ):
        if ref is not None:
            assert(alt is not None)
            assert(var is None)
            assert(length is None)
            assert(seq is None)
            assert(typ is None)
            self.reference = ref
            self.alternate = alt

        if var is not None:
            assert(ref is None)
            assert(alt is None)
            assert(length is None)
            assert(seq is None)
            assert(typ is None)
            self.set_ref_alt_from_variant(var)

        assert(self.reference is not None)
        assert(self.alternate is not None)

    def set_ref_alt_from_variant(self, var):
        if var.startswith("complex"):
            a = re.match('.*\((.*)->(.*)\)', var)
            self.reference = a.group(1).upper()
            self.alternate = a.group(2).upper()
            return

        t = var[0].upper()
        if t == "S":
            a = re.match('.*\((.*)->(.*)\)', var)
            self.reference = a.group(1).upper()
            self.alternate = a.group(2).upper()
            return

        if t == "D":
            a = re.match('.*\((.*)\)', var)
            self.reference = "0" * int(a.group(1))
            self.alternate = ""
            return

        if t == "I":
            a = re.match('.*\((.*)\)', var)
            self.reference = ""
            self.alternate = re.sub('[0-9]+', '', a.group(1).upper())
            return

        raise Exception("Unknown variant!: " + var)


class VariantAnnotator:
    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.effects_checkers = [PromoterEffectChecker(),
                                 FrameShiftEffectChecker()]

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

    @classmethod
    def annotate_variant(cls, gm, refG, chr=None, position=None, loc=None,
                         var=None, ref=None, alt=None, length=None, seq=None,
                         typ=None, promoter_len=0):
        annotator = VariantAnnotator(refG, gm, NuclearCode(), promoter_len)
        variant = Variant(chr, position, loc, var, ref, alt, length, seq, typ)
        return annotator.annotate(variant)
