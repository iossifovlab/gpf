# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest
from dae.effect_annotation.annotator import (
    AnnotationRequestFactory,
    EffectAnnotator,
    Variant,
)
from dae.effect_annotation.effect_checkers.stop_loss import (
    StopLossEffectChecker,
)
from dae.genomic_resources.gene_models import Exon, TranscriptModel

from .mocks import TranscriptModelMock


@pytest.fixture(scope="session")
def possitive_transcript_model(
    exons: list[Exon], coding: list[Exon],
) -> TranscriptModel:
    return cast(
        TranscriptModel, TranscriptModelMock("+", 65, 110, exons, coding))


@pytest.fixture(scope="session")
def negative_transcript_model(
    exons: list[Exon], coding: list[Exon],
) -> TranscriptModel:
    return cast(
        TranscriptModel, TranscriptModelMock("-", 65, 110, exons, coding))


@pytest.fixture(scope="session")
def effect_checker() -> StopLossEffectChecker:
    return StopLossEffectChecker()


def test_possitive_deletion_before_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:105", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_deletion_at_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:109", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "noEnd"


def test_possitive_deletion_after_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:111", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_insertion_before_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:107", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_possitive_insertion_at_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:108", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "noEnd"


def test_possitive_insertion_after_end(
    annotator: EffectAnnotator,
    possitive_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:111", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, possitive_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_deletion_before_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:62", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_deletion_at_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:63", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "noEnd"


def test_negative_deletion_after_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:68", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_insertion_before_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:64", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None


def test_negative_insertion_at_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:65", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "noEnd"


def test_negative_insertion_after_end(
    annotator: EffectAnnotator,
    negative_transcript_model: TranscriptModel,
    effect_checker: StopLossEffectChecker,
) -> None:
    variant = Variant(loc="1:68", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, negative_transcript_model,
    )
    effect = effect_checker.get_effect(request)

    assert effect is None
