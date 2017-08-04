from ..effect import Effect
import logging


class IntronicEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        coding_regions = request.CDS_regions()
        prev = coding_regions[0].stop

        last_position = request.variant.position + \
            len(request.variant.reference)

        intron_regions_before_coding = 0
        for j in request.transcript_model.exons:
            logger.debug("reg %d-%d cds:%d", j.start, j.stop,
                         request.transcript_model.cds[0])
            if (request.transcript_model.cds[0] <= j.stop):
                break
            intron_regions_before_coding += 1

        for i, j in enumerate(coding_regions):
            logger.debug("pos: %d-%d checking intronic region %d-%d",
                         request.variant.position, last_position, prev,
                         j.start)
            if (prev <= request.variant.position
                    and last_position < j.start):
                worstEffect = "intron"
                ef = Effect(worstEffect, request.transcript_model)
                dist_left = request.variant.position - prev
                dist_right = j.start - max(
                    request.variant.position,
                    request.variant.ref_position_last - 1
                )
                ef.dist_from_coding = min(dist_left, dist_right)

                ef.how_many_introns = len(request.transcript_model.exons) - 1
                if request.transcript_model.strand == "+":
                    ef.which_intron = intron_regions_before_coding + i
                else:
                    ef.which_intron = ef.how_many_introns - \
                        intron_regions_before_coding - i + 1
                return ef
            prev = j.stop
