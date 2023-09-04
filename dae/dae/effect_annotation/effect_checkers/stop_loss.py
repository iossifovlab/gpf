import logging
from typing import Optional

from ..effect import EffectFactory
from .effect_checker import EffectChecker, AnnotationEffect, AnnotationRequest

logger = logging.getLogger(__name__)


class StopLossEffectChecker(EffectChecker):
    """Stop loss effect checker class."""

    def get_effect(
        self, request: AnnotationRequest
    ) -> Optional[AnnotationEffect]:
        last_position = request.variant.position + len(
            request.variant.reference
        )

        logger.debug(
            "position check %d <= %d-%d <= %d",
            request.transcript_model.cds[1] - 2,
            request.variant.position,
            last_position,
            request.transcript_model.cds[0],
        )

        if request.is_stop_codon_affected():
            try:
                ref_aa, alt_aa = request.get_amino_acids()

                if len(ref_aa) == len(alt_aa):
                    if alt_aa[ref_aa.index("End")] == "End":
                        return None

                logger.debug("ref aa=%s, alt aa=%s", ref_aa, alt_aa)

            except IndexError:
                pass
            except ValueError:
                pass

            return EffectFactory.create_effect_with_prot_pos("noEnd", request)

        return None
