from ..effect import EffectFactory
import logging


class IntronicEffectChecker(object):
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        coding_regions = request.CDS_regions()
        prev = coding_regions[0].stop

        last_position = request.variant.corrected_ref_position_last

        intron_regions_before_coding = 0
        for j in request.transcript_model.exons:
            logger.debug(
                "reg %d-%d cds:%d",
                j.start,
                j.stop,
                request.transcript_model.cds[0],
            )
            if request.transcript_model.cds[0] <= j.stop:
                break
            intron_regions_before_coding += 1

        for i, j in enumerate(coding_regions):
            logger.debug(
                "pos: %d-%d checking intronic region %d-%d",
                request.variant.position,
                last_position,
                prev,
                j.start,
            )
            if prev < request.variant.position and last_position < j.start:
                return EffectFactory.create_intronic_effect(
                    "intron",
                    request,
                    prev,
                    j.start,
                    intron_regions_before_coding + i,
                )
            prev = j.stop
