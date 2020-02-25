import pytest

from .mocks import TranscriptModelMock

from dae.variant_annotation.annotator import Variant
from dae.variant_annotation.annotation_request import AnnotationRequestFactory
from dae.variant_annotation.effect_checkers.coding import CodingEffectChecker


@pytest.fixture(scope="session")
def transcript_model(exons, coding):
    return TranscriptModelMock("+", 1, 2000, coding, is_coding=False)


@pytest.fixture(scope="session")
def effect_checker():
    return CodingEffectChecker()


def test_insertion_3_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:80", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:79", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:78", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"


def test_deletion_3_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:80", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:79", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:78", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:77", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"


def test_subs_3_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:80", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:79", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:78", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:77", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"


def test_insertion_5_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:70", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:71", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:72", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:73", ref="", alt="A")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"


def test_deletion_5_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:70", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:71", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:72", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:73", ref="0", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"


def test_subs_5_prime_side(annotator, transcript_model, effect_checker):
    variant = Variant(loc="1:70", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding"

    variant = Variant(loc="1:71", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:72", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"

    variant = Variant(loc="1:73", ref="A", alt="G")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    effect = effect_checker.get_effect(request)
    assert effect.effect == "non-coding-intron"
