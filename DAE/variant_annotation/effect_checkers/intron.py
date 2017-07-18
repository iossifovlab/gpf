from ..effect import Effect
import logging


class IntronicEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)

        coding_regions = transcript_model.CDS_regions()
        prev = coding_regions[0].stop

        last_position = variant.position + len(variant.reference)

        for j in coding_regions:
            logger.debug("pos: %d-%d checking intronic region %d-%d",
                         variant.position, last_position, prev, j.start)
            if (prev <= variant.position
                    and last_position < j.start):
                worstEffect = "intron"
                ef = Effect(worstEffect, transcript_model)
                return ef
            prev = j.stop
