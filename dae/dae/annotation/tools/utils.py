import gzip
import os
from importlib import import_module
from dae.annotation.tools.score_annotator import PositionScoreAnnotator, \
    NPScoreAnnotator
from dae.annotation.tools.allele_score_annotator import AlleleScoreAnnotator
from dae.annotation.tools.effect_annotator import EffectAnnotator
from dae.annotation.tools.lift_over_annotator import LiftOverAnnotator


class AnnotatorFactory:
    SCORE_ANNOTATOR_NAMES = {
        "position_score": PositionScoreAnnotator,
        "np_score": NPScoreAnnotator,
        "allele_score": AlleleScoreAnnotator
    }

    @staticmethod
    def _split_class_name(class_fullname):
        splitted = class_fullname.split(".")
        module_path = splitted[:-1]
        assert len(module_path) >= 1
        if len(module_path) == 1:
            res = ["dae", "annotation", "tools"]
            res.extend(module_path)
            module_path = res

        module_name = ".".join(module_path)
        class_name = splitted[-1]

        return module_name, class_name

    @classmethod
    def name_to_class(cls, class_fullname):
        module_name, class_name = cls._split_class_name(class_fullname)
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz

    @classmethod
    def make_score_annotator(
            cls, annotator_type, gr,
            liftover=None, override=None):
        clazz = cls.SCORE_ANNOTATOR_NAMES.get(annotator_type)
        assert clazz is not None
        return clazz(gr, liftover=liftover, override=override)

    @classmethod
    def make_effect_annotator(
            cls, annotator, gene_models, genome, override=None, **kwargs):
        assert annotator == "effect_annotator"

        return EffectAnnotator(
                gene_models=gene_models,
                genome=genome)

    @classmethod
    def make_liftover_annotator(
            cls, annotator, chain, genome, liftover, override=None, **kwargs):
        assert annotator == "liftover_annotator"

        return LiftOverAnnotator(chain, genome, liftover, override=override)


def handle_chrom_prefix(expect_prefix, data):
    if data is None:
        return data
    if expect_prefix and not data.startswith("chr"):
        return "chr{}".format(data)
    if not expect_prefix and data.startswith("chr"):
        return data[3:]
    return data


def is_gzip(filename):
    try:
        if filename == "-" or not os.path.exists(filename):
            return False
        with gzip.open(filename, "rt") as infile:
            infile.readline()
        return True
    except Exception:
        return False


def regions_intersect(b1: int, e1: int, b2: int, e2: int) -> bool:
    return (
        b2 <= b1 <= e2
        or b2 <= e1 <= e2
        or b1 <= b2 <= e1
        or b1 <= e2 <= e1
    )
