from __future__ import annotations

import logging

from dae.annotation.annotatable import Annotatable
from dae.genomic_resources.gene_models import GeneModels, TranscriptModel
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.utils.regions import Region

from .annotation_request import (
    AnnotationRequest,
    NegativeStrandAnnotationRequest,
    PositiveStrandAnnotationRequest,
)
from .effect import AnnotationEffect, EffectFactory
from .effect_checkers.coding import CodingEffectChecker
from .effect_checkers.effect_checker import EffectChecker
from .effect_checkers.frame_shift import FrameShiftEffectChecker
from .effect_checkers.intron import IntronicEffectChecker
from .effect_checkers.promoter import PromoterEffectChecker
from .effect_checkers.protein_change import ProteinChangeEffectChecker
from .effect_checkers.splice_site import SpliceSiteEffectChecker
from .effect_checkers.start_loss import StartLossEffectChecker
from .effect_checkers.stop_loss import StopLossEffectChecker
from .effect_checkers.utr import UTREffectChecker
from .gene_codes import NuclearCode
from .variant import Variant

logger = logging.getLogger(__name__)


class AnnotationRequestFactory:
    """Factory for annotation requests."""

    @staticmethod
    def create_annotation_request(
            annotator: EffectAnnotator,
            variant: Variant,
            transcript_model: TranscriptModel) -> AnnotationRequest:
        """Create an annotation request."""
        assert annotator.reference_genome is not None
        if transcript_model.strand == "+":
            return PositiveStrandAnnotationRequest(
                annotator.reference_genome, annotator.code,
                annotator.promoter_len,
                variant, transcript_model,
            )
        return NegativeStrandAnnotationRequest(
            annotator.reference_genome, annotator.code,
            annotator.promoter_len,
            variant, transcript_model,
        )


class EffectAnnotator:
    """Predicts variant effect."""

    def __init__(
            self, reference_genome: ReferenceGenome, gene_models: GeneModels,
            code: NuclearCode | None = None,
            promoter_len: int = 0):

        if code is None:
            code = NuclearCode()
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.effects_checkers: list[EffectChecker] = [
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

    def close(self) -> None:
        self.reference_genome = None  # type: ignore
        self.gene_models = None  # type: ignore

    def get_effect_for_transcript(
        self, variant: Variant, transcript_model: TranscriptModel,
    ) -> AnnotationEffect | None:
        """Calculate effect for a given transcript."""
        request = AnnotationRequestFactory.create_annotation_request(
            self, variant, transcript_model,
        )

        for effect_checker in self.effects_checkers:
            effect = effect_checker.get_effect(request)
            if effect is not None:
                return effect
        return None

    def annotate_cnv(
        self, chrom: str, pos_start: int, pos_end: int,
        variant_type: Annotatable.Type,
    ) -> list[AnnotationEffect]:
        """Annotate a CNV variant."""
        assert self.gene_models is not None
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
        self, chrom: str, pos_start: int, pos_end: int,
        effect_type: str = "unknown",
    ) -> list[AnnotationEffect]:
        """Annotate a region or position."""
        assert self.gene_models is not None
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

    def annotate(self, variant: Variant) -> list[AnnotationEffect]:
        """Annotate effects for a variant."""
        assert self.gene_models is not None

        if self.gene_models.utr_models is None:
            raise ValueError("bad gene models")
        if variant.variant_type in {
                Annotatable.Type.LARGE_DUPLICATION,
                Annotatable.Type.LARGE_DELETION}:
            assert variant.length is not None
            return self.annotate_cnv(
                variant.chromosome,
                variant.position,
                variant.position + variant.length,
                variant.variant_type)

        effects = []
        if variant.chromosome not in self.gene_models.utr_models:
            effects.append(EffectFactory.create_effect("intergenic"))
            return effects

        assert variant.ref_position_last is not None
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
        self, *,
        chrom: str | None = None,
        pos: int | None = None,
        location: str | None = None,
        variant: str | None = None,
        ref: str | None = None,
        alt: str | None = None,
        length: int | None = None,
        seq: str | None = None,
        variant_type: Annotatable.Type | None = None,
    ) -> list[AnnotationEffect]:
        """Annotate effects for a variant."""
        if variant in {"CNV+", "CNV-"}:
            if variant == "CNV+":
                cnv_type = Annotatable.Type.LARGE_DUPLICATION
            elif variant == "CNV-":
                cnv_type = Annotatable.Type.LARGE_DELETION
            else:
                raise ValueError(
                    f"Unexpected CNV variant type: {variant_type}")

            if chrom is not None and pos is not None and length is not None:
                return self.annotate_cnv(
                    chrom, pos, pos + length,
                    cnv_type,
                )
            if location is not None:
                chrom, beg_end = location.split(":")
                pos_beg, pos_end = beg_end.split("-")
                return self.annotate_cnv(
                    chrom, int(pos_beg), int(pos_end),
                    cnv_type)
            raise ValueError("unexpected CNV variant description")
        return self.annotate(Variant(
            chrom, pos,
            loc=location,
            var=variant,
            ref=ref,
            alt=alt,
            length=length,
            seq=seq,
            variant_type=variant_type))

    def annotate_allele(
        self, *,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        length: int | None = None,
        seq: str | None = None,
        variant_type: Annotatable.Type | None = None,
    ) -> list[AnnotationEffect]:
        """Annotate effects for a variant."""
        variant = Variant(
            chrom, pos,
            ref=ref,
            alt=alt,
            length=length,
            seq=seq,
            variant_type=variant_type,
        )
        return self.annotate(variant)

    @staticmethod
    def annotate_variant(
        gm: GeneModels,
        reference_genome: ReferenceGenome, *,
        chrom: str | None = None,
        pos: int | None = None,
        location: str | None = None,
        variant: str | None = None,
        ref: str | None = None,
        alt: str | None = None,
        length: int | None = None,
        seq: str | None = None,
        variant_type: Annotatable.Type | None = None,
        promoter_len: int = 0,
    ) -> list[AnnotationEffect]:
        """Build effect annotator and annotate a variant."""
        # pylint: disable=too-many-arguments
        annotator = EffectAnnotator(
            reference_genome, gm, promoter_len=promoter_len)
        effects = annotator.do_annotate_variant(
            chrom=chrom, pos=pos, location=location,
            variant=variant, ref=ref, alt=alt, length=length,
            seq=seq, variant_type=variant_type,
        )
        desc = AnnotationEffect.effects_description(effects)
        logger.debug("effect: %s", desc)

        return effects
