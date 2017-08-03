from ..effect import Effect
import logging


class SpliceSiteEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length
        self.logger = logging.getLogger(__name__)

    def get_effect(self, request):
        coding_regions = request.transcript_model.exons
        last_position = request.variant.position + \
            len(request.variant.reference)
        prev = None

        for j in coding_regions:
            if prev is None:
                prev = j.stop
                continue

            self.logger.debug("pos: %d-%d checking intronic region %d-%d %d",
                              request.variant.position, last_position,
                              prev, j.start, j.stop)

            if (request.variant.position < prev + self.splice_site_length + 1
                    and prev + 1 < last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, request.transcript_model)
                ef.prot_pos = request.get_protein_position_for_pos(prev)
                ef.prot_length = request.get_protein_length()
                return ef

            if (request.variant.position < j.start
                    and j.start - self.splice_site_length < last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, request.transcript_model)
                ef.prot_pos = request.get_protein_position_for_pos(j.start)
                ef.prot_length = request.get_protein_length()
                return ef
            prev = j.stop
