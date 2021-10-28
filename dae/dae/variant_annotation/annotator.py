from dae.utils.regions import Region
from dae.variants.core import Allele

from .gene_codes import NuclearCode
from .effect_checkers.coding import CodingEffectChecker
from .effect_checkers.promoter import PromoterEffectChecker
from .effect_checkers.frame_shift import FrameShiftEffectChecker
from .effect_checkers.utr import UTREffectChecker
from .effect_checkers.protein_change import ProteinChangeEffectChecker
from .effect_checkers.start_loss import StartLossEffectChecker
from .effect_checkers.stop_loss import StopLossEffectChecker
from .effect_checkers.splice_site import SpliceSiteEffectChecker
from .effect_checkers.intron import IntronicEffectChecker
from .effect import EffectFactory
from .variant import Variant
from .annotation_request import AnnotationRequestFactory
import logging


class VariantAnnotator(object):
    Severity = {
        "CNV+": 35,
        "CNV-": 35,
        "tRNA:ANTICODON": 30,
        "all": 24,
        "splice-site": 23,
        "frame-shift": 22,
        "nonsense": 21,
        "no-frame-shift-newStop": 20,
        "noStart": 19,
        "noEnd": 18,
        "missense": 17,
        "no-frame-shift": 16,
        "CDS": 15,
        "synonymous": 14,
        "coding_unknown": 13,
        "regulatory": 12,
        "3'UTR": 11,
        "5'UTR": 10,
        "intron": 9,
        "non-coding": 8,
        "5'UTR-intron": 7,
        "3'UTR-intron": 6,
        "promoter": 5,
        "non-coding-intron": 4,
        "unknown": 3,
        "intergenic": 2,
        "no-mutation": 1,
    }

    def __init__(
            self, reference_genome, gene_models, code=NuclearCode(),
            promoter_len=0):

        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.effects_checkers = [
            PromoterEffectChecker(),
            CodingEffectChecker(),
            SpliceSiteEffectChecker(),
            StartLossEffectChecker(),
            StopLossEffectChecker(),
            FrameShiftEffectChecker(),
            ProteinChangeEffectChecker(),
            UTREffectChecker(),
            IntronicEffectChecker(),
        ]

    def get_effect_for_transcript(self, variant, transcript_model):
        request = AnnotationRequestFactory.create_annotation_request(
            self, variant, transcript_model
        )

        for effect_checker in self.effects_checkers:
            effect = effect_checker.get_effect(request)
            if effect is not None:
                return effect
        return None

    def _do_annotate_cnv(self, variant):
        assert Allele.Type.is_cnv(variant.variant_type)
        if variant.variant_type & Allele.Type.large_duplication:
            effect_type = "CNV+"
        elif variant.variant_type & Allele.Type.large_deletion:
            effect_type = "CNV-"
        else:
            raise ValueError(
                f"unexpected variant type: {variant.variant_type}")
        assert effect_type is not None

        effects = []
        cnv_region = Region(
            variant.chromosome,
            variant.position,
            variant.position + variant.length)

        for (start, stop), tms in \
                self.gene_models.utr_models[variant.chromosome].items():
            if cnv_region.intersection(
                    Region(variant.chromosome, start, stop)):
                for tm in tms:
                    effects.append(
                        EffectFactory.create_effect_with_tm(effect_type, tm))

        if len(effects) == 0:
            effects.append(EffectFactory.create_effect(effect_type))

        return effects

    def annotate(self, variant):
        logger = logging.getLogger(__name__)
        if Allele.Type.is_cnv(variant.variant_type):
            return self._do_annotate_cnv(variant)

        effects = []
        if variant.chromosome not in self.gene_models.utr_models:
            effects.append(EffectFactory.create_effect("intergenic"))
            return effects

        for key in self.gene_models.utr_models[variant.chromosome]:
            if (
                variant.position <= key[1] + self.promoter_len
                and variant.ref_position_last >= key[0] - self.promoter_len
            ):
                for tm in self.gene_models.utr_models[variant.chromosome][key]:
                    logger.debug(
                        "========: %s-%s :====================",
                        tm.gene,
                        tm.tr_id,
                    )
                    effect = self.get_effect_for_transcript(variant, tm)

                    logger.debug("")
                    logger.debug("Result: %s", effect)
                    logger.debug("")
                    if effect is not None:
                        effects.append(effect)

        if len(effects) == 0:
            effects.append(EffectFactory.create_effect("intergenic"))
        return effects

    def do_annotate_variant(
            self,
            chrom=None,
            position=None,
            loc=None,
            var=None,
            ref=None,
            alt=None,
            length=None,
            seq=None,
            variant_type=None):

        variant = Variant(
            chrom, position, loc, var, ref, alt, length, seq, variant_type
        )
        return self.annotate(variant)

    @classmethod
    def annotate_variant(
            cls,
            gm,
            refG,
            chrom=None,
            position=None,
            loc=None,
            var=None,
            ref=None,
            alt=None,
            length=None,
            seq=None,
            variant_type=None,
            promoter_len=0):

        annotator = VariantAnnotator(refG, gm, promoter_len=promoter_len)
        effects = annotator.do_annotate_variant(
            chrom, position, loc, var, ref, alt, length, seq, variant_type
        )
        desc = VariantAnnotator.effect_description(effects)

        logger = logging.getLogger(__name__)
        logger.debug("effect: %s", desc)

        return effects

    @classmethod
    def effect_description1(cls, E):
        if E[0].effect == "unk_chr":
            return ("unk_chr", "unk_chr", "unk_chr")

        effect_type = []
        effect_gene = []
        effect_details = []

        D = {}
        [D.setdefault(cls.Severity[i.effect], []).append(i) for i in E]

        set_worst_effect = False

        for key in sorted(D, key=int, reverse=True):
            if set_worst_effect is False:
                effect_type = [D[key][0].effect]
                set_worst_effect = True

            if effect_type == "intergenic":
                return ("intergenic", "intergenic", "intergenic")

            if effect_type == "no-mutation":
                return ("no-mutation", "no-mutation", "no-mutation")

            G = {}
            [G.setdefault(i.gene, []).append(i) for i in D[key]]

            for gene in G:
                for v in G[gene]:
                    effect_details.append(v.create_effect_details())
                if gene is not None:
                    gene_str = str(gene)
                else:
                    gene_str = ""
                effect_gene.append(gene_str + ":" + G[gene][0].effect)

        return (effect_type, effect_gene, effect_details)

    @classmethod
    def effect_description(cls, E):
        effect_type, effect_gene, effect_details = cls.effect_simplify(E)
        if isinstance(effect_gene, list):
            effect_gene = "|".join([":".join(eg) for eg in effect_gene])
        if isinstance(effect_details, list):
            effect_details = "|".join(
                [";".join([e for e in ed]) for ed in effect_details]
            )
        return (effect_type, effect_gene, effect_details)

    @classmethod
    def effect_simplify(cls, E):
        if E[0].effect == "unk_chr":
            return ("unk_chr", "unk_chr", "unk_chr")

        effect_type = ""
        effect_gene = []
        effect_details = []

        D = {}
        [D.setdefault(cls.Severity[i.effect], []).append(i) for i in E]

        set_worst_effect = False

        for key in sorted(D, key=int, reverse=True):
            if set_worst_effect is False:
                effect_type = D[key][0].effect
                set_worst_effect = True

            if effect_type == "intergenic":
                return (
                    "intergenic",
                    [("intergenic", "intergenic")],
                    "intergenic",
                )

            if effect_type == "no-mutation":
                return ("no-mutation", "no-mutation", "no-mutation")

            G = {}
            [G.setdefault(i.gene, []).append(i) for i in D[key]]

            effect_detail = []
            for gene in G:
                for v in G[gene]:
                    effect_detail.append(v.create_effect_details())
                effect_gene.append((gene, G[gene][0].effect))

            effect_details.append(effect_detail)

        return (effect_type, effect_gene, effect_details)
