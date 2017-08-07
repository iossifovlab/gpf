from ..effect import Effect
import logging


class SpliceSiteEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length
        self.logger = logging.getLogger(__name__)

    def create_effect(self, request, start, end, index):
        ef = Effect("splice-site", request.transcript_model)
        ef.prot_length = request.get_protein_length()

        dist_left = request.variant.position - start - 1
        dist_right = end - request.variant.ref_position_last
        ef.dist_from_coding = min(dist_left, dist_right)

        ef.how_many_introns = len(request.transcript_model.exons) - 1
        ef.intron_length = end - start - 1
        if request.transcript_model.strand == "+":
            ef.prot_pos = request.get_protein_position_for_pos(end)
            ef.dist_from_acceptor = dist_right
            ef.dist_from_donor = dist_left
            ef.which_intron = index
        else:
            ef.prot_pos = request.get_protein_position_for_pos(start)
            ef.dist_from_acceptor = dist_left
            ef.dist_from_donor = dist_right
            ef.which_intron = ef.how_many_introns - \
                index + 1

        return ef

    def get_effect(self, request):
        coding_regions = request.transcript_model.exons
        last_position = request.variant.position + \
            len(request.variant.reference)
        prev = None

        for i, j in enumerate(coding_regions):
            if prev is None:
                prev = j.stop
                continue

            self.logger.debug("pos: %d-%d checking intronic region %d-%d %d",
                              request.variant.position, last_position,
                              prev, j.start, j.stop)

            if (request.variant.position < prev + self.splice_site_length + 1
                    and prev + 1 < last_position):
                return self.create_effect(request, prev, j.start, i)

            if (request.variant.position < j.start
                    and j.start - self.splice_site_length < last_position):
                return self.create_effect(request, prev, j.start, i)
            prev = j.stop
