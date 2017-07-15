from ..effect import Effect
import logging


class SpliceSiteEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)

        coding_regions = transcript_model.CDS_regions()
        prev = coding_regions[0].stop

        length = abs(len(variant.reference) - len(variant.alternate))
        last_position = variant.position + length

        for j in coding_regions:
            logger.debug("pos: %d-%d checking intronic region %d-%d",
                         variant.position, last_position, prev, j.start)

            if (variant.position <= prev + self.splice_site_length
                    and prev < last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, transcript_model)
                return ef

            if (variant.position < j.start
                    and j.start - self.splice_site_length <= last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, transcript_model)
                return ef
            prev = j.stop
