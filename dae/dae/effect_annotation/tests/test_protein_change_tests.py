import pytest

from .mocks import TranscriptModelMock

from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.effect_checkers.protein_change import (
    ProteinChangeEffectChecker,
)
from dae.effect_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="session")
def transcript_model(exons, coding):
    return TranscriptModelMock("+", 65, 110, exons, coding)


@pytest.fixture(scope="session")
def effect_checker():
    return ProteinChangeEffectChecker()


def test_missense(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:66", ref="ABC", alt="DEF")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon
    effect = effect_checker.get_effect(request)

    assert effect.effect == "missense"


def test_nonsense(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="ABC", alt="End")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon
    effect = effect_checker.get_effect(request)

    assert effect.effect == "nonsense"


def test_synonymous(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="ABC", alt="End")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: "Asn"
    effect = effect_checker.get_effect(request)

    assert effect.effect == "synonymous"


def test_multiple_codons_missense(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:66", ref="ABCDEF", alt="abcdef")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon
    effect = effect_checker.get_effect(request)

    assert effect.effect == "missense"


def test_multiple_codons_nonsense(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="ABCDEF", alt="EndPBC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon
    effect = effect_checker.get_effect(request)

    assert effect.effect == "nonsense"


def test_multiple_codons_synonymous(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:65", ref="ABCDEF", alt="AAABBB")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: "Asn"
    effect = effect_checker.get_effect(request)

    assert effect.effect == "synonymous"
