import pytest

from .mocks import ExonMock
from .mocks import TranscriptModelMock

from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.effect_checkers.utr import UTREffectChecker
from dae.effect_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="session")
def transcript_model():
    exons = [
        ExonMock(60, 70, 0),
        ExonMock(80, 90, 1),
        ExonMock(100, 110, 2),
        ExonMock(150, 170, 2),
    ]
    coding = [ExonMock(85, 90, 1), ExonMock(100, 105, 2)]

    return TranscriptModelMock("+", 85, 105, exons, coding)


@pytest.fixture(scope="session")
def effect_checker():
    return UTREffectChecker()


def test_deletion_before_start(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "5'UTR"
    assert effect.dist_from_coding == 11


def test_deletion_after_end_same_exon(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:108", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 3


def test_deletion_after_end_same_exon_end(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:110", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 5


def test_deletion_after_end_last_exon(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:151", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 7
