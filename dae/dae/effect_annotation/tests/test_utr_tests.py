# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.effect_annotation.annotator import (
    AnnotationRequestFactory,
    EffectAnnotator,
    Variant,
)
from dae.effect_annotation.effect_checkers.utr import UTREffectChecker
from dae.genomic_resources.gene_models import Exon, TranscriptModel

from .mocks import TranscriptModelMock


@pytest.fixture(scope="session")
def transcript_model() -> TranscriptModel:
    exons = [
        Exon(60, 70, 0),
        Exon(80, 90, 1),
        Exon(100, 110, 2),
        Exon(150, 170, 2),
    ]
    coding = [Exon(85, 90, 1), Exon(100, 105, 2)]

    return cast(
        TranscriptModel,
        TranscriptModelMock("+", 85, 105, exons, coding),
    )


@pytest.fixture(scope="session")
def effect_checker() -> UTREffectChecker:
    return UTREffectChecker()


def test_deletion_before_start(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: UTREffectChecker,
) -> None:
    variant = Variant(loc="1:65", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "5'UTR"
    assert effect.dist_from_coding == 11


def test_deletion_after_end_same_exon(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: UTREffectChecker,
) -> None:
    variant = Variant(loc="1:108", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 3


def test_deletion_after_end_same_exon_end(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: UTREffectChecker,
) -> None:
    variant = Variant(loc="1:110", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 5


def test_deletion_after_end_last_exon(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: UTREffectChecker,
) -> None:
    variant = Variant(loc="1:151", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model,
    )
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "3'UTR"
    assert effect.dist_from_coding == 7
