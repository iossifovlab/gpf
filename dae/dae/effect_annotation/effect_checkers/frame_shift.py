import logging
from typing import Optional

from ..effect import EffectFactory, AnnotationEffect
from ..annotation_request import AnnotationRequest
from .effect_checker import EffectChecker


class FrameShiftEffectChecker(EffectChecker):
    """Frame shift effect checker class."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def create_effect(
        self, request: AnnotationRequest, change_length: int
    ) -> Optional[AnnotationEffect]:
        """Create frame-shift annotation effect."""
        if change_length > 0:
            if change_length % 3 == 0:
                if self.check_if_new_stop(request):
                    effect_name = "no-frame-shift-newStop"
                else:
                    effect_name = "no-frame-shift"
                effect = EffectFactory.create_effect_with_aa_change(
                    effect_name, request
                )
            else:
                effect_name = "frame-shift"
                effect = EffectFactory.create_effect_with_aa_change(
                    effect_name, request
                )
            return effect
        return None

    def check_if_new_stop(self, request: AnnotationRequest) -> bool:
        """Check for a new stop codon."""
        ref_aa, alt_aa = request.get_amino_acids()
        for aa in ref_aa:
            if aa == "End":
                return False
        for aa in alt_aa:
            if aa == "End":
                return True
        return False

    def check_stop_codon(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        """Check for stop codon."""
        try:
            ref_aa, alt_aa = request.get_amino_acids()
            if "End" not in ref_aa:
                return None

            ref_index = ref_aa.index("End")
            alt_index = alt_aa.index("End")

            if ref_index != alt_index:
                diff = abs(ref_index - alt_index) * 3
                return self.create_effect(request, diff)
        except ValueError:
            pass
        except IndexError:
            pass
        return None

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        coding_regions = request.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        if request.is_stop_codon_affected():
            return self.check_stop_codon(request)

        for j in coding_regions:
            start = j.start
            stop = j.stop

            if len(request.variant.reference) == 0:
                stop += 1

            self.logger.debug(
                "frameshift %d<=%d<=%d cds:%d-%d exon:%d-%d",
                start,
                request.variant.position,
                stop,
                request.transcript_model.cds[0],
                request.transcript_model.cds[1],
                j.start,
                j.stop,
            )

            if start <= request.variant.position <= stop:
                self.logger.debug(
                    "fs detected %d<=%d-%d<=%d cds:%d-%d",
                    start,
                    request.variant.position,
                    request.variant.ref_position_last,
                    stop,
                    request.transcript_model.cds[0],
                    request.transcript_model.cds[1],
                )

                return self.create_effect(request, length)
        return None
