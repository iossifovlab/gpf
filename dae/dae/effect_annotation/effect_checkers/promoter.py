
from dae.effect_annotation.annotation_request import AnnotationRequest
from dae.effect_annotation.effect import AnnotationEffect, EffectFactory
from dae.effect_annotation.effect_checkers.effect_checker import EffectChecker
from dae.effect_annotation.variant import Variant
from dae.genomic_resources.gene_models.gene_models import TranscriptModel


class PromoterEffectChecker(EffectChecker):
    """Promoter effect checker class."""

    def create_effect(
        self, transcript_model: TranscriptModel,
    ) -> AnnotationEffect:
        return EffectFactory.create_effect_with_tm(
            "promoter", transcript_model)

    def create_positive_strand_effect(
        self, transcript_model: TranscriptModel,
        variant: Variant,
    ) -> AnnotationEffect:
        """Create a positive strand promoter effect."""
        assert variant.ref_position_last is not None
        assert variant.corrected_ref_position_last is not None

        effect = self.create_effect(transcript_model)
        effect.dist_from_5utr = (
            transcript_model.exons[0].start - variant.ref_position_last
        )
        return effect

    def create_negative_strand_effect(
        self, transcript_model: TranscriptModel, variant: Variant,
    ) -> AnnotationEffect:
        effect = self.create_effect(transcript_model)
        effect.dist_from_5utr = \
            variant.position - transcript_model.exons[-1].stop
        return effect

    def get_effect(
        self, request: AnnotationRequest,
    ) -> AnnotationEffect | None:
        if request.promoter_len == 0:
            return None

        assert request.variant.ref_position_last is not None
        assert request.variant.corrected_ref_position_last is not None

        if (
            request.variant.position < request.transcript_model.exons[0].start
            and request.transcript_model.strand == "+"
            and request.variant.ref_position_last
            >= request.transcript_model.exons[0].start
            - request.promoter_len
        ):
            return self.create_positive_strand_effect(
                request.transcript_model, request.variant,
            )

        if (
            request.variant.position > request.transcript_model.exons[-1].stop
            and request.transcript_model.strand == "-"
            and request.variant.position
            <= request.transcript_model.exons[-1].stop
            + request.promoter_len
        ):
            return self.create_negative_strand_effect(
                request.transcript_model, request.variant,
            )
        return None
