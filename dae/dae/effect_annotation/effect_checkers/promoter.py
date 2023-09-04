from typing import Optional

from dae.genomic_resources.gene_models import TranscriptModel

from ..effect import EffectFactory
from ..variant import Variant

from .effect_checker import EffectChecker, AnnotationEffect, AnnotationRequest


class PromoterEffectChecker(EffectChecker):
    """Promoter effect checker class."""

    def create_effect(
        self, transcript_model: TranscriptModel
    ) -> AnnotationEffect:
        return EffectFactory.create_effect_with_tm(
            "promoter", transcript_model)

    def create_positive_strand_effect(
        self, transcript_model: TranscriptModel,
        variant: Variant
    ) -> AnnotationEffect:
        """Create a positive strand promoter effect."""
        effect = self.create_effect(transcript_model)
        effect.dist_from_5utr = (
            transcript_model.exons[0].start - variant.ref_position_last
        )
        return effect

    def create_negative_strand_effect(
        self, transcript_model: TranscriptModel, variant: Variant
    ) -> AnnotationEffect:
        effect = self.create_effect(transcript_model)
        effect.dist_from_5utr = \
            variant.position - transcript_model.exons[-1].stop
        return effect

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        if request.annotator.promoter_len == 0:
            return None

        if (
            request.variant.position < request.transcript_model.exons[0].start
            and request.transcript_model.strand == "+"
            and request.variant.ref_position_last
            >= request.transcript_model.exons[0].start
            - request.annotator.promoter_len
        ):
            return self.create_positive_strand_effect(
                request.transcript_model, request.variant
            )

        if (
            request.variant.position > request.transcript_model.exons[-1].stop
            and request.transcript_model.strand == "-"
            and request.variant.position
            <= request.transcript_model.exons[-1].stop
            + request.annotator.promoter_len
        ):
            return self.create_negative_strand_effect(
                request.transcript_model, request.variant
            )
        return None
