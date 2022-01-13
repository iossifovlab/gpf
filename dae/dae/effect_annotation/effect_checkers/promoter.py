from ..effect import EffectFactory


class PromoterEffectChecker(object):
    def create_effect(self, transcript_model):
        return EffectFactory.create_effect_with_tm(
            "promoter", transcript_model)

    def create_positive_strand_effect(self, transcript_model, variant):
        ef = self.create_effect(transcript_model)
        ef.dist_from_5utr = (
            transcript_model.exons[0].start - variant.ref_position_last
        )
        return ef

    def create_negative_strand_effect(self, transcript_model, variant):
        ef = self.create_effect(transcript_model)
        ef.dist_from_5utr = variant.position - transcript_model.exons[-1].stop
        return ef

    def get_effect(self, request):
        if request.annotator.promoter_len == 0:
            return None

        if (
            request.variant.position < request.transcript_model.exons[0].start
            and request.transcript_model.strand == "+"
            and request.variant.ref_position_last
            >= request.transcript_model.exons[0].start
            - request.annotator.promoter_len
        ):
            return self.create_positive_strand_effect(
                request.transcript_model, request.variant
            )

        if (
            request.variant.position > request.transcript_model.exons[-1].stop
            and request.transcript_model.strand == "-"
            and request.variant.position
            <= request.transcript_model.exons[-1].stop
            + request.annotator.promoter_len
        ):
            return self.create_negative_strand_effect(
                request.transcript_model, request.variant
            )
        return None
