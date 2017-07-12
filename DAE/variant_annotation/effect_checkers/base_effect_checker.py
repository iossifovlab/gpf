from ..effect import Effect


class BaseEffectChecker(object):
    def create_effect(self, transcript_model):
        ef = Effect()
        ef.gene = transcript_model.gene
        ef.strand = transcript_model.strand
        ef.transcript_id = transcript_model.trID
        return ef
