from ..effect import Effect
import logging


class IntronicEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        coding_regions = request.transcript_model.CDS_regions()
        prev = coding_regions[0].stop

        last_position = request.variant.position + \
            len(request.variant.reference)

        for j in coding_regions:
            logger.debug("pos: %d-%d checking intronic region %d-%d",
                         request.variant.position, last_position, prev,
                         j.start)
            if (prev <= request.variant.position
                    and last_position < j.start):
                worstEffect = "intron"
                ef = Effect(worstEffect, request.transcript_model)
                return ef
            prev = j.stop
