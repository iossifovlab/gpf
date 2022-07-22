# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.effect_checkers.start_loss import (
    StartLossEffectChecker,
)
from dae.effect_annotation.annotation_request import AnnotationRequestFactory

from .mocks import TranscriptModelMock


@pytest.fixture(scope="session")
def possitive_transcript_model(exons, coding):
    return TranscriptModelMock("+", 65, 110, exons, coding)


@pytest.fixture(scope="session")
def negative_transcript_model(exons, coding):
    return TranscriptModelMock("-", 65, 110, exons, coding)


@pytest.fixture(scope="session")
def effect_checker():
    return StartLossEffectChecker()


def test_possitive_deletion_before_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:62", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_deletion_at_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:63", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "noStart"


def test_possitive_deletion_after_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:68", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_insertion_before_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:64", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_insertion_at_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:65", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "noStart"


def test_possitive_insertion_after_start(
    annotator, possitive_transcript_model, effect_checker
):
    variant = Variant(loc="1:68", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_deletion_before_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:105", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_deletion_at_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:109", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "noStart"


def test_negative_deletion_after_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:111", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_insertion_before_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:107", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_insertion_at_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:108", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect.effect == "noStart"


def test_negative_insertion_after_start(
    annotator, negative_transcript_model, effect_checker
):
    variant = Variant(loc="1:111", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model
    )
    effect = effect_checker.get_effect(request)

    assert effect is None
