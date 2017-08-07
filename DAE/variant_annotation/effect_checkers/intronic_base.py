from ..effect import Effect


class IntronicBase:
    def create_effect(self, effect_type, request, start, end, index):
        ef = Effect(effect_type, request.transcript_model)
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
