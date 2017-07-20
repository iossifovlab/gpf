from .gene_codes import NuclearCode
from .effect_checkers.example import ExampleEffectChecker
from .effect_checkers.promoter import PromoterEffectChecker
from .effect_checkers.frame_shift import FrameShiftEffectChecker
from .effect_checkers.utr import UTREffectChecker
from .effect_checkers.protein_change import ProteinChangeEffectChecker
from .effect_checkers.start_loss import StartLossEffectChecker
from .effect_checkers.stop_loss import StopLossEffectChecker
from .effect_checkers.splice_site import SpliceSiteEffectChecker
from .effect_checkers.intron import IntronicEffectChecker
from effect import Effect
from .variant import Variant


class VariantAnnotator:
    Severity = {
        'tRNA:ANTICODON': 30,
        'all': 24,
        'splice-site': 23,
        'frame-shift': 22,
        'nonsense': 21,
        'no-frame-shift-newStop': 20,
        'noStart': 19,
        'noEnd': 18,
        'missense': 17,
        'no-frame-shift': 16,
        'CDS': 15,
        'synonymous': 14,
        'coding_unknown': 13,
        'regulatory': 12,
        "3'UTR": 11,
        "5'UTR": 10,
        'intron': 9,
        'non-coding': 8,
        "5'UTR-intron": 7,
        "3'UTR-intron": 6,
        "promoter": 5,
        "non-coding-intron": 4,
        'unknown': 3,
        'intergenic': 2,
        'no-mutation': 1
    }

    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.effects_checkers = [PromoterEffectChecker(),
                                 UTREffectChecker(),
                                 SpliceSiteEffectChecker(),
                                 StartLossEffectChecker(),
                                 StopLossEffectChecker(),
                                 FrameShiftEffectChecker(),

                                 ProteinChangeEffectChecker(),
                                 IntronicEffectChecker()]

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
        if len(effects) == 0:
            effects.append(Effect("intergenic"))
        return effects

    @classmethod
    def annotate_variant(cls, gm, refG, chr=None, position=None, loc=None,
                         var=None, ref=None, alt=None, length=None, seq=None,
                         typ=None, promoter_len=0):
        annotator = VariantAnnotator(refG, gm, NuclearCode(), promoter_len)
        variant = Variant(chr, position, loc, var, ref, alt, length, seq, typ)
        return annotator.annotate(variant)

    @classmethod
    def effect_description(cls, E):
        #cnvs ???

        if E[0].effect == 'unk_chr':
            return('unk_chr', 'unk_chr', 'unk_chr')

        effect_type = ""
        effect_gene = ""
        effect_details = ""

        D = {}

        for i in E:
            severity_score = cls.Severity[i.effect]
            try:
                D[severity_score].append(i)
            except:
                D[severity_score] = [i]

        set_worst_effect = False

        for key in sorted(D, key=int, reverse=True):
            if set_worst_effect is False:
                effect_type = D[key][0].effect
                set_worst_effect = True

            if effect_type == "intergenic":
                return("intergenic", "intergenic", "intergenic")

            if effect_type == "no-mutation":
                return("no-mutation", "no-mutation", "no-mutation")

            G = {}
            for i in D[key]:
                try:
                    G[i.gene].append(i)
                except:
                    G[i.gene] = [i]

            for gene in G:
                for v in G[gene]:
                    effect_details += cls.create_effect_details(v) + ";"
                effect_gene += gene + ":" + G[gene][0].effect + "|"

            effect_details = effect_details[:-1] + "|"

        return(effect_type, effect_gene[:-1], effect_details[:-1])

    @staticmethod
    def create_effect_details(e):
        if e.effect in ["intron", "5'UTR-intron", "3'UTR-intron",
                        "non-coding-intron"]:
            eff_d = str(e.which_intron) + "/" + str(e.how_many_introns)
            eff_d += "[" + str(e.dist_from_coding) + "]"
        elif (e.effect == "frame-shift" or e.effect == "no-frame-shift"
              or e.effect == "no-frame-shift-newStop"):
            eff_d = str(e.prot_pos) + "/" + str(e.prot_length)
        elif e.effect == "splice-site" or e.effect == "synonymous":
            eff_d = str(e.prot_pos) + "/" + str(e.prot_length)
        elif e.effect == "5'UTR" or e.effect == "3'UTR":
            eff_d = str(e.dist_from_coding)
        elif e.effect in ["non-coding", "unknown", "tRNA:ANTICODON"]:
            eff_d = str(e.length)
        elif e.effect == "noStart" or e.effect == "noEnd":
            eff_d = str(e.prot_length)
        elif (e.effect == "missense" or e.effect == "nonsense" or
              e.effect == "coding_unknown"):
            eff_d = str(e.prot_pos) + "/" + str(e.prot_length)
            eff_d += "(" + e.aa_change + ")"
        elif e.effect == "promoter":
            eff_d = str(e.dist_from_5utr)
        elif e.effect == "CDS" or e.effect == "all":
            eff_d = str(e.prot_length)
        elif e.effect == "no-mutation":
            eff_d = "no-mutation"
        return(eff_d)
