import logging
from typing import Optional

from ..effect import EffectFactory
from .effect_checker import EffectChecker, AnnotationEffect, AnnotationRequest


class UTREffectChecker(EffectChecker):
    """UTR effect checker class."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def create_utr_effect(
        self, request: AnnotationRequest, strand: str
    ) -> AnnotationEffect:
        """Create an UTR annotation effect."""
        if request.transcript_model.strand == strand:
            effect_name = "5'UTR"
        else:
            effect_name = "3'UTR"

        effect = EffectFactory.create_effect_with_prot_length(
            effect_name, request
        )
        self.logger.debug(
            "pos=%d cds end=%d",
            request.variant.ref_position_last - 1,
            request.transcript_model.cds[0],
        )

        if strand == "+":
            effect.dist_from_coding = request.get_exonic_distance(
                request.variant.corrected_ref_position_last,
                request.transcript_model.cds[0],
            )
        else:
            effect.dist_from_coding = request.get_exonic_distance(
                request.transcript_model.cds[1], request.variant.position
            )
        return effect

    def create_effect(
        self, request: AnnotationRequest, strand: str
    ) -> Optional[AnnotationEffect]:
        """Create UTR effect."""
        coding_regions = request.transcript_model.exons
        last_position = request.variant.corrected_ref_position_last
        prev = None

        for i, j in enumerate(coding_regions):
            if request.variant.position <= j.stop and j.start <= last_position:
                return self.create_utr_effect(request, strand)
            if (
                prev is not None
                and prev <= request.variant.position
                and last_position < j.start
            ):
                if request.transcript_model.strand == strand:
                    effect_name = "5'UTR-intron"
                else:
                    effect_name = "3'UTR-intron"
                return EffectFactory.create_intronic_non_coding_effect(
                    effect_name, request, prev, j.start, i
                )
            prev = j.stop
        return None

    def check_stop_codon(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        """Check for stop codon."""
        if not request.has_utr3_region():
            return None

        try:
            ref_aa, alt_aa = request.get_amino_acids()
            if "End" not in ref_aa:
                return None

            ref_index = ref_aa.index("End")
            alt_index = alt_aa.index("End")

            if ref_index == alt_index:
                effect = EffectFactory.create_effect_with_prot_length(
                    "3'UTR", request
                )
                effect.dist_from_coding = 0
                return effect
        except ValueError:
            pass
        except IndexError:
            pass
        return None

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        if request.is_stop_codon_affected():
            return self.check_stop_codon(request)

        self.logger.debug(
            "utr check: %d<%d or %d>%d exons:%d-%d",
            request.variant.position,
            request.transcript_model.cds[0],
            request.variant.position,
            request.transcript_model.cds[1],
            request.transcript_model.exons[0].start,
            request.transcript_model.exons[-1].stop,
        )

        if request.variant.position < request.transcript_model.cds[0]:
            return self.create_effect(request, "+")

        if request.variant.position > request.transcript_model.cds[1]:
            return self.create_effect(request, "-")

        return None
