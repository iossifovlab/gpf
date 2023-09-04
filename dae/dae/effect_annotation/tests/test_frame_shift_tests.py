# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.genomic_resources.gene_models import Exon, TranscriptModel
from dae.effect_annotation.variant import Variant
from dae.effect_annotation.annotator import AnnotationRequestFactory, \
    EffectAnnotator
from dae.effect_annotation.effect_checkers.frame_shift import \
    FrameShiftEffectChecker

from .mocks import TranscriptModelMock


@pytest.fixture(scope="session")
def transcript_model(
    exons: list[Exon], coding: list[Exon]
) -> TranscriptModel:
    return cast(
        TranscriptModel,
        TranscriptModelMock("+", 65, 2000, exons, coding)
    )


@pytest.fixture(scope="session")
def effect_checker() -> FrameShiftEffectChecker:
    return FrameShiftEffectChecker()


def test_deletion_before_start(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:64", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is None


def test_insertion_before_start(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:64", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is None


def test_insertion_at_start_codon(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "frame-shift"


def test_insertion_after_start_codon(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:66", ref="", alt="ABC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "no-frame-shift"


def test_insertion_at_start_codon_2(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="", alt="BC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "frame-shift"


def test_deletion_start_codon(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: FrameShiftEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="ABC", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "no-frame-shift"
