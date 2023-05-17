import logging

from typing import List

from dae.utils.regions import Region
from dae.annotation.annotatable import Annotatable
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome

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
from .effect import EffectFactory, AnnotationEffect
from .variant import Variant
from .annotation_request import AnnotationRequestFactory


logger = logging.getLogger(__name__)


class EffectAnnotator:
    """Predicts variant effect."""

    def __init__(
            self, reference_genome: ReferenceGenome, gene_models: GeneModels,
            code=NuclearCode(),
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
        """Calculate effect for a given transcript."""
        request = AnnotationRequestFactory.create_annotation_request(
            self, variant, transcript_model
        )

        for effect_checker in self.effects_checkers:
            effect = effect_checker.get_effect(request)  # type: ignore
            if effect is not None:
                return effect
        return None

    def annotate_cnv(
        self, chrom, pos_start, pos_end, variant_type
    ) -> List[AnnotationEffect]:
        """Annotate a CNV variant."""
        if self.gene_models.utr_models is None:
            raise ValueError("bad gene models")

        if variant_type == Annotatable.Type.LARGE_DUPLICATION:
            effect_type = "CNV+"
        elif variant_type == Annotatable.Type.LARGE_DELETION:
            effect_type = "CNV-"
        else:
            raise ValueError(
                f"unexpected variant type: {variant_type}")
        assert effect_type is not None

        return self.annotate_region(
            chrom, pos_start, pos_end, effect_type=effect_type)

    def annotate_region(
            self, chrom, pos_start, pos_end, effect_type="unknown"):
        """Annotate a region or position."""
        if self.gene_models.utr_models is None:
            raise ValueError("bad gene models")
        region = Region(chrom, pos_start, pos_end)
        effects = []
        length = pos_end - pos_start + 1
        for (start, stop), tms in \
                self.gene_models.utr_models[chrom].items():
            if region.intersection(
                    Region(chrom, start, stop)):
                for transcript_model in tms:
                    effect = EffectFactory.create_effect_with_tm(
                        effect_type, transcript_model)
                    effect.length = length
                    effects.append(effect)

        if len(effects) == 0:
            effect = EffectFactory.create_effect(effect_type)
            effect.length = pos_end - pos_start + 1
            effects.append(effect)

        return effects

    def annotate(self, variant) -> List[AnnotationEffect]:
        """Annotate effects for a variant."""
        if self.gene_models.utr_models is None:
            raise ValueError("bad gene models")
        if variant.variant_type in {
                Annotatable.Type.LARGE_DUPLICATION,
                Annotatable.Type.LARGE_DELETION}:
            return self.annotate_cnv(
                variant.chromosome,
                variant.position,
                variant.position + variant.length,
                variant.variant_type)

        effects = []
        if variant.chromosome not in self.gene_models.utr_models:
            effects.append(EffectFactory.create_effect("intergenic"))
            return effects

        for key in self.gene_models.utr_models[variant.chromosome]:
            if (
                variant.position <= key[1] + self.promoter_len
                and variant.ref_position_last >= key[0] - self.promoter_len
            ):
                for transcript_model in self.gene_models\
                        .utr_models[variant.chromosome][key]:
                    effect = self.get_effect_for_transcript(
                        variant, transcript_model)

                    if effect is not None:
                        effects.append(effect)

        if len(effects) == 0:
            effects.append(EffectFactory.create_effect("intergenic"))
        return effects

    def do_annotate_variant(
            self,
            chrom=None,
            pos=None,
            location=None,
            variant=None,
            ref=None,
            alt=None,
            length=None,
            seq=None,
            variant_type=None):
        """Annotate effects for a variant."""
        variant = Variant(
            chrom, pos, location, variant, ref, alt, length, seq, variant_type
        )
        return self.annotate(variant)

    def annotate_allele(
            self,
            chrom,
            pos,
            ref,
            alt,
            length=None,
            seq=None,
            variant_type=None):
        """Annotate effects for a variant."""
        variant = Variant(
            chrom, pos, None, None, ref, alt, length, seq, variant_type
        )
        return self.annotate(variant)

    @staticmethod
    def annotate_variant(
            gm,
            reference_genome,
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
        """Build effect annotator and annotate a variant."""
        # pylint: disable=too-many-arguments
        annotator = EffectAnnotator(
            reference_genome, gm, promoter_len=promoter_len)
        effects = annotator.do_annotate_variant(
            chrom, position, loc, var, ref, alt, length, seq, variant_type
        )
        desc = AnnotationEffect.effects_description(effects)
        logger.debug("effect: %s", desc)

        return effects

    # @classmethod
    # def effect_description1(cls, E):
    #     if E[0].effect == "unk_chr":
    #         return ("unk_chr", "unk_chr", "unk_chr")

    #     effect_type = []
    #     effect_gene = []
    #     effect_details = []

    #     D = {}
    #     [D.setdefault(
    #         AnnotationEffect.Severity[i.effect], []).append(i) for i in E]

    #     set_worst_effect = False

    #     for key in sorted(D, key=int, reverse=True):
    #         if set_worst_effect is False:
    #             effect_type = [D[key][0].effect]
    #             set_worst_effect = True

    #         if effect_type == "intergenic":
    #             return ("intergenic", "intergenic", "intergenic")

    #         if effect_type == "no-mutation":
    #             return ("no-mutation", "no-mutation", "no-mutation")

    #         G = {}
    #         [G.setdefault(i.gene, []).append(i) for i in D[key]]

    #         for gene in G:
    #             for v in G[gene]:
    #                 effect_details.append(v.create_effect_details())
    #             if gene is not None:
    #                 gene_str = str(gene)
    #             else:
    #                 gene_str = ""
    #             effect_gene.append(gene_str + ":" + G[gene][0].effect)

    #     return (effect_type, effect_gene, effect_details)

    # @classmethod
    # def effect_description(cls, E):
    #     effect_type, effect_gene, effect_details = cls.effect_simplify(E)
    #     if isinstance(effect_gene, list):
    #         effect_gene = "|".join([":".join(eg) for eg in effect_gene])
    #     if isinstance(effect_details, list):
    #         effect_details = "|".join(
    #             [";".join([e for e in ed]) for ed in effect_details]
    #         )
    #     return (effect_type, effect_gene, effect_details)

    # @classmethod
    # def effect_simplify(cls, E):
    #     if E[0].effect == "unk_chr":
    #         return ("unk_chr", "unk_chr", "unk_chr")

    #     effect_type = ""
    #     effect_gene = []
    #     effect_details = []

    #     D = {}
    #     [D.setdefault(AnnotationEffect.Severity[i.effect], []).append(i)
    #      for i in E]

    #     set_worst_effect = False

    #     for key in sorted(D, key=int, reverse=True):
    #         if set_worst_effect is False:
    #             effect_type = D[key][0].effect
    #             set_worst_effect = True

    #         if effect_type == "intergenic":
    #             return (
    #                 "intergenic",
    #                 [("intergenic", "intergenic")],
    #                 "intergenic",
    #             )

    #         if effect_type == "no-mutation":
    #             return ("no-mutation", "no-mutation", "no-mutation")

    #         G = {}
    #         [G.setdefault(i.gene, []).append(i) for i in D[key]]

    #         effect_detail = []
    #         for gene in G:
    #             for v in G[gene]:
    #                 effect_detail.append(v.create_effect_details())
    #             effect_gene.append((gene, G[gene][0].effect))

    #         effect_details.append(effect_detail)

    #     return (effect_type, effect_gene, effect_details)
