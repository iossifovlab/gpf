from .score_annotator import PositionScoreAnnotator, \
    NPScoreAnnotator
from .allele_score_annotator import AlleleScoreAnnotator
from .effect_annotator import EffectAnnotatorAdapter
from .lift_over_annotator import LiftOverAnnotator


class AnnotatorFactory:
    SCORE_ANNOTATOR_NAMES = {
        "position_score": PositionScoreAnnotator,
        "np_score": NPScoreAnnotator,
        "allele_score": AlleleScoreAnnotator
    }

    @classmethod
    def make_score_annotator(
            cls, annotator_type, gr,
            liftover=None, attributes=None):

        clazz = cls.SCORE_ANNOTATOR_NAMES.get(annotator_type)
        assert clazz is not None
        return clazz(gr, liftover=liftover, attributes=attributes)

    @classmethod
    def make_effect_annotator(
            cls, gene_models, genome, override=None, **kwargs):

        return EffectAnnotatorAdapter(
            gene_models=gene_models,
            genome=genome,
            **kwargs)

    @classmethod
    def make_liftover_annotator(
            cls, annotator, chain, genome, liftover, override=None, **kwargs):
        assert annotator == "liftover_annotator"

        return LiftOverAnnotator(chain, genome, liftover, override=override)

