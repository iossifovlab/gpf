# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

import pytest

from dae.genomic_resources.gene_models import Exon, TranscriptModel
from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.effect_checkers.protein_change import (
    ProteinChangeEffectChecker,
)
from dae.effect_annotation.annotator import AnnotationRequestFactory, \
    EffectAnnotator

from .mocks import TranscriptModelMock


@pytest.fixture(scope="session")
def transcript_model(exons: list[Exon], coding: list[Exon]) -> TranscriptModel:
    return cast(
        TranscriptModel, TranscriptModelMock("+", 65, 110, exons, coding))


@pytest.fixture(scope="session")
def effect_checker() -> ProteinChangeEffectChecker:
    return ProteinChangeEffectChecker()


def test_missense(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:66", ref="ABC", alt="DEF")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "missense"


def test_nonsense(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="ABC", alt="End")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "nonsense"


def test_synonymous(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="ABC", alt="End")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: "Asn"  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "synonymous"


def test_multiple_codons_missense(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:66", ref="ABCDEF", alt="abcdef")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "missense"


def test_multiple_codons_nonsense(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="ABCDEF", alt="EndPBC")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: codon  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "nonsense"


def test_multiple_codons_synonymous(
    annotator: EffectAnnotator,
    transcript_model: TranscriptModel,
    effect_checker: ProteinChangeEffectChecker
) -> None:
    variant = Variant(loc="1:65", ref="ABCDEF", alt="AAABBB")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    request.cod2aa = lambda codon: "Asn"  # type: ignore
    effect = effect_checker.get_effect(request)
    assert effect is not None
    assert effect.effect == "synonymous"
