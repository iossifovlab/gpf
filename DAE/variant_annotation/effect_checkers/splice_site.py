from ..effect import Effect
from ..mutation import GenomicSequence
import logging


class SpliceSiteEffectChecker:
    def mutation_type(self, aaref, aaalt):
        if len(aaref) != len(aaalt):
            if "End" in aaalt:
                return "nonsense"
            else:
                return "missense"

        for ref, alt in zip(aaref, aaalt):
            if ref == "?" or alt == "?":
                return "coding_unknown"
            if ref != alt and alt == "End":
                return "nonsense"
            if ref != alt:
                return "missense"
        return "synonymous"

    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)

        coding_regions = transcript_model.CDS_regions()
        prev = coding_regions[0].stop

        for j in coding_regions:
            logger.debug("pos: %d checking intronic region %d-%d",
                         variant.position, prev, j.start)
            if (prev <= variant.position <= j.start):
                if (variant.position - prev < 3
                        or j.start - variant.position < 3):
                    # splice
                    worstEffect = "splice-site"
                else:
                    # intron not splice
                    worstEffect = "intron"

                ef = Effect(worstEffect, transcript_model)
                return ef
            prev = j.stop
