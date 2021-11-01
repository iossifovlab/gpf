import pytest

from .mocks import TranscriptModelMock

from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.annotation_request import AnnotationRequestFactory
from dae.effect_annotation.effect_checkers.frame_shift import (
    FrameShiftEffectChecker,
)


@pytest.fixture(scope="session")
def transcript_model(exons, coding):
    return TranscriptModelMock("+", 65, 2000, exons, coding)


@pytest.fixture(scope="session")
def effect_checker():
    return FrameShiftEffectChecker()


def test_deletion_before_start(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:64", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is None


def test_insertion_before_start(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:64", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is None


def test_insertion_at_start_codon(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "frame-shift"


def test_insertion_after_start_codon(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:66", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "no-frame-shift"


def test_insertion_at_start_codon_2(
    annotator, transcript_model, effect_checker
):
    variant = Variant(loc="1:65", ref="", alt="BC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "frame-shift"


def test_deletion_start_codon(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:65", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "no-frame-shift"
