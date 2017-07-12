from ..effect import Effect


class PromoterEffectChecker:
    def create_effect(self, transcript_model):
        return Effect("promoter", transcript_model)

    def create_positive_strand_effect(self, transcript_model, variant):
        ef = self.create_effect(transcript_model)
        ef.dist_from_5utr = transcript_model.exons[0].start \
            - variant.position_last
        return ef

    def create_negative_strand_effect(self, transcript_model, variant):
        ef = self.create_effect(transcript_model)
        ef.dist_from_5utr = variant.position - transcript_model.exons[-1].stop
        return ef

    def get_effect(self, annotator, variant, transcript_model):
        if annotator.promoter_len == 0:
            return None

        if (variant.position < transcript_model.exons[0].start
            and transcript_model.strand == "+"
            and variant.position_last >=
                transcript_model.exons[0].start - annotator.promoter_len):
            return self.create_positive_strand_effect(
                transcript_model, variant
            )

        if (variant.position > transcript_model.exons[-1].stop
            and transcript_model.strand == "-"
            and variant.position <=
                transcript_model.exons[-1].stop + annotator.promoter_len):
            return self.create_negative_strand_effect(
                transcript_model, variant
            )
        return None
