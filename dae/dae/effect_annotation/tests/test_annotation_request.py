import pytest

from .mocks import TranscriptModelMock

from dae.effect_annotation.annotator import Variant
from dae.effect_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="session")
def transcript_model(exons, coding):
    return TranscriptModelMock("+", 65, 2000, exons, coding)


def test_exonic_distance(annotator, transcript_model):
    variant = Variant(loc="1:64", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    assert request.get_exonic_distance(60, 61) == 1
    assert request.get_exonic_distance(60, 70) == 10
    assert request.get_exonic_distance(60, 80) == 11
    assert request.get_exonic_distance(70, 80) == 1


def test_exonic_pos_first_exon(annotator, transcript_model):
    variant = Variant(loc="1:64", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    assert request.get_exonic_position() == 5
    assert request.get_exonic_length() == 33


def test_exonic_pos_last_in_first_exon(annotator, transcript_model):
    variant = Variant(loc="1:70", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    assert request.get_exonic_position() == 11
    assert request.get_exonic_length() == 33


def test_exonic_pos_second_exon(annotator, transcript_model):
    variant = Variant(loc="1:80", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    assert request.get_exonic_position() == 12
    assert request.get_exonic_length() == 33


def test_exonic_pos_last_exon(annotator, transcript_model):
    variant = Variant(loc="1:110", ref="A", alt="")
    request = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    assert request.get_exonic_position() == 33
    assert request.get_exonic_length() == 33
